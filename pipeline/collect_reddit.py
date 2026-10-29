"""Reddit via the Arctic Shift (title/full-text search times out, so: list every post 2024-01..now in 3 subs, filter locally) public archive (reddit.com itself blocks automated reads: HTTP 403).
Full-text 'query' searches time out on the archive, so we use title-keyword searches in yearly windows,
then pull comments for posts that have discussion. Usernames are dropped."""
import json, time, urllib.request, urllib.parse

API = "https://arctic-shift.photon-reddit.com/api"
SUBS = ["IndiaInvestments", "mutualfunds", "personalfinanceindia", "FIREIndia", "IndianStockMarket"]
TITLE_KW = ["SIP", "mutual fund", "autopay", "mandate", "Groww", "first investment", "beginner"]
YEARS = [("2022-01-01", "2023-01-01"), ("2023-01-01", "2024-01-01"), ("2024-01-01", "2025-01-01"),
         ("2025-01-01", "2026-01-01"), ("2026-01-01", "2026-11-01")]

def get(path, **p):
    url = f"{API}/{path}?{urllib.parse.urlencode(p)}"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (student research; NextLeap project)"})
            d = json.load(urllib.request.urlopen(req, timeout=60))
            if d.get("error"):
                time.sleep(5 * (attempt + 1)); continue
            return d.get("data") or []
        except Exception:
            time.sleep(5 * (attempt + 1))
    return []

import re
REL = re.compile(r"(\bsips?\b|mutual ?funds?|\bmfs?\b|autopay|auto-pay|mandate|e-?nach|groww|instal+ment|step.?up|"
                 r"first (time )?invest|beginner|new to invest|just started|index fund|elss)", re.I)
SUBS = ["mutualfunds", "IndiaInvestments", "personalfinanceindia"]
START, END = "2024-01-01", "2026-11-01"
posts, seen_total = {}, 0
for sub in SUBS:
    after = START
    while True:
        rows = get("posts/search", subreddit=sub, after=after, before=END, limit=100, sort="asc",
                   fields="id,title,selftext,created_utc,num_comments,score")
        if not rows: break
        seen_total += len(rows)
        for r in rows:
            if REL.search((r.get("title") or "") + " " + (r.get("selftext") or "")):
                posts[r["id"]] = {**r, "sub": sub}
        after = str(int(rows[-1]["created_utc"]) + 1)
        if len(rows) < 100: break
        time.sleep(1.0)
    print(sub, "scanned", seen_total, "relevant posts so far", len(posts), flush=True)

out = []
for p in posts.values():
    body = (p.get("title") or "") + ". " + (p.get("selftext") or "")
    if p.get("selftext") in ("[removed]", "[deleted]"): body = p.get("title") or ""
    out.append({"source": "reddit", "app": "r/" + p["sub"], "id": "rd_" + p["id"], "rating": None,
                "date": time.strftime("%Y-%m-%d", time.gmtime(int(p["created_utc"]))), "text": body[:3000],
                "thumbs": p.get("score", 0), "thread": p.get("title"), "is_op": True,
                "url": f"https://www.reddit.com/comments/{p['id']}"})

# comments for posts with discussion (most-discussed first, capped)
disc = sorted([p for p in posts.values() if (p.get("num_comments") or 0) >= 3], key=lambda p: -(p.get("num_comments") or 0))[:1200]
for i, p in enumerate(disc):
    rows = get("comments/search", link_id=p["id"], limit=100, fields="id,body,created_utc,score")
    for c in rows:
        if c.get("body") in (None, "[removed]", "[deleted]") or len(c["body"]) < 25: continue
        out.append({"source": "reddit", "app": "r/" + p["sub"], "id": "rdc_" + c["id"], "rating": None,
                    "date": time.strftime("%Y-%m-%d", time.gmtime(int(c["created_utc"]))), "text": c["body"][:2000],
                    "thumbs": c.get("score", 0), "thread": p.get("title"), "is_op": False,
                    "url": f"https://www.reddit.com/comments/{p['id']}/_/{c['id']}"})
    if i % 100 == 0: print("comments for", i, "posts; rows", len(out), flush=True)
    time.sleep(0.8)
json.dump(out, open("/home/claude/engine/raw/reddit.json", "w"), ensure_ascii=False)
print("DONE posts", len(posts), "rows", len(out))
