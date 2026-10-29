"""YouTube Data API v3: find Indian personal-finance videos about SIPs (English + Hindi/Hinglish),
then pull top-level comments. Commenter names/channel IDs are dropped."""
import json, os, time, urllib.request, urllib.parse

KEY = os.environ["YOUTUBE_API_KEY"]
API = "https://www.googleapis.com/youtube/v3"
QUERIES = ["SIP stop or continue", "should I stop my SIP", "SIP band kare ya nahi", "SIP band kaise kare",
           "first SIP mistakes beginners", "SIP returns negative what to do", "SIP for beginners India",
           "mutual fund SIP first time investor", "SIP pause skip groww", "groww SIP",
           "SIP kaise shuru kare", "SIP loss kya kare", "why people stop SIP", "SIP mandate failed autopay",
           "SIP 1 saal ka result", "my SIP portfolio after 1 year", "SIP me loss ho raha hai",
           "step up SIP explained", "SIP mistakes hindi", "should beginners start SIP 2026"]

def get(path, **p):
    p["key"] = KEY
    url = f"{API}/{path}?{urllib.parse.urlencode(p)}"
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(url, timeout=30))
        except Exception as e:
            err = str(e); time.sleep(2)
    print("fail", path, err); return {}

videos = {}
for q in QUERIES:
    d = get("search", part="snippet", q=q, type="video", maxResults=15, regionCode="IN",
            relevanceLanguage="hi" if any(w in q for w in ["kare", "kaise", "nahi", "saal", "kya", "hindi", "me "]) else "en",
            publishedAfter="2023-01-01T00:00:00Z", order="relevance")
    for it in d.get("items", []):
        vid = it["id"]["videoId"]
        videos[vid] = {"title": it["snippet"]["title"], "channel": it["snippet"]["channelTitle"], "query": q}
print("videos", len(videos), flush=True)

# keep videos with enough comments
ids = list(videos)
for i in range(0, len(ids), 50):
    d = get("videos", part="statistics", id=",".join(ids[i:i+50]))
    for it in d.get("items", []):
        videos[it["id"]]["comments"] = int(it["statistics"].get("commentCount", 0))
        videos[it["id"]]["views"] = int(it["statistics"].get("viewCount", 0))

rows = []
for vid, v in sorted(videos.items(), key=lambda kv: -kv[1].get("comments", 0)):
    if v.get("comments", 0) < 20: continue
    token, n = None, 0
    while n < 600:
        p = dict(part="snippet", videoId=vid, maxResults=100, order="relevance", textFormat="plainText")
        if token: p["pageToken"] = token
        d = get("commentThreads", **p)
        for it in d.get("items", []):
            s = it["snippet"]["topLevelComment"]["snippet"]
            rows.append({"source": "youtube", "app": "youtube", "id": "yt_" + it["id"], "rating": None,
                         "date": s["publishedAt"][:10], "text": s["textDisplay"][:2000], "thumbs": s.get("likeCount", 0),
                         "thread": v["title"], "channel": v["channel"],
                         "url": f"https://www.youtube.com/watch?v={vid}&lc={it['id']}"})
            n += 1
        token = d.get("nextPageToken")
        if not token: break
print("comments", len(rows), "from videos", len({r['url'].split('&')[0] for r in rows}))
json.dump(rows, open("/home/claude/engine/raw/youtube.json", "w"), ensure_ascii=False)
json.dump(videos, open("/home/claude/engine/out/youtube_videos.json", "w"), ensure_ascii=False, indent=1)
