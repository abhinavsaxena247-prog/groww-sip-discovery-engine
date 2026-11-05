"""Run: PYTHONPATH=. python3 -m fix_helper.tests.run_qa [basic]"""
import json, sys, time
from fix_helper import core
from fix_helper.tests.qa_cases import CASES

def outcome(text):
    r = core.read_facts(text)
    if r["kind"] in ("block", "decline"):
        return r, r["kind"]
    if r["kind"] == "help":
        return r, ("help", r["topic"])
    f = dict(r["facts"])  # investor confirms the pre-fills unchanged
    return r, core.decide(f)

def check(exp, r, got):
    if isinstance(exp, str) or exp[0] == "help":
        return got == exp
    if exp[0] == "reason":
        return got == ("reason", exp[1])
    if exp[0] == "facts":
        return r["kind"] == "facts" and (len(exp) == 1 or r["facts"].get(exp[1]) == exp[2])
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "basic":
        core.llm.json_call = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("forced basic"))
    rows, ok = [], 0
    for cid, cat, text, exp in CASES:
        r, got = outcome(text)
        p = check(exp, r, got); ok += p
        rows.append({"id": cid, "cat": cat, "input": text[:80], "expected": exp, "got": got if not isinstance(got, tuple) else list(got), "pass": p})
        if not p:
            print("FAIL", cid, cat, repr(text[:60]), "expected", exp, "got", got, r.get("facts"))
        time.sleep(0.25)
    print(f"{ok}/{len(CASES)} passed")
    json.dump({"passed": ok, "total": len(CASES), "rows": rows}, open(f"fix_helper/tests/qa_results_{sys.argv[1] if len(sys.argv)>1 else 'ai'}.json", "w"), ensure_ascii=False, indent=1, default=str)
