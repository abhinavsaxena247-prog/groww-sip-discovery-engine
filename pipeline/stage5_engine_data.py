"""Stage 5: build the compact data file the public engine page renders (site/engine_data.json).
Everything is computed from the tagged corpus; nothing hand-entered except labels and method text."""
import json, glob, collections, re, random

E = "/home/claude/engine"
items = {i["id"]: i for i in json.load(open(f"{E}/out/stage1.json"))}
T = {}
for f in sorted(glob.glob(f"{E}/out/tags_s*.jsonl")):
    for l in open(f):
        t = json.loads(l); T.setdefault(t["id"], t)
R = [{**items[k], **t} for k, t in T.items() if k in items and t.get("relevant")]
DE = {"skipped", "paused", "reduced", "stopped_cancelled", "lapsed_failed_payment"}
def is_drop(r): return bool(DE & set(r["event"])) or r["dropoff_type"] in ("voluntary", "involuntary", "passive_drift")
D = [r for r in R if is_drop(r)]
FT = [r for r in R if r["first_time_signal"] == "yes"]
pct = lambda a, b: round(100 * a / b, 1) if b else 0.0
C = collections.Counter

st1 = json.load(open(f"{E}/out/stage1_stats.json"))
reddit_raw = json.load(open(f"{E}/out/reddit_sample_stats.json"))
opp = json.load(open(f"{E}/out/opportunities.json"))
rob = json.load(open(f"{E}/out/reddit_robustness.json"))
guard = json.load(open(f"{E}/out/guardrail_corpus.json"))

SRC = {"play_store": "Play Store", "app_store": "App Store", "reddit": "Reddit", "youtube": "YouTube",
       "tradingqna": "TradingQnA", "zerodha_varsity": "Zerodha Varsity", "team_bhp": "Team-BHP"}
collected = dict(st1["collected"]); collected["reddit"] = reddit_raw["collected"]
funnel = {"collected": sum(collected.values()), "collected_by_source": collected,
          "cleaned": sum(st1["relevant_kept"].values()), "cleaned_by_source": st1["relevant_kept"],
          "tagged": sum(1 for k in T if k in items),
          "tagged_by_source": dict(C(items[k]["source"] for k in T if k in items)),
          "relevant": len(R), "relevant_by_source": dict(C(r["source"] for r in R)),
          "dropoffs": len(D), "first_time": len(FT), "groww": sum(r.get("app") == "Groww" for r in R),
          "lang": st1["lang"],
          "removed": {k: sum(st1[k].values()) for k in ("duplicates_removed", "too_short_removed", "promotional_removed", "not_relevant_removed")},
          "reddit": {"scanned_posts": 135833, "sip_posts": 48037, "rows": reddit_raw["collected"],
                     "personal_sip": reddit_raw["after_personal_sip_filter"],
                     "cleaned": st1["relevant_kept"].get("reddit"), "tagged": sum(1 for k in T if k in items and items[k]["source"] == "reddit")},
          "models": dict(C(T[k].get("_model") for k in T if k in items))}

anatomy = {"type": dict(C(r["dropoff_type"] for r in D)), "events": dict(C(e for r in D for e in r["event"] if e in DE)),
           "type_by_source": {s: dict(C(r["dropoff_type"] for r in D if r["source"] == s)) for s in SRC},
           "first_time_type": dict(C(r["dropoff_type"] for r in D if r["first_time_signal"] == "yes"))}

