"""Stage 2: AI tagging with Gemini (free tier), 20 items per request, resumable.
Output: out/tags.jsonl (one JSON per item, keyed by id). Run log: out/tag_log.txt.
Usage: python3 stage2_tag.py [model] [limit]"""
import json, os, sys, time, re, urllib.request, random
sys.path.insert(0, os.path.dirname(__file__))
from codebook import CODEBOOK, SYSTEM, PROMPT_VERSION, RESPONSE_SCHEMA

MODELS = (sys.argv[1] if len(sys.argv) > 1 else "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-flash-lite-latest").split(",")
MODEL = MODELS[0]
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9
KEY = os.environ["GEMINI_API_KEY"]
BATCH = int(os.environ.get('BATCH', 10))
OUT = os.environ.get("OUT", "/home/claude/engine/out/tags.jsonl")
LOG = open(os.environ.get("LOG", "/home/claude/engine/out/tag_log.txt"), "a")

items = json.load(open("/home/claude/engine/out/stage1.json"))
import glob as _g
done = set()
for _f in set(_g.glob("/home/claude/engine/out/tags_s*.jsonl")) | {OUT}:  # all shard files, so re-sharding never re-tags
    if not os.path.exists(_f): continue
    for line in open(_f):
        try: done.add(json.loads(line)["id"])
        except Exception: pass
SHARDS, SHARD = int(os.environ.get("SHARDS", 1)), int(os.environ.get("SHARD", 0))
items = [it for k, it in enumerate(items) if k % SHARDS == SHARD]
todo = [i for i in items if i["id"] not in done][:LIMIT]
print(f"model={MODEL} prompt={PROMPT_VERSION} todo={len(todo)} done={len(done)}", file=LOG, flush=True)

INSTR = SYSTEM + """
You will receive a JSON array of items, each with an "id". Return a JSON array with one object per item,
in the same order, each containing "id" plus every codebook field:
relevant, first_time_signal, lifecycle_stage, event, dropoff_type (ONE label), drivers, what_they_check,
outside_app_behaviour, income, age_hint, influencer, expectation_gap, unmet_need, emergent_theme,
severity (1, 2 or 3), evidence_span.
If relevant is false, still return the object with the other fields set to defaults ('unclear', [], '', 1)."""

def call(batch):
    payload = [{"id": b["id"], "source": b["source"], "app": b.get("app"), "rating": b.get("rating"),
                "text": b["text"][:1800]} for b in batch]
    body = {"systemInstruction": {"parts": [{"text": INSTR}]},
            "contents": [{"role": "user", "parts": [{"text": "CODEBOOK:\n" + json.dumps(CODEBOOK, ensure_ascii=False) +
                                                       "\n\nITEMS:\n" + json.dumps(payload, ensure_ascii=False)}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": RESPONSE_SCHEMA}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    txt = r["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(txt), r.get("usageMetadata", {})

out = open(OUT, "a")
ok = fail = 0
t0 = time.time()
for i in range(0, len(todo), BATCH):
    batch = todo[i:i + BATCH]
    for attempt in range(6):
        try:
            res, usage = call(batch)
            ids = {b["id"] for b in batch}
            n = 0
            for r in res:
                if isinstance(r, dict) and r.get("id") in ids:
                    for k in ("event", "drivers", "what_they_check", "outside_app_behaviour"):
                        r[k] = [x for x in r.get(k, []) if x not in ("none", "nothing_mentioned", "none_mentioned")]
                    r["_model"] = MODEL; r["_prompt"] = PROMPT_VERSION
                    out.write(json.dumps(r, ensure_ascii=False) + "\n"); n += 1
            out.flush(); ok += n; fail += len(batch) - n
            break
        except urllib.error.HTTPError as e:
            full = e.read().decode()
            if e.code == 429 and "PerDay" in full:
                print(f"DAILY QUOTA HIT on {MODEL}", file=LOG, flush=True)
                MODELS.pop(0)
                if not MODELS: print("ALL MODELS EXHAUSTED", file=LOG, flush=True); sys.exit(2)
                MODEL = MODELS[0]; print(f"switching to {MODEL}", file=LOG, flush=True); continue
            wait = 20 * (attempt + 1) if e.code == 429 else 8
            print(f"HTTP {e.code} batch {i} -> wait {wait}s", file=LOG, flush=True)
            time.sleep(wait)
        except Exception as e:
            print(f"ERR batch {i}: {e}", file=LOG, flush=True); time.sleep(5)
    else:
        fail += len(batch)
    if (i // BATCH) % 10 == 0:
        print(f"{i+len(batch)}/{len(todo)} ok={ok} fail={fail} {time.time()-t0:.0f}s", file=LOG, flush=True)
print(f"FINISHED ok={ok} fail={fail} {time.time()-t0:.0f}s", file=LOG, flush=True)
