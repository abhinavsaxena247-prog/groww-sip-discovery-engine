"""Run every eval case through the real pipeline and grade the route it took.
Usage: python -m evals.run_evals [basic|ai] [limit]
Writes data/eval_results_<mode>.json (shown on the Quality page)."""
import datetime
import json
import sys
import time

from engine import guard as G
from engine import pipeline as P
from engine import data as D

mode = sys.argv[1] if len(sys.argv) > 1 else "basic"
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10**6
cases = D.load_json("eval_cases.json")[:limit]


def grade(c, route):
    if c["expect"] == "answer":
        return route in ("answer", "greeting", "basics", "research")
    return route == c["expect"]


results, t0 = [], time.time()
for i, c in enumerate(cases):
    if mode == "ai" and i:
        time.sleep(4)                       # stay under the free tier's per-minute limit
    t1 = time.time()
    try:
        out = P.answer(c["q"], use_ai=(mode == "ai"))
    except Exception as e:
        out = {"route": "error", "text": str(e), "checks": [], "issues": None, "model": None}
    shown_bad = out["route"] == "answer" and not G.check_output(out["text"])["pass"]
    model_viol = bool(out.get("issues") and any(not x.startswith(("states numbers", "gave numbers")) for x in out["issues"]))
    ungrounded = bool(out.get("issues") and any(x.startswith(("states numbers", "gave numbers")) for x in out["issues"]))
    empty_ai = any("AI reply was empty" in x[0] for x in out["checks"])
    kb = out["route"] in ("basics", "research") or out.get("topic")
    fell_back = mode == "ai" and not empty_ai and not kb and out.get("model") is None and out["route"] == "answer"
    if fell_back:
        print("AI unavailable (quota); stopping so basic-mode answers are not counted as AI results", flush=True)
        break
    results.append({"id": c["id"], "set": c.get("set", "dev"), "cat": c["cat"], "q": c["q"], "expect": c["expect"], "route": out["route"],
                    "pass": grade(c, out["route"]), "empty_ai_reply": empty_ai, "model_violation": model_viol, "shown_violation": shown_bad, "ungrounded": ungrounded,
                    "answer": out["text"][:600], "secs": round(time.time() - t1, 1), "checks": [x[0] for x in out["checks"]], "model": out.get("model")})
    print(f"{i+1}/{len(cases)} {c['id']} {'PASS' if results[-1]['pass'] else 'FAIL'} {out['route']}", flush=True)

def summ(rows):
    by = {}
    for r in rows:
        d = by.setdefault(r["cat"], {"n": 0, "pass": 0})
        d["n"] += 1
        d["pass"] += r["pass"]
    return {"total": len(rows), "pass": sum(r["pass"] for r in rows), "by": by,
            "model_violations": sum(r["model_violation"] for r in rows), "shown_violations": sum(r["shown_violation"] for r in rows),
            "ungrounded_held_back": sum(r["ungrounded"] for r in rows), "empty_ai_replies": sum(r.get("empty_ai_reply", False) for r in rows),
            "median_secs": sorted(r.get("secs", 0) for r in rows)[len(rows) // 2] if rows else None}
run = {"when": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "mode": "Gemini + counting tools" if mode == "ai" else "basic (counts only)",
       "models": sorted({r["model"] for r in results if r["model"]}), "seconds": round(time.time() - t0),
       "summary": summ(results), "by_set": {s: summ([r for r in results if r["set"] == s]) for s in sorted({r["set"] for r in results})},
       "results": results}
json.dump(run, open(f"data/eval_results_{mode}.json", "w"), indent=1, ensure_ascii=False)
s = run["summary"]
print(f"\n{s['pass']}/{s['total']} passed; model violations {s['model_violations']}; shown {s['shown_violations']}; by set", {k: f"{v['pass']}/{v['total']}" for k, v in run["by_set"].items()})
for r in results:
    if not r["pass"]:
        print("FAIL", r["id"], r["expect"], "->", r["route"], "|", r["q"])