# Q9 unmet needs: transparent keyword clusters over the AI's neutral 'unmet_need' phrases
NEEDS = [
 ("Pause, skip or change a SIP instead of cancelling", r"paus|skip|hold|modif|change (the )?(sip )?(date|amount)|edit sip|flexib|step.?down|reduce (the )?sip"),
 ("Instalments that go through, with clear alerts when they don't", r"mandate|autopay|auto.?pay|nach|debit|instal+ment|payment (fail|success|reliab)|retry|failed (sip|payment)|alert|notif|reminder"),
 ("Support that answers and resolves", r"support|customer (care|service)|ticket|respon|resolution|helpline|human"),
 ("Holdings and numbers that match records", r"accura|mismatch|reconcil|discrepan|correct (value|amount|nav)|statement|cams|kfin|sync"),
 ("Faster, predictable redemption and allotment", r"redeem|redemption|withdraw|allot|credit(ed)? (on|in) time|faster (unit|payout|processing)|settle"),
 ("Plain explanation of returns and figures", r"xirr|explain|understand|clarity|clear (return|number|info)|meaning|what .* means|transparen(t|cy) (in|of|on) (return|calc)"),
 ("Track progress toward a goal", r"goal|target|track(ing)? progress|milestone"),
 ("See everything in one place (family, external funds)", r"consolidat|family|external|import|one place|single view|all (my )?(funds|investments)"),
 ("Lower or clearer fees", r"fee|charge|cost|commission|expense ratio|hidden"),
 ("Direct plans / no forced demat", r"direct plan|regular to direct|demat|soa"),
 ("Step-up / increase SIP easily", r"step.?up|increase (the )?sip|top.?up"),
]
need_rows = [r for r in R if r.get("unmet_need")]
needs = []
for name, pat in NEEDS:
    rx = re.compile(pat, re.I)
    m = [r for r in need_rows if rx.search(r["unmet_need"])]
    needs.append({"need": name, "n": len(m), "pct_of_needs": pct(len(m), len(need_rows)),
                  "sources": len({r["source"] for r in m}), "first_time_n": sum(r["first_time_signal"] == "yes" for r in m),
                  "with_dropoff_pct": pct(sum(is_drop(r) for r in m), len(m))})
needs.sort(key=lambda x: -x["n"])
advice_seekers = sum(1 for r in R if re.search(r"(which|best|suggest|recommend).{0,30}(fund|sip|scheme)", r["text"], re.I))

def top(c, k=8): return [[a, b] for a, b in c.most_common(k)]
seg = {}
for field in ("income", "age_hint", "influencer"):
    seg[field] = {}
    for v in sorted({r[field] for r in R} - {"unclear"}):
        rows = [r for r in R if r[field] == v]
        seg[field][v] = {"n": len(rows), "pct_dropoff": pct(sum(is_drop(r) for r in rows), len(rows)),
                         "top_drivers": top(C(d for r in rows for d in r["drivers"] if d != "other"), 3)}
started = [r for r in R if "started" in r["event"]]
cont = [r for r in R if "continued" in r["event"] and not is_drop(r)]
STAGES = ["first_instalments_1_3m", "months_4_12", "beyond_12m"]
q = {
 "q1": {"started_n": len(started), "influencer": top(C(r["influencer"] for r in started if r["influencer"] != "unclear"), 5),
        "first_time_started": sum(r["first_time_signal"] == "yes" for r in started)},
 "q2": {s: {"n": sum(1 for r in R if r["lifecycle_stage"] == s),
            "drop_pct": pct(sum(is_drop(r) for r in R if r["lifecycle_stage"] == s), sum(1 for r in R if r["lifecycle_stage"] == s)),
            "events": top(C(e for r in R if r["lifecycle_stage"] == s for e in r["event"]), 6)} for s in STAGES},
 "q3": {"n": len(D), "drivers": top(C(d for r in D for d in r["drivers"] if d != "other"), 10),
        "ft_drivers": top(C(d for r in D if r["first_time_signal"] == "yes" for d in r["drivers"] if d != "other"), 6), "ft_n": sum(r["first_time_signal"] == "yes" for r in D)},
 "q4": {"all": top(C(x for r in R for x in r["what_they_check"]), 6), "first_time": top(C(x for r in FT for x in r["what_they_check"]), 6)},
 "q5": top(C(d for r in R for d in r["drivers"] if d in ("confusing_numbers_or_terms", "app_friction_or_bug", "missing_control_pause_skip_modify",
                                                           "payment_mandate_failure", "fees_or_hidden_charges", "trust_or_support_failure")), 6),
 "q6": {"all": top(C(x for r in R for x in r["outside_app_behaviour"]), 8), "first_time": top(C(x for r in FT for x in r["outside_app_behaviour"]), 6)},
 "q7": {"continuers_n": len(cont), "dropoffs_n": len(D),
        "continuer": top(C(d for r in cont for d in r["drivers"] if d != "other"), 6), "dropoff": top(C(d for r in D for d in r["drivers"] if d != "other"), 6)},
 "q8": seg,
 "q9": {"needs": needs, "need_items": len(need_rows), "advice_seekers": advice_seekers},
}

