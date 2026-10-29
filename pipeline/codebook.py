"""Codebook + classifier prompt for the Discovery Engine (stage 2).
Lenses are chosen to TEST, not to presume answers: every field allows 'none'/'unclear',
and 'emergent_theme' captures anything the codebook misses (clustered in stage 3)."""

MODEL = "claude-haiku-5-5"      # batch tagging; logged in Evidence Log
PROMPT_VERSION = "v1.2-2026-10-29"
TEMPERATURE = 0

CODEBOOK = {
  "relevant": "true only if the text is about the writer's OWN experience with SIPs/mutual-fund investing (not stock trading, F&O, IPO, loans)",
  "first_time_signal": "yes = writer says they are new/beginner/first SIP/started recently; no = clearly experienced; unclear",
  "lifecycle_stage": ["pre_start", "starting_setup", "first_instalments_1_3m", "months_4_12", "beyond_12m", "unclear"],
  "event": ["started", "continued", "checked_tracked", "skipped", "paused", "reduced", "increased_stepup",
            "stopped_cancelled", "lapsed_failed_payment", "redeemed_withdrew", "switched_platform", "none"],
  "dropoff_type": ["voluntary", "involuntary", "passive_drift", "none"],
  "dropoff_type_definitions": "voluntary = writer chose to stop/pause/skip/reduce; involuntary = SIP lapsed or failed without the writer deciding (mandate, autopay, bank debit, OTP, app error); passive_drift = writer lost track, forgot, disengaged; none = no drop-off described. Pick ONE.",
  "drivers": ["cashflow_or_income_change", "emergency_or_goal_need_for_money",
              "returns_below_expectation", "negative_or_volatile_returns", "payment_mandate_failure",
              "app_friction_or_bug", "missing_control_pause_skip_modify", "confusing_numbers_or_terms",
              "fees_or_hidden_charges", "trust_or_support_failure", "advice_from_others_or_media",
              "goal_clarity_or_tracking", "habit_or_automation_positive", "other"],
  "what_they_check": ["returns_pl", "nav", "xirr", "instalment_status", "portfolio_value", "fund_rank_or_category",
                      "nothing_mentioned"],
  "outside_app_behaviour": ["asked_friend_family", "youtube_social", "forum_reddit", "amc_or_cams_kfintech",
                            "advisor", "other_app_or_tracker", "bank_statement", "customer_support", "none_mentioned"],
  "segment_signals": {"income": ["salaried", "variable_self_employed", "student_no_income", "unclear"],
                      "age_hint": ["under_25", "25_35", "over_35", "unclear"],
                      "influencer": ["friend_family", "social_media", "app_nudge", "employer", "self", "unclear"]},
  "expectation_gap": "one short phrase: what they expected vs what happened, or ''",
  "unmet_need": "one short phrase in neutral words: what they wanted that the product did not give, or ''",
  "emergent_theme": "a 2-5 word label for the main idea IF none of the drivers fit, else ''",
  "severity": "1 = minor annoyance, 2 = changed behaviour (skipped/reduced/considered stopping), 3 = stopped, lapsed or left platform",
  "evidence_span": "<= 20 words copied from the text that justify the tags",
}

DISCOVERY_QUESTIONS = {
  "Q1 why start & expectations": ["event=started", "expectation_gap"],
  "Q2 behaviour change after start": ["lifecycle_stage", "event"],
  "Q3 what leads to pause/reduce/stop": ["drivers x event in {skipped,paused,reduced,stopped_cancelled,lapsed}"],
  "Q4 what they check & how often": ["what_they_check"],
  "Q5 in-app confusion/worry": ["drivers in {confusing_numbers_or_terms, app_friction_or_bug, missing_control...}"],
  "Q6 outside-app behaviour when unsure": ["outside_app_behaviour"],
  "Q7 continuers vs drop-offs": ["drivers for event=continued vs drop-off events"],
  "Q8 segment differences": ["segment_signals x drivers (n shown, small cuts flagged)"],
  "Q9 consistent unmet needs": ["unmet_need clustered"],
}

SYSTEM = """You tag Indian retail-investor feedback for a product research study about SIP continuation.
Each item is independent: tag it ONLY from its own text. Never carry details from one item to another.
Return ONLY JSON matching the schema. Use the exact labels given.
Rules:
- relevant = true only if the writer describes their OWN experience, behaviour, question, worry or need about
  SIPs or mutual-fund investing. Generic praise or abuse with no SIP/MF detail ("good app for MF") = false.
  Stock trading, F&O, IPO, loans, brokerage = false unless SIP/MF experience is also described.
- event: only events the writer says happened to them. [] if none.
- dropoff_type: 'none' unless the text describes a SIP being skipped, paused, reduced, stopped, cancelled,
  or lapsing/failing. Redeeming or a support complaint alone is NOT a drop-off.
- drivers: reasons the writer gives or clearly implies for what happened. [] if none.
- unmet_need: only if the writer states a want, request or missing capability, or it is the direct
  opposite of their complaint. Otherwise ''. Neutral wording, no fund names.
- severity: 1 = mention/annoyance; 2 = changed SIP behaviour or seriously considered it; 3 = stopped,
  lapsed, withdrew everything or left the platform. Use 1 when not relevant.
- segment fields and first_time_signal: 'unclear' unless the text says so.
- evidence_span: copied verbatim from the text, max 20 words; '' if not relevant.
- Hinglish/Hindi: understand the meaning; keep evidence_span in the original words.
- Never give investment opinions or name funds/stocks in any field."""

def user_prompt(item):
    import json
    return ("CODEBOOK:\n" + json.dumps(CODEBOOK, ensure_ascii=False) +
            f"\n\nSOURCE: {item['source']} | APP: {item.get('app')} | RATING: {item.get('rating')}\n"
            f"TEXT: {item['text'][:2500]}\n\nReturn the JSON object now.")


def _enum(vals): return {"type": "STRING", "enum": vals}
def _arr(vals): return {"type": "ARRAY", "items": _enum(vals)}
CB = CODEBOOK
ITEM_SCHEMA = {"type": "OBJECT", "properties": {
    "id": {"type": "STRING"},
    "relevant": {"type": "BOOLEAN"},
    "first_time_signal": _enum(["yes", "no", "unclear"]),
    "lifecycle_stage": _enum(CB["lifecycle_stage"]),
    "event": _arr(CB["event"]),
    "dropoff_type": _enum(CB["dropoff_type"]),
    "drivers": _arr(CB["drivers"]),
    "what_they_check": _arr(CB["what_they_check"]),
    "outside_app_behaviour": _arr(CB["outside_app_behaviour"]),
    "income": _enum(CB["segment_signals"]["income"]),
    "age_hint": _enum(CB["segment_signals"]["age_hint"]),
    "influencer": _enum(CB["segment_signals"]["influencer"]),
    "expectation_gap": {"type": "STRING"},
    "unmet_need": {"type": "STRING"},
    "emergent_theme": {"type": "STRING"},
    "severity": {"type": "INTEGER"},
    "evidence_span": {"type": "STRING"}},
  "required": ["id", "relevant", "first_time_signal", "lifecycle_stage", "event", "dropoff_type", "drivers",
               "what_they_check", "outside_app_behaviour", "income", "age_hint", "influencer",
               "expectation_gap", "unmet_need", "emergent_theme", "severity", "evidence_span"]}
RESPONSE_SCHEMA = {"type": "ARRAY", "items": ITEM_SCHEMA}
