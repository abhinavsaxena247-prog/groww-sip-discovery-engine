"""Play Store caps each sorted stream (~20k). Pull Groww newest per star rating (1-5) to reach older reviews."""
import json
from google_play_scraper import reviews, Sort
rows=[]
for star in [1,2,3,4,5]:
    token, got = None, 0
    while got < 20000:
        try: batch, token = reviews("com.nextbillion.groww", lang="en", country="in", sort=Sort.NEWEST, count=200, filter_score_with=star, continuation_token=token)
        except Exception as e: print("err",e,flush=True); break
        for r in batch:
            rows.append({"source":"play_store","app":"Groww","id":r["reviewId"],"rating":r["score"],"date":r["at"].strftime("%Y-%m-%d"),
                         "text":r["content"] or "","thumbs":r["thumbsUpCount"],"app_version":r.get("appVersion"),"sort":f"newest_star{star}"})
        got += len(batch)
        if not batch or token is None or token.token is None: break
    print("star",star,got,rows[-1]["date"],flush=True)
json.dump(rows,open("/home/claude/engine/raw/play_groww_bystar.json","w"),ensure_ascii=False)
