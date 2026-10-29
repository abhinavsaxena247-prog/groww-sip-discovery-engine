"""Collect Play Store and App Store reviews (India) for Groww and comparison apps.
Stores everything raw; relevance filtering happens in the pipeline, not here.
No reviewer names or user IDs are kept."""
import json, time, sys, urllib.request
from google_play_scraper import reviews, Sort

OUT = "/home/claude/engine/raw"
PLAY = {  # package: (label, newest_count)
    "com.nextbillion.groww": ("Groww", 20000),
    "com.zerodha.coin": ("Zerodha Coin", 4000),
    "com.zerodha.kite3": ("Zerodha Kite", 4000),
    "in.upstox.app": ("Upstox", 4000),
    "com.msf.angelmobile": ("Angel One", 4000),
    "com.mosl.mobile": ("MO Riise", 3000),
    "com.paytmmoney": ("Paytm Money", 4000),
    "in.indwealth": ("INDmoney", 4000),
}
APPSTORE = {
    1404871703: "Groww", 1392892554: "Zerodha Coin", 1449453802: "Zerodha Kite",
    1584953620: "Upstox", 1060530981: "Angel One", 1344431352: "Paytm Money",
    1450178837: "INDmoney", 1212752482: "ET Money", 1329701793: "Kuvera",
}

def play():
    rows = []
    for pkg, (label, n) in PLAY.items():
        for sort, sname, cnt in [(Sort.NEWEST, "newest", n), (Sort.MOST_RELEVANT, "relevant", 2000)]:
            got, token = 0, None
            while got < cnt:
                try:
                    batch, token = reviews(pkg, lang="en", country="in", sort=sort,
                                           count=min(200, cnt - got), continuation_token=token)
                except Exception as e:
                    print(label, sname, "error", e, file=sys.stderr); time.sleep(3); break
                for r in batch:
                    rows.append({"source": "play_store", "app": label, "id": r["reviewId"],
                                 "rating": r["score"], "date": r["at"].strftime("%Y-%m-%d"),
                                 "text": r["content"] or "", "thumbs": r["thumbsUpCount"],
                                 "app_version": r.get("appVersion"), "sort": sname})
                got += len(batch)
                if not batch or token is None or token.token is None: break
            print(f"play {label} {sname}: {got}", flush=True)
    json.dump(rows, open(f"{OUT}/play.json", "w"), ensure_ascii=False)

def appstore():
    rows = []
    for aid, label in APPSTORE.items():
        n = 0
        for sortby in ["mostrecent", "mosthelpful"]:
            for p in range(1, 11):
                url = f"https://itunes.apple.com/in/rss/customerreviews/page={p}/id={aid}/sortby={sortby}/json"
                try:
                    d = json.load(urllib.request.urlopen(url, timeout=20))
                except Exception:
                    break
                entries = d.get("feed", {}).get("entry", [])
                if isinstance(entries, dict): entries = [entries]
                entries = [e for e in entries if "im:rating" in e]
                if not entries: break
                for e in entries:
                    rows.append({"source": "app_store", "app": label, "id": e["id"]["label"],
                                 "rating": int(e["im:rating"]["label"]), "date": e["updated"]["label"][:10],
                                 "text": (e["title"]["label"] + ". " + e["content"]["label"]),
                                 "thumbs": int(e.get("im:voteSum", {}).get("label", 0) or 0),
                                 "app_version": e.get("im:version", {}).get("label"), "sort": sortby})
                    n += 1
        print(f"appstore {label}: {n}", flush=True)
    json.dump(rows, open(f"{OUT}/appstore.json", "w"), ensure_ascii=False)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "appstore"): appstore()
    if which in ("all", "play"): play()