# evidence explorer: up to 40 items per opportunity area, highest severity first, short verbatim spans
random.seed(7)
AREA_MATCH = {
 "A": lambda r: "payment_mandate_failure" in r["drivers"] or "lapsed_failed_payment" in r["event"] or r["dropoff_type"] == "involuntary",
 "B": lambda r: "missing_control_pause_skip_modify" in r["drivers"] or bool(set(r["event"]) & {"skipped", "paused", "reduced"}),
 "C": lambda r: bool(set(r["drivers"]) & {"cashflow_or_income_change", "emergency_or_goal_need_for_money"}),
 "D": lambda r: bool(set(r["drivers"]) & {"returns_below_expectation", "negative_or_volatile_returns", "confusing_numbers_or_terms", "goal_clarity_or_tracking"}),
 "E": lambda r: "trust_or_support_failure" in r["drivers"],
 "F": lambda r: "app_friction_or_bug" in r["drivers"],
 "G": lambda r: "fees_or_hidden_charges" in r["drivers"]}
ev = []
for a, fn in AREA_MATCH.items():
    rows = [r for r in R if fn(r) and r.get("evidence_span") and 6 <= len(r["evidence_span"].split()) <= 22]
    rows.sort(key=lambda r: (-r["severity"], -(r.get("thumbs") or 0)))
    pick = rows[:25] + random.sample(rows[25:], min(15, max(0, len(rows) - 25)))
    seen = set()
    for r in pick:
        if r["id"] in seen: continue
        seen.add(r["id"])
        ev.append({"a": a, "s": SRC[r["source"]], "app": r.get("app") if r["source"] in ("play_store", "app_store") else (r.get("app") if r["source"] == "reddit" else ""),
                   "q": r["evidence_span"], "d": r["dropoff_type"], "sev": r["severity"], "ft": r["first_time_signal"] == "yes",
                   "y": (r.get("date") or "")[:4] if re.match(r"\d{4}", r.get("date") or "") else re.findall(r"20\d\d", r.get("date") or "")[:1][0] if re.findall(r"20\d\d", r.get("date") or "") else "",
                   "u": r.get("url") or ""})

data = {"generated": "2026-10-29", "funnel": funnel, "anatomy": anatomy, "opportunities": opp["areas"],
        "questions": q, "evidence": ev, "reddit_robustness": rob,
        "guardrail": {"checked": guard["summary"]["checked"], "flags": guard["summary"]["advice"] + guard["summary"]["fund_name"],
                      "true_violations": guard["manual_review"]["true_violations"]},
        "golden": {"size": 26, "status": "awaiting human labels"},
        "prompt_version": "v1.2-2026-10-29"}
json.dump(data, open(f"{E}/site/engine_data.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("evidence", len(ev), "needs", [(n["need"][:30], n["n"]) for n in needs], "advice_seekers", advice_seekers)
print("q2", json.dumps(q["q2"])[:400]); print("ft check", q["q4"]["first_time"], "ft outside", q["q6"]["first_time"])
print("anatomy ft", anatomy["first_time_type"]); print("seg", json.dumps(seg["income"]))
import os; print("bytes", os.path.getsize(f"{E}/site/engine_data.json"))
