"""Non-AI baseline on the same v3 test set: the same pipeline with the AI call disabled, so keyword rules read the facts.
Usage: PYTHONPATH=. python3 -m fix_helper.evals.run_baseline_v3 fix_helper/evals/labels_v3_final.json"""
import sys
from fix_helper import core
from fix_helper.evals import run_eval_v3

core.llm.json_call = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("baseline: AI disabled"))
run_eval_v3.time.sleep = lambda s: None
if __name__ == "__main__":
    run_eval_v3.main(sys.argv[1], "baseline_rules_final")
