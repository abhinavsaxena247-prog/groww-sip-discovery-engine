"""Grade a question bank (route + topic) in basic mode. Usage: python -m evals.run_bank bank_v3 [ai]"""
import importlib, json, sys
from engine import pipeline as P

name = sys.argv[1]; use_ai = len(sys.argv) > 2 and sys.argv[2] == "ai"
cases = importlib.import_module("evals." + name).CASES
OK = {"basics": ("basics",), "research": ("research",), "answer": ("answer", "greeting"),
      "decline_advice": ("decline_advice",), "decline_offtopic": ("decline_offtopic",)}
rows, fails = [], []
for exp, topic, q in cases:
    o = P.answer(q, use_ai=use_ai)
    ok = o["route"] in OK[exp] and (topic is None or o.get("topic") == topic)
    rows.append({"q": q, "expect": exp, "topic": topic, "route": o["route"], "got_topic": o.get("topic"), "pass": ok, "text": o["text"][:300]})
    if not ok:
        fails.append(f"  {exp}/{topic} -> {o['route']}/{o.get('topic')} | {q}")
n = sum(r["pass"] for r in rows)
print(f"{name}: {n}/{len(rows)} passed")
by = {}
for r in rows:
    d = by.setdefault(r["expect"], [0, 0]); d[0] += r["pass"]; d[1] += 1
print({k: f"{a}/{b}" for k, (a, b) in by.items()})
print("\n".join(fails))
json.dump({"name": name, "mode": "ai" if use_ai else "basic", "pass": n, "total": len(rows), "by": by, "rows": rows},
          open(f"data/bank_results_{name}{'_ai' if use_ai else ''}.json", "w"), indent=1, ensure_ascii=False)
