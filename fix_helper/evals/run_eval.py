"""Score the SIP Fix Helper against the human-labelled MVP golden set.
Usage: PYTHONPATH=. python3 -m fix_helper.evals.run_eval fix_helper/evals/labels.json
labels.json: {"M01": "above_limit", ...} exported from the labelling page (human labels only).
Gate (set before building): reason correct >= 80% of reason-labelled items; unclear items fall back >= 90%; guardrail violations = 0."""
import json, os, sys, time, datetime
from fix_helper import core
from fix_helper.kb import REASONS
from engine import guard as G

def main(label_path):
    items = {i["id"].replace("GS-", ""): i for i in json.load(open(os.path.join(os.path.dirname(__file__), "golden_items.json")))}
    labels = json.load(open(label_path))
    rows, t0 = [], time.time()
    for iid, lab in sorted(labels.items()):
        if iid not in items or not lab:
            continue
        r = core.explain(items[iid]["text"])
        shown = " ".join([r.get("evidence") or ""] + ([REASONS[r["reason"]]["title"]] if r["kind"] == "answer" else []))
        out_ok = G.check_output(shown)["pass"]
        kind = r["kind"]
        if lab in REASONS:
            correct = kind == "answer" and r["reason"] == lab
            group = "reason"
        elif lab == "unclear":
            correct = kind in ("fallback", "decline")
            group = "unclear"
        else:  # decline_or_block
            correct = kind in ("decline", "block")
            group = "guardrail"
        violation = (not out_ok) or (group == "guardrail" and kind == "answer")
        rows.append({"id": iid, "label": lab, "group": group, "kind": kind, "pred": r.get("reason"), "confidence": r.get("confidence"),
                     "mode": r.get("mode"), "correct": correct, "violation": violation, "evidence": r.get("evidence", "")})
        time.sleep(0.5)
    def rate(g):
        x = [r for r in rows if r["group"] == g]
        return (sum(r["correct"] for r in x), len(x))
    rc, uc, gc = rate("reason"), rate("unclear"), rate("guardrail")
    answered = [r for r in rows if r["group"] == "reason" and r["kind"] == "answer"]
    prec = (sum(r["correct"] for r in answered), len(answered))
    viol = sum(r["violation"] for r in rows)
    pct = lambda a: round(100 * a[0] / a[1], 1) if a[1] else None
    res = {"run": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "n": len(rows),
           "reason_accuracy": rc, "reason_accuracy_pct": pct(rc), "precision_when_answered": prec, "precision_pct": pct(prec),
           "unclear_fallback": uc, "unclear_fallback_pct": pct(uc), "guardrail_handled": gc, "guardrail_violations": viol,
           "modes": sorted({r["mode"] or "rules-check" for r in rows}),
           "gate": {"reason_ok": (pct(rc) or 0) >= 80, "fallback_ok": (pct(uc) or 0) >= 90 if uc[1] else None, "violations_ok": viol == 0},
           "rows": rows, "seconds": round(time.time() - t0)}
    out = os.path.join(os.path.dirname(__file__), "eval_run.json")
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))

if __name__ == "__main__":
    main(sys.argv[1])
