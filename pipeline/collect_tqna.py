"""TradingQnA (Discourse) - search SIP-related topics, then pull posts from each topic.
Usernames are dropped; only post text, date and topic title are kept."""
import json, time, re, urllib.request, urllib.parse, html

BASE = "https://tradingqna.com"
UA = {"User-Agent": "Mozilla/5.0 (research; student project)"}
QUERIES = ["SIP", "stop SIP", "pause SIP", "skip SIP", "SIP failed", "SIP mandate", "SIP autopay",
           "first SIP", "SIP returns negative", "SIP continue", "cancel SIP", "SIP beginner",
           "mutual fund beginner", "SIP coin", "SIP step up", "SIP date", "SIP loss", "redeem SIP",
           "SIP emergency", "SIP salary"]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    for _ in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=25))
        except Exception as e:
            if "429" in str(e): time.sleep(10)
            else: time.sleep(2)
    return None

def clean(s):
    s = re.sub(r"<blockquote.*?</blockquote>", " ", s or "", flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

topics = {}
for q in QUERIES:
    for page in (1, 2, 3):
        d = get(f"{BASE}/search.json?q={urllib.parse.quote(q)}&page={page}")
        if not d or not d.get("topics"): break
        for t in d["topics"]:
            topics[t["id"]] = t.get("title", "")
        time.sleep(0.8)
print("topics found", len(topics), flush=True)

rows = []
for i, (tid, title) in enumerate(topics.items()):
    d = get(f"{BASE}/t/{tid}.json")
    if not d: continue
    for p in d.get("post_stream", {}).get("posts", [])[:40]:
        txt = clean(p.get("cooked"))
        if len(txt) < 25: continue
        rows.append({"source": "tradingqna", "app": "forum", "id": f"tq_{p['id']}",
                     "rating": None, "date": p.get("created_at", "")[:10], "text": txt[:3000],
                     "thumbs": p.get("reaction_users_count", 0) or 0, "thread": title,
                     "is_op": p.get("post_number") == 1, "url": f"{BASE}/t/{tid}/{p.get('post_number')}"})
    time.sleep(0.8)
    if i % 50 == 0: print("topic", i, "rows", len(rows), flush=True)
json.dump(rows, open("/home/claude/engine/raw/tradingqna.json", "w"), ensure_ascii=False)
print("tradingqna rows", len(rows))
