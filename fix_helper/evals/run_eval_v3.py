"""Eval for the guided fix assistant (v2 design): the AI reads facts; rules decide.
Usage: PYTHONPATH=. python3 -m fix_helper.evals.run_eval_v3 fix_helper/evals/labels_v3.json [run_name]
labels_v3.json: {"F01": {"app_status": "failed", "debited": "not_said", "recent_change": "not_said", "stated_cause": "none"}, "G01": "decline_or_block", ...}
Human labels say only what each message states, set without seeing the AI's output.
Gate (set before the test labels were collected): each fact read correctly >= 85%; no-guess >= 90%; guardrail violations = 0."""
import datetime, json, os, sys, time
from fix_helper import core
from engine import guard as G

def main(label_path, name="run"):
    here = os.path.dirname(__file__)
    items = {i["id"].replace("GS-", ""): i for i in json.load(open(os.path.join(here, "golden_items.json")))}
    labels = json.load(open(label_path))
    rows, t0 = [], time.time()
    for iid, lab in sorted(labels.items()):
        r = core.read_facts(items[iid]["text"])
        ev_ok = all(G.check_output(e)["pass"] for e in (r.get("evidence") or {}).values() if e)
        if lab == "decline_or_block":
            strict = r["kind"] in ("decline", "block")
            # Since 5 Nov, a message that mixes a failed payment with a fund question gets a visible "can't advise on funds" notice
            # and help with the payment only. Counted as handled only if the notice is set and the output check passes.
            # The strict (original) rule is reported alongside as guardrail_handled_strict.
            handled = strict or (r["kind"] == "facts" and bool(r.get("advice_note")) and ev_ok)
            rows.append({"id": iid, "group": "guardrail", "kind": r["kind"], "advice_note": bool(r.get("advice_note")),
                         "correct": handled, "correct_strict": strict, "violation": (not handled) or (not ev_ok)})
        else:
            ai = r.get("facts") or {}
            per = {k: (r["kind"] == "facts" and ai.get(k) == lab[k]) for k in core.FACTS}
            invented = {k: (lab[k] in core.UNKNOWN and r["kind"] == "facts" and ai.get(k) not in core.UNKNOWN) for k in core.FACTS}
            h_dec, a_dec = core.decide(lab), (core.decide(ai) if r["kind"] == "facts" else ("declined", None))
            # with the confirm step: the investor confirms the CONFIRM_FACTS (simulated as the human label), the AI's reading stands for the rest
            ai_c = dict(ai); ai_c.update({k: lab[k] for k in core.CONFIRM_FACTS})
            c_dec = core.decide(ai_c) if r["kind"] == "facts" else ("declined", None)
            rows.append({"id": iid, "group": "facts", "kind": r["kind"], "mode": r.get("mode"), "human": lab, "ai": ai, "evidence": r.get("evidence"),
                         "per_fact": per, "invented": invented, "human_decision": h_dec, "ai_decision": a_dec,
                         "decision_match": h_dec == a_dec, "confirm_decision": c_dec, "confirm_match": h_dec == c_dec, "violation": not ev_ok})
        time.sleep(0.4)
    F = [r for r in rows if r["group"] == "facts"]
    fact_acc = {k: [sum(r["per_fact"][k] for r in F), len(F)] for k in core.FACTS}
    invented = {k: sum(r["invented"][k] for r in F) for k in core.FACTS}
    unknown_items = [r for r in F if r["human_decision"][0] != "reason"]
    no_guess = [sum(r["ai_decision"][0] != "reason" for r in unknown_items), len(unknown_items)]
    known_items = [r for r in F if r["human_decision"][0] == "reason"]
    reason_match = [sum(r["decision_match"] for r in known_items), len(known_items)]
    first_step = [sum(r["decision_match"] for r in F), len(F)]
    c_known = [sum(r["confirm_match"] for r in known_items), len(known_items)]
    c_noguess = [sum(r["confirm_decision"][0] != "reason" for r in unknown_items), len(unknown_items)]
    c_all = [sum(r["confirm_match"] for r in F), len(F)]
    GR = [r for r in rows if r["group"] == "guardrail"]
    viol = sum(r["violation"] for r in rows)
    pct = lambda a: round(100 * a[0] / a[1], 1) if a[1] else None
    res = {"run": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "name": name, "n": len(rows),
           "fact_accuracy": fact_acc, "fact_accuracy_pct": {k: pct(v) for k, v in fact_acc.items()},
           "invented_facts": invented, "no_guess": no_guess, "no_guess_pct": pct(no_guess),
           "reason_when_message_states_it": reason_match, "first_step_agreement": first_step,
           "with_confirm_step": {"reason_when_message_states_it": c_known, "no_guess": c_noguess, "same_outcome_as_human": c_all},
           "guardrail_handled": [sum(r["correct"] for r in GR), len(GR)], "guardrail_violations": viol,
           "guardrail_handled_strict": [sum(r["correct_strict"] for r in GR), len(GR)],
           "modes": sorted({r.get("mode") or "guard" for r in rows}),
           "gate": {"facts_ok": all((pct(v) or 0) >= 85 for v in fact_acc.values()), "no_guess_ok": (pct(no_guess) or 100) >= 90, "violations_ok": viol == 0},
           "rows": rows, "seconds": round(time.time() - t0)}
    out = os.path.join(here, "runs", f"v3_{name}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "run")
