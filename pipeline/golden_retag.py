"""Re-tag the 27 golden-set comments with prompt v1.2 and v1.3 in identical batches (same model, temperature 0,
same schema, same instructions apart from the relevance rule), so the comparison isolates the prompt change.
Output: /home/claude/engine/out/golden_retag.json"""
import json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(__file__))
import codebook as V12
import codebook_v13 as V13

KEY = [l.split("=", 1)[1].strip() for l in open("/home/claude/engine/.env") if l.startswith("GEMINI_API_KEY=")][0]
MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]
G = json.load(open("/home/claude/engine/out/golden_selection.json"))
TAIL = """
You will receive a JSON array of items, each with an "id". Return a JSON array with one object per item,
in the same order, each containing "id" plus every codebook field:
relevant, first_time_signal, lifecycle_stage, event, dropoff_type (ONE label), drivers, what_they_check,
outside_app_behaviour, income, age_hint, influencer, expectation_gap, unmet_need, emergent_theme,
severity (1, 2 or 3), evidence_span.
If relevant is false, still return the object with the other fields set to defaults ('unclear', [], '', 1)."""

def call(model, system, codebook, batch):
    payload = [{"id": b["id"], "source": b["source"], "app": b.get("app"), "rating": b.get("rating"), "text": b["text"][:1800]} for b in batch]
    body = {"systemInstruction": {"parts": [{"text": system + TAIL}]},
            "contents": [{"role": "user", "parts": [{"text": "CODEBOOK:\n" + json.dumps(codebook, ensure_ascii=False) + "\n\nITEMS:\n" + json.dumps(payload, ensure_ascii=False)}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": V12.RESPONSE_SCHEMA}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={KEY}",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    return json.loads(r["candidates"][0]["content"]["parts"][0]["text"])

def run(system, codebook, version):
    out = {}
    for i in range(0, len(G), 10):
        batch = G[i:i + 10]
        for attempt in range(8):
            model = MODELS[0]
            try:
                res = call(model, system, codebook, batch)
                for r in res:
                    if isinstance(r, dict) and r.get("id") in {b["id"] for b in batch}:
                        for k in ("event", "drivers", "what_they_check", "outside_app_behaviour"):
                            r[k] = [x for x in r.get(k, []) if x not in ("none", "nothing_mentioned", "none_mentioned")]
                        r["_model"], r["_prompt"] = model, version
                        out[r["id"]] = r
                missing = [b["id"] for b in batch if b["id"] not in out]
                if missing:
                    raise ValueError(f"missing ids {missing}")
                break
            except urllib.error.HTTPError as e:
                txt = e.read().decode()
                if e.code == 429 and "PerDay" in txt and len(MODELS) > 1:
                    print("daily quota on", MODELS.pop(0)); continue
                print("HTTP", e.code, "wait"); time.sleep(20 * (attempt + 1))
            except Exception as e:
                print("ERR", e); time.sleep(8)
        time.sleep(4)
    return out

res = {"v1.2": run(V12.SYSTEM, V12.CODEBOOK, V12.PROMPT_VERSION), "v1.3": run(V13.SYSTEM, V13.CODEBOOK, V13.PROMPT_VERSION),
       "date": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}
json.dump(res, open("/home/claude/engine/out/golden_retag.json", "w"), ensure_ascii=False, indent=1)
print({k: len(v) for k, v in res.items() if k != "date"})
