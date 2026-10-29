"""Zerodha Varsity - reader comments on Personal Finance (mutual fund / SIP) chapters.
Commenter names dropped. Keeps reader questions/comments, not Varsity staff replies."""
import re, json, time, html, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
def get(u):
    try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode("utf-8", "ignore")
    except Exception: return ""

mod = get("https://zerodha.com/varsity/module/personalfinance/")
chapters = sorted(set(re.findall(r'href="(https://zerodha.com/varsity/chapter/[^"]+)"', mod)))
rows = []
for ch in chapters:
    h = get(ch)
    # each comment: <div class="comment-body"> ... author ... <p>text</p>
    for m in re.finditer(r'<li class="([^"]*)" id="comment-(\d+)">\s*<div id="div-comment-\d+" class="comment-body">(.*?)<div class="reply">', h, re.S):
        cls, cid, block = m.groups()
        if "bypostauthor" in cls:  # Varsity staff reply
            continue
        date = re.search(r'#comment-\d+">(\w+ \d{1,2}, \d{4})', block)
        paras = re.findall(r'<p>(.*?)</p>', block, re.S)
        if not paras: continue
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", " ".join(paras)))).replace("\\","").strip()
        if len(txt) < 25: continue
        rows.append({"source": "zerodha_varsity", "app": "forum", "id": f"zv_{cid}", "rating": None,
                     "date": date.group(1) if date else "", "text": txt[:2000], "thumbs": 0,
                     "thread": ch.rstrip("/").split("/")[-1], "url": f"{ch}#comment-{cid}"})
    time.sleep(0.6)
json.dump(rows, open("/home/claude/engine/raw/varsity.json", "w"), ensure_ascii=False)
print("chapters", len(chapters), "comments", len(rows))
