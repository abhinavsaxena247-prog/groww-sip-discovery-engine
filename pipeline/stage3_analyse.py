"""Stage 3: quantify themes, compare opportunity areas, answer the 9 discovery questions.
Inputs: out/stage1.json + out/tags_s*.jsonl.  Output: out/analysis.json (feeds engine page, deck, Evidence Log)."""
import json, glob, collections, re, statistics
from datetime import datetime

items = {i["id"]: i for i in json.load(open("/home/claude/engine/out/stage1.json"))}
tags = {}
for f in sorted(glob.glob("/home/claude/engine/out/tags_s*.jsonl")):
    for line in open(f):
        try:
            t = json.loads(line); tags.setdefault(t["id"], t)
        except Exception: pass

def year(d):
    for fmt in ("%Y-%m-%d", "%B %d, %Y"):
        try: return datetime.strptime(d[:10] if fmt == "%Y-%m-%d" else d, fmt).year
        except Exception: pass
    m = re.search(r"(20\d\d)", d or ""); return int(m.group(1)) if m else None

R = []  # relevant, tagged rows
for k, t in tags.items():
    if k not in items or not t.get("relevant"): continue
    it = items[k]
    R.append({**it, **t, "year": year(it.get("date", "")), "is_groww": it.get("app") == "Groww"})
N = len(R)
DROP_EVENTS = {"skipped", "paused", "reduced", "stopped_cancelled", "lapsed_failed_payment"}
def is_drop(r): return bool(DROP_EVENTS & set(r["event"])) or r["dropoff_type"] in ("voluntary", "involuntary", "passive_drift")
def pct(a, b): return round(100 * a / b, 1) if b else 0.0

summary = {"tagged": len(tags), "relevant": N,
           "relevant_rate": pct(N, len(tags)),
           "by_source": collections.Counter(r["source"] for r in R),
           "groww_items": sum(r["is_groww"] for r in R),
           "first_time_yes": sum(r["first_time_signal"] == "yes" for r in R),
           "dropoff_items": sum(is_drop(r) for r in R),
           "models": collections.Counter(t.get("_model") for t in tags.values())}

# --- drop-off anatomy (voluntary / involuntary / passive) ---
drop = [r for r in R if is_drop(r)]
anatomy = {"n": len(drop), "type": collections.Counter(r["dropoff_type"] for r in drop),
           "events": collections.Counter(e for r in drop for e in r["event"] if e in DROP_EVENTS),
           "by_stage": collections.Counter(r["lifecycle_stage"] for r in drop)}

# --- drivers: size, spread, severity, drop link ---
SOURCES = sorted({r["source"] for r in R})
drivers = {}
for d in sorted({x for r in R for x in r["drivers"]}):
    rows = [r for r in R if d in r["drivers"]]
    src = collections.Counter(r["source"] for r in rows)
    drivers[d] = {"n": len(rows), "share_of_relevant": pct(len(rows), N),
                  "sources": dict(src), "n_sources": len(src),
                  "triangulated": sum(1 for s, c in src.items() if c >= 5) >= 2,
                  "avg_severity": round(statistics.mean(r["severity"] for r in rows), 2),
                  "pct_sev3": pct(sum(r["severity"] == 3 for r in rows), len(rows)),
                  "pct_with_dropoff": pct(sum(is_drop(r) for r in rows), len(rows)),
                  "share_of_all_dropoffs": pct(sum(is_drop(r) for r in rows), len(drop)),
                  "groww_n": sum(r["is_groww"] for r in rows),
                  "first_time_n": sum(r["first_time_signal"] == "yes" for r in rows),
                  "examples": [{"source": r["source"], "app": r.get("app"), "evidence": r["evidence_span"], "url": r.get("url")}
                               for r in sorted(rows, key=lambda r: (-r["severity"], -(r.get("thumbs") or 0)))[:4]]}

# --- 9 questions ---
def top(counter, k=8): return [(a, b) for a, b in counter.most_common(k)]
started = [r for r in R if "started" in r["event"]]
cont = [r for r in R if "continued" in r["event"] and not is_drop(r)]
q = {
 "Q1_why_start_expectations": {"n": len(started),
     "influencer": top(collections.Counter(r["influencer"] for r in started if r["influencer"] != "unclear")),
     "expectation_gaps": [r["expectation_gap"] for r in started if r["expectation_gap"]][:40]},
 "Q2_behaviour_change": {"stage_x_event": {s: dict(collections.Counter(e for r in R if r["lifecycle_stage"] == s for e in r["event"]))
                                            for s in ["first_instalments_1_3m", "months_4_12", "beyond_12m"]}},
 "Q3_pause_reduce_stop": {"n": len(drop), "drivers": top(collections.Counter(d for r in drop for d in r["drivers"]), 12),
                          "type": dict(anatomy["type"])},
 "Q4_what_they_check": top(collections.Counter(x for r in R for x in r["what_they_check"]), 10),
 "Q5_in_app_confusion_worry": top(collections.Counter(d for r in R for d in r["drivers"]
                                  if d in ("confusing_numbers_or_terms", "app_friction_or_bug", "missing_control_pause_skip_modify",
                                           "payment_mandate_failure", "fees_or_hidden_charges", "trust_or_support_failure"))),
 "Q6_outside_app": top(collections.Counter(x for r in R for x in r["outside_app_behaviour"]), 10),
 "Q7_continuers_vs_dropoffs": {"continuers_n": len(cont), "dropoffs_n": len(drop),
     "continuer_drivers": top(collections.Counter(d for r in cont for d in r["drivers"]), 8),
     "dropoff_drivers": top(collections.Counter(d for r in drop for d in r["drivers"]), 8)},
 "Q8_segments": {},
 "Q9_unmet_needs_raw_n": sum(1 for r in R if r["unmet_need"]),
}
for field in ("income", "age_hint", "influencer"):
    seg = {}
    for v in sorted({r[field] for r in R} - {"unclear"}):
        rows = [r for r in R if r[field] == v]
        seg[v] = {"n": len(rows), "small_sample": len(rows) < 30, "pct_dropoff": pct(sum(is_drop(r) for r in rows), len(rows)),
                  "top_drivers": top(collections.Counter(d for r in rows for d in r["drivers"]), 4)}
    q["Q8_segments"][field] = seg

out = {"summary": summary, "anatomy": anatomy, "drivers": drivers, "questions": q,
       "unmet_needs": [{"id": r["id"], "need": r["unmet_need"], "source": r["source"], "sev": r["severity"],
                        "drop": is_drop(r), "groww": r["is_groww"]} for r in R if r["unmet_need"]],
       "emergent": collections.Counter(r["emergent_theme"].lower().strip() for r in R if r["emergent_theme"]).most_common(60)}
json.dump(out, open("/home/claude/engine/out/analysis.json", "w"), ensure_ascii=False, indent=1, default=dict)
print(json.dumps({"summary": summary, "anatomy": anatomy}, indent=1, default=dict))
print("\nDRIVERS (n, share%, sev, %drop, share of drops, sources)")
for d, v in sorted(drivers.items(), key=lambda kv: -kv[1]["n"]):
    print(f"{d:38s} {v['n']:5d} {v['share_of_relevant']:5.1f}% sev{v['avg_severity']} drop{v['pct_with_dropoff']:5.1f}% ofdrops{v['share_of_all_dropoffs']:5.1f}% tri={v['triangulated']} {v['sources']}")
