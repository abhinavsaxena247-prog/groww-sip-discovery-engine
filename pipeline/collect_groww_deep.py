"""Deeper Groww Play Store crawl (newest-first, up to 150k) to raise the Groww-specific SIP sample."""
import json, sys
from google_play_scraper import reviews, Sort
rows, token, got = [], None, 0
while got < 150000:
    try:
        batch, token = reviews("com.nextbillion.groww", lang="en", country="in", sort=Sort.NEWEST, count=200, continuation_token=token)
    except Exception as e:
        print("err", e, flush=True); break
    for r in batch:
        rows.append({"source": "play_store", "app": "Groww", "id": r["reviewId"], "rating": r["score"],
                     "date": r["at"].strftime("%Y-%m-%d"), "text": r["content"] or "", "thumbs": r["thumbsUpCount"],
                     "app_version": r.get("appVersion"), "sort": "newest_deep"})
    got += len(batch)
    if got % 10000 < 200: print(got, rows[-1]["date"], flush=True)
    if not batch or token is None or token.token is None: break
json.dump(rows, open("/home/claude/engine/raw/play_groww_deep.json", "w"), ensure_ascii=False)
print("done", got, rows[-1]["date"] if rows else None)
