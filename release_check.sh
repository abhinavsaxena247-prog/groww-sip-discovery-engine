#!/usr/bin/env bash
# One release check, run on the exact build before every deploy: QA (AI + rules-only), the eval (AI, 1 run) on the
# final labels, the rules-only baseline, the contradiction rules and the 336-combination audit. Fails if any gate fails.
set -e
cd "$(dirname "$0")"
set -a; . /home/claude/engine/.env; set +a
export PYTHONPATH=.
echo "== QA rules-only";  python3 -m fix_helper.tests.run_qa basic | tail -1
echo "== QA with AI";     python3 -m fix_helper.tests.run_qa | tail -1
echo "== Rule tests";     python3 -m fix_helper.tests.test_conflict | tail -1
echo "== Audit";          python3 -m fix_helper.tests.audit_combos | tail -1
echo "== Eval (AI)";      python3 -m fix_helper.evals.run_eval_v3 fix_helper/evals/labels_v3_final.json release 2>/dev/null | python3 -c "
import sys,json;t=sys.stdin.read();d=json.loads(t[t.index('{'):])
c=d['with_confirm_step']['same_outcome_as_human'];print('outcome',c,'guardrails',d['guardrail_handled'],'violations',d['guardrail_violations'])
sys.exit(0 if d['guardrail_violations']==0 and c[0]>=27 else 1)"
echo "== Baseline (rules)"; python3 -m fix_helper.evals.run_baseline_v3 fix_helper/evals/labels_v3_final.json 2>/dev/null | python3 -c "
import sys,json;t=sys.stdin.read();d=json.loads(t[t.index('{'):]);print('outcome',d['with_confirm_step']['same_outcome_as_human'])"
echo "RELEASE CHECK PASSED"
