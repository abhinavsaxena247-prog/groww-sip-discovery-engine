"""Contradicting facts must never produce a reason (found in user review, 6 Nov)."""
from fix_helper import core

CASES = [
    ({"app_status": "failed", "debited": "yes", "stated_cause": "low_balance"}, ("fallback", None)),
    ({"app_status": "failed", "debited": "refunded", "stated_cause": "over_limit"}, ("fallback", None)),
    ({"app_status": "failed", "debited": "yes", "stated_cause": "mandate_not_ready"}, ("fallback", None)),
    ({"app_status": "failed", "debited": "yes", "stated_cause": "mandate_stopped"}, ("fallback", None)),
    ({"app_status": "failed", "debited": "yes", "stated_cause": "bank_error"}, ("reason", "bank_declined")),
    ({"app_status": "failed", "debited": "no", "stated_cause": "low_balance"}, ("reason", "low_balance")),
    ({"app_status": "failed", "debited": "yes", "stated_cause": "not_said"}, ("reason", "debited_not_invested")),
    ({"app_status": "failed", "debited": "not_said", "stated_cause": "low_balance"}, ("reason", "low_balance")),
]

if __name__ == "__main__":
    ok = 0
    for f, want in CASES:
        got = core.decide(dict(f, recent_change="no"), skip={"app_status", "debited", "stated_cause", "recent_change"})
        ok += got == want
        print("PASS" if got == want else "FAIL", f, got)
    print(f"{ok}/{len(CASES)} passed")
