"""Stage 4: group drivers into opportunity areas and compare on size, severity, drop-off link,
spread across sources (normalised per source to remove channel bias), first-time and Groww share.
Addressability and constraint-fit are analyst judgements, stated with a rationale (not AI outputs)."""
import json, glob, collections, statistics

items = {i["id"]: i for i in json.load(open("/home/claude/engine/out/stage1.json"))}
T = {}
for f in sorted(glob.glob("/home/claude/engine/out/tags_s*.jsonl")):
    for l in open(f):
        t = json.loads(l); T.setdefault(t["id"], t)   # first tagging per id wins (381 accidental re-tags ignored)
R = [{**items[k], **t} for k, t in T.items() if k in items and t.get("relevant")]
N = len(R)
DROP_EVENTS = {"skipped", "paused", "reduced", "stopped_cancelled", "lapsed_failed_payment"}
def is_drop(r): return bool(DROP_EVENTS & set(r["event"])) or r["dropoff_type"] in ("voluntary", "involuntary", "passive_drift")
drops = [r for r in R if is_drop(r)]
src_tot = collections.Counter(r["source"] for r in R)

AREAS = {
 "A. SIP lapses without the investor deciding (failed debit, mandate, autopay)":
     {"match": lambda r: "payment_mandate_failure" in r["drivers"] or "lapsed_failed_payment" in r["event"] or r["dropoff_type"] == "involuntary",
      "addressability": 3, "fit": 3,
      "why": "Platform owns mandate setup, retry, alerts and recovery; no advice needed."},
 "B. No flexible control when life changes (pause, skip, modify, step-down)":
     {"match": lambda r: "missing_control_pause_skip_modify" in r["drivers"] or set(r["event"]) & {"skipped", "paused", "reduced"},
      "addressability": 3, "fit": 3,
      "why": "Product controls are fully in the platform's hands; neutral, no nudging required."},
 "C. Cash-flow shock or need for money":
     {"match": lambda r: set(r["drivers"]) & {"cashflow_or_income_change", "emergency_or_goal_need_for_money"},
      "addressability": 2, "fit": 3,
      "why": "Cannot fix income; can offer pause/step-down instead of cancel. Overlaps with B."},
 "D. Numbers and outcomes don't match expectations (returns, volatility, confusing figures, goal clarity)":
     {"match": lambda r: set(r["drivers"]) & {"returns_below_expectation", "negative_or_volatile_returns", "confusing_numbers_or_terms", "goal_clarity_or_tracking"},
      "addressability": 2, "fit": 2,
      "why": "Explanation and expectation-setting are addressable; must stay factual and never become advice or fear/FOMO."},
 "E. Trust and support breakdowns (missing money, mismatched holdings, slow redemption, unanswered tickets)":
     {"match": lambda r: "trust_or_support_failure" in r["drivers"],
      "addressability": 2, "fit": 3,
      "why": "Ops/support process heavy; product can add status transparency but core fix is operational."},
 "F. App bugs and general friction":
     {"match": lambda r: "app_friction_or_bug" in r["drivers"],
      "addressability": 2, "fit": 3,
      "why": "Diffuse engineering backlog, not one product opportunity; tracked as hygiene."},
 "G. Fees and hidden charges":
     {"match": lambda r: "fees_or_hidden_charges" in r["drivers"],
      "addressability": 1, "fit": 2,
      "why": "Pricing is a business decision outside a growth PM's product scope."},
}
rows = []
for name, a in AREAS.items():
    m = [r for r in R if a["match"](r)]
    src = collections.Counter(r["source"] for r in m)
    per_src = {s: round(100 * src[s] / src_tot[s], 1) for s in src_tot}
    d = [r for r in m if is_drop(r)]
    rows.append({"area": name, "n": len(m), "share_pct": round(100 * len(m) / N, 1),
                 "per_source_pct": per_src, "sources_with_5plus": sum(1 for s in src if src[s] >= 5),
                 "avg_severity": round(statistics.mean(r["severity"] for r in m), 2) if m else 0,
                 "dropoff_n": len(d), "pct_of_area_with_dropoff": round(100 * len(d) / len(m), 1) if m else 0,
                 "share_of_all_dropoffs_pct": round(100 * len(d) / len(drops), 1),
                 "first_time_n": sum(r["first_time_signal"] == "yes" for r in m),
                 "groww_n": sum(r.get("app") == "Groww" for r in m),
                 "addressability_1to3": a["addressability"], "constraint_fit_1to3": a["fit"], "why": a["why"]})
# composite: drop-off reach x severity x addressability x fit (each normalised); shown alongside raw parts
mx = max(r["share_of_all_dropoffs_pct"] for r in rows)
for r in rows:
    r["opportunity_score"] = round((r["share_of_all_dropoffs_pct"] / mx) * (r["avg_severity"] / 3) * (r["addressability_1to3"] / 3) * (r["constraint_fit_1to3"] / 3) * 100, 1)
rows.sort(key=lambda r: -r["opportunity_score"])
json.dump({"N_relevant": N, "N_dropoffs": len(drops), "areas": rows,
           "note": "Areas overlap (an item can sit in several). Severity, events and drivers are AI tags pending golden-set validation. Addressability/fit = analyst judgement."},
          open("/home/claude/engine/out/opportunities.json", "w"), indent=1, ensure_ascii=False)
print(f"relevant={N} dropoffs={len(drops)}")
for r in rows:
    print(f"{r['opportunity_score']:5.1f} | n={r['n']:5d} ({r['share_pct']}%) | sev {r['avg_severity']} | drop {r['dropoff_n']} = {r['share_of_all_dropoffs_pct']}% of drops | 1st-time {r['first_time_n']} | Groww {r['groww_n']} | src5+ {r['sources_with_5plus']} | {r['area'][:60]}")
    print("        per-source %:", r["per_source_pct"])
