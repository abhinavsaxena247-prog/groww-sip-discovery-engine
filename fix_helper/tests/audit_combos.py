"""Exhaustive audit: every combination of the investor's answers (app status x money taken x reason x recent change)
is run through decide() and checked against what each reason assumes. A combination passes if the reason it gives
is consistent with every answer, or it safely falls back / asks."""
import itertools
from fix_helper import core

APP = ["in_progress", "failed", "sip_cancelled", "not_said"]
DEB = ["yes", "no", "refunded", "not_said"]
CAUSE = ["low_balance", "over_limit", "mandate_not_ready", "mandate_stopped", "bank_error", "none", "not_said"]
CHG = ["yes", "no", "not_said"]
NO_DEBIT = {"low_balance", "over_limit", "mandate_not_ready", "mandate_stopped"}
TAKEN = {"yes", "refunded"}

def problems(f, reason):
    a, d, c, ch = f["app_status"], f["debited"], f["stated_cause"], f["recent_change"]
    p = []
    if reason in ("low_balance", "above_limit", "autopay_not_setup", "mandate_stopped", "failed_after_change") and d in TAKEN:
        p.append("reason says no money left the account, but the investor says money was taken")
    if reason == "still_processing" and (a != "in_progress" or d == "refunded"):
        p.append("says 'still processing' but the app doesn't show in progress, or the money was already returned")
    if reason == "still_processing" and c in NO_DEBIT | {"bank_error"}:
        p.append("says 'still processing' though a failure reason was given")
    if reason == "debited_not_invested" and (d != "yes" or a != "failed"):
        p.append("says money left but wasn't invested, without both 'failed' and 'money taken'")
    if reason in ("cancelled_after_change", "cancelled_after_failures") and a != "sip_cancelled":
        p.append("says cancelled but the app doesn't show cancelled")
    if reason == "bank_declined" and d == "yes":
        p.append("says the bank declined the debit, but the money was taken")
    if reason == "failed_after_change" and ch != "yes":
        p.append("blames a change the investor didn't make")
    return p

def run():
    rows, bad = 0, []
    for a, d, c, ch in itertools.product(APP, DEB, CAUSE, CHG):
        f = {"app_status": a, "debited": d, "stated_cause": c, "recent_change": ch}
        kind, val = core.decide(f, skip=set(f))
        rows += 1
        if kind == "reason":
            pr = problems(f, val)
            if pr:
                bad.append((f, val, pr))
        if core.conflict(f) and kind != "fallback":
            bad.append((f, val, ["conflict not caught"]))
    return rows, bad

if __name__ == "__main__":
    rows, bad = run()
    for f, v, p in bad:
        print("PROBLEM", f, "->", v, "|", "; ".join(p))
    print(f"{rows} combinations checked, {len(bad)} problems")
