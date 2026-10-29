"""The guarded question-answering pipeline.
Order for every message: rule check -> AI intent check -> grounded answer (counting tools) -> output check.
Falls back to basic mode (direct counts, same rule and output checks) when no AI quota is available."""
import json
import re

from engine import data as D
from engine import guard as G
from engine import llm

CODE = {
    "lifecycle_stage": ["pre_start", "starting_setup", "first_instalments_1_3m", "months_4_12", "beyond_12m", "unclear"],
    "event": ["started", "continued", "checked_tracked", "skipped", "paused", "reduced", "increased_stepup", "stopped_cancelled",
              "lapsed_failed_payment", "redeemed_withdrew", "switched_platform"],
    "dropoff_type": ["voluntary", "involuntary", "passive_drift", "none"],
    "drivers": ["cashflow_or_income_change", "emergency_or_goal_need_for_money", "returns_below_expectation", "negative_or_volatile_returns",
                "payment_mandate_failure", "app_friction_or_bug", "missing_control_pause_skip_modify", "confusing_numbers_or_terms",
                "fees_or_hidden_charges", "trust_or_support_failure", "advice_from_others_or_media", "goal_clarity_or_tracking",
                "habit_or_automation_positive", "other"],
    "what_they_check": ["returns_pl", "nav", "xirr", "instalment_status", "portfolio_value", "fund_rank_or_category"],
    "outside_app_behaviour": ["asked_friend_family", "youtube_social", "forum_reddit", "amc_or_cams_kfintech", "advisor",
                              "other_app_or_tracker", "bank_statement", "customer_support"],
}
OFFICIAL = "AMFI investor education (amfiindia.com), SEBI (sebi.gov.in) or a SEBI-registered investment adviser"
REPLIES = {
    "abuse": "I can't respond to abusive or offensive language. If you rephrase your question about SIP behaviour, I'll answer it from the data.",
    "pii": "Please don't share personal details such as a {kind}. Your message was not sent to any AI or stored. This engine can't look up accounts; for a problem with your own SIP, contact your app's support (for Groww: groww.in/help). You can ask what other investors wrote about the same kind of problem.",
    "injection": "I can't change how I work or reveal my instructions. I only describe what investors wrote in public comments, and I never give investment advice.",
    "advice": f"I can't advise you on which fund, app or amount to choose, predict returns or markets, or say whether to start, stop or change a SIP. This engine only studies what investors wrote. For guidance, try {OFFICIAL}.",
    "off_topic": "That's outside what this engine covers. I answer questions about first-time SIP investors in India: why they start, what they check, what worries them, and why SIPs continue, pause or stop.",
    "account_help": "I can't see or fix anyone's account or transactions. For a failed instalment or mandate on your own SIP, your app's support can check it (for Groww: groww.in/help). I can show what other investors wrote when this happened to them.",
    "too_long": "Please keep your question under 800 characters.",
    "empty": "Type a question first.",
}


def greeting():
    return (f"Hi. I answer questions about what {len(D.corpus()['rows']):,} tagged public comments say about SIPs: why people start, stop, "
            "pause or keep going, what they check, where they look for help, and how this differs by app, source and segment. "
            "Every number I give is counted from the data, and I don't give investment advice.")


def reframe_for(q):
    s = q.lower()
    if re.search(r"(stop|band|cancel|pause|skip|chhod|chod|continue|keep)", s):
        return "What did investors say led them to stop, pause or keep their SIP?"
    if re.search(r"(fund|scheme|stock|which|kaun|best)", s):
        return "What do first-time investors say about choosing where to start?"
    if re.search(r"(return|grow|market|nav|loss|profit)", s):
        return "What did investors expect from returns, and what did they describe happening?"
    if re.search(r"(app|groww|zerodha|indmoney|upstox)", s):
        return "What problems do investors describe most often on each app?"
    if re.search(r"(invest|amount|money|much)", s):
        return "How do investors describe changes in their income affecting their SIP?"
    return "Why do first-time investors stop their SIPs?"


INTENT_SCHEMA = {"type": "OBJECT", "properties": {
    "intent": {"type": "STRING", "enum": ["research", "advice", "account_help", "off_topic", "abusive", "greeting"]},
    "reframe": {"type": "STRING"}}, "required": ["intent", "reframe"]}
INTENT_PROMPT = """You are the intent filter for a research engine. The engine ONLY describes what public Indian investor comments (app reviews, Reddit, YouTube, forums) say about SIPs and mutual funds. It never gives investment advice.
Classify the user's message into exactly one intent:
- "research": asks what investors say, do, feel, check, experience or need; reasons, patterns, comparisons across apps, sources, segments or time; quotes; questions about the data or method; product or research questions about the findings (for example what a product team should look at). Hinglish counts.
- "advice": asks what THEY should do with their money: which fund, app or amount; whether a fund is good or safe; whether to start, stop, pause, continue or switch; whether stopping is good or bad; return or market predictions; tax or allocation guidance.
- "account_help": wants help with their own account, transaction, mandate or SIP.
- "off_topic": anything unrelated to SIP or investor-behaviour research.
- "abusive": insults, slurs, harassment or sexual content.
- "greeting": hello, thanks, or asks what the engine can do.
Also return "reframe": for advice or account_help, one neutral research question about what investors wrote on the same topic (no fund names); otherwise "".
User message: \"\"\"{q}\"\"\""""

ANSWER_RULES = f"""You are the NL-Groww Discovery Engine. You answer questions about a research corpus of public Indian investor comments about SIPs and mutual funds (Play Store and App Store reviews of Groww and 9 other apps, Reddit, YouTube, TradingQnA, Zerodha Varsity, Team-BHP), each tagged by an AI with a fixed codebook.
ALWAYS call tools to get numbers and quotes before answering. Never estimate, round up or invent a number; only state numbers that appear in tool results. Give each count with its base, for example "212 of 1,480 drop-off comments (14.3%)". If a base is under 30, say it is a small sample. Comments can carry several tags, so shares need not add to 100%. When useful, mention that these are AI tags on public comments and directional.
Write plain English, at most 160 words, no headings or tables. Use at most two short quotes, in quotation marks, only from find_quotes. If the data cannot answer the question, say so plainly and say what it can show instead.
Hard rules: never recommend, rank, praise or criticise a specific fund, scheme, stock or AMC, and never repeat fund names even if a quote contains one; never tell anyone to start, continue, pause, stop or change a SIP, or judge whether doing so is good or bad; never predict returns or markets; never use fear, FOMO or urgency. If the conversation drifts into advice, say the engine only describes what investors wrote and point to {OFFICIAL}.
Field values you can filter on: {json.dumps(CODE)}"""


def _arr(vals):
    return {"type": "ARRAY", "items": {"type": "STRING", "enum": vals}}


FILTER = {"type": "OBJECT", "description": "All optional, combined with AND; a list matches any of its values.", "properties": {
    "source": _arr(D.SRC_ORDER),
    "app": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Store app (Groww, Zerodha Coin, Zerodha Kite, Upstox, Angel One, MO Riise, Paytm Money, INDmoney, ET Money, Kuvera) or subreddit (r/mutualfunds, r/IndiaInvestments, r/personalfinanceindia)"},
    "first_time": {"type": "BOOLEAN", "description": "true = the writer says they are a first-time or new investor"},
    "stage": _arr(CODE["lifecycle_stage"]), "event_any": _arr(CODE["event"]), "drop": _arr(CODE["dropoff_type"]),
    "driver_any": _arr(CODE["drivers"]), "check_any": _arr(CODE["what_they_check"]), "outside_any": _arr(CODE["outside_app_behaviour"]),
    "income": _arr(["salaried", "variable_self_employed", "student_no_income"]), "age": _arr(["under_25", "25_35", "over_35"]),
    "influencer": _arr(["friend_family", "social_media", "app_nudge", "employer", "self"]),
    "dropoff_only": {"type": "BOOLEAN", "description": "only comments describing a SIP skipped, paused, reduced, stopped or lapsing"},
    "year_min": {"type": "INTEGER"}, "year_max": {"type": "INTEGER"}, "min_severity": {"type": "INTEGER", "description": "1 to 3"},
    "keyword": {"type": "STRING", "description": "words searched in the evidence quote and unmet-need phrase; separate alternatives with |"}}}
FIELD_DESC = "one of: source, app, stage, event_any, drop, driver_any, check_any, outside_any, income, age, influencer"
TOOLS = [
    {"name": "count_comments", "description": "Count relevant tagged comments matching the filters. Returns matching_comments, total_relevant and share_pct.",
     "parameters": {"type": "OBJECT", "properties": {"filters": FILTER}}},
    {"name": "breakdown", "description": "Count each value of one field among comments matching the filters. Returns base_comments, small_sample and top values with n and pct_of_base.",
     "parameters": {"type": "OBJECT", "properties": {"field": {"type": "STRING", "description": FIELD_DESC}, "filters": FILTER, "top": {"type": "INTEGER"}}, "required": ["field"]}},
    {"name": "compare_groups", "description": "Break down one field for two groups side by side (for example first-time vs other investors, Groww vs other apps, Reddit vs Play Store).",
     "parameters": {"type": "OBJECT", "properties": {"field": {"type": "STRING", "description": FIELD_DESC}, "group_a": FILTER, "group_b": FILTER,
                                                     "label_a": {"type": "STRING"}, "label_b": {"type": "STRING"}}, "required": ["field", "group_a", "group_b"]}},
    {"name": "trend_by_year", "description": "For each year, how many relevant comments match the filters and what share of that year they are.",
     "parameters": {"type": "OBJECT", "properties": {"filters": FILTER}}},
    {"name": "find_quotes", "description": "Up to 6 short verbatim evidence quotes (source, app, year, link) from comments matching the filters. Quotes naming funds are excluded.",
     "parameters": {"type": "OBJECT", "properties": {"filters": FILTER, "limit": {"type": "INTEGER"}}}},
]


def _executors(led):
    return {
        "count_comments": lambda a: D.count(a.get("filters") or {}, led),
        "breakdown": lambda a: D.breakdown(str(a.get("field")), a.get("filters") or {}, led, a.get("top") or 8),
        "compare_groups": lambda a: D.compare(str(a.get("field")), a.get("group_a") or {}, a.get("group_b") or {}, led, a.get("label_a"), a.get("label_b")),
        "trend_by_year": lambda a: D.trend(a.get("filters") or {}, led),
        "find_quotes": lambda a: D.quotes(a.get("filters") or {}, led, a.get("limit") or 4),
    }


# ---------- basic mode (no AI): deterministic router over the same counting tools ----------
TOPIC = re.compile(r"(sip|mutual|fund|invest|groww|zerodha|coin|kite|indmoney|upstox|angel|paytm|kuvera|mandate|autopay|instal|nav|xirr|portfolio|return|stop|band|chhod|chod|pause|skip|lapse|cancel|continu|drop|redeem|redemption|withdraw|first|beginner|new|app|reddit|youtube|review|comment|people|investor|log |support|complain|fee|charge|need|want|reason|why|kyun|kyu|check|track|segment|salar|student|income|age|influenc|data|engine|theme|opportunit|step.?up|market|loss|profit|expect)", re.I)
GREET = re.compile(r"^(hi|hii+|hello|hey|namaste|thanks|thank you|ok|okay)\b[\s!.?]*$|what can you do|what do you do|how does this work|who are you|help me use|^what('s| is) (this|that)\b|^what is this (page|engine|tool)", re.I)
FIRST_PERSON = re.compile(r"\b(i|me|my|mine|mujhe|mera|meri|main|hum|humein)\b", re.I)
DECISION = re.compile(r"\b(better|best|safe|enough|choose|pick|should|what (should|do) i do|good|worth|returns?|give|lu|lun|loon|karu|karun|start|stop|continue|invest|buy|sell)\b", re.I)
THIRD = re.compile(r"\b(people|investors|others|users|log|comments|reviews|data)\b", re.I)


def route(q):
    s = q.lower()
    f = {}
    if re.search(r"(first[- ]?time|first sip|beginner|new investor|newbie|pehli|naya|nayi|naye|just started|new to)", s):
        f["first_time"] = True
    apps = ["groww", "zerodha coin", "zerodha kite", "upstox", "angel one", "paytm money", "indmoney", "et money", "kuvera"]
    a = next((x for x in apps if x in s), None)
    if a:
        f["app"] = [a]
    elif re.search(r"\bzerodha|\bcoin\b", s):
        f["app"] = ["Zerodha Coin"]
    srcs = {"reddit": "reddit", "youtube": "youtube", "play store": "play_store", "app store": "app_store", "tradingqna": "tradingqna",
            "varsity": "zerodha_varsity", "team-bhp": "team_bhp", "team bhp": "team_bhp"}
    for k, v in srcs.items():
        if k in s:
            f.setdefault("source", []).append(v)
    if re.search(r"(stop|band|cancel|paus|skip|lapse|drop|chhod|chod|quit|discontinu)", s):
        f["dropoff_only"] = True
    if re.search(r"(autopay|auto-pay|mandate|payments? fail|fail(ed|s|ing)? payment|debit|nach|instal+ments? fail|sip fail|payment issue|payment problem)", s):
        f["driver_any"] = ["payment_mandate_failure"]
    elif re.search(r"(pause|skip|modify|change date|edit)", s):
        f["driver_any"] = ["missing_control_pause_skip_modify"]
    elif re.search(r"(job|income|salary|emergency|money tight|cash)", s):
        f["driver_any"] = ["cashflow_or_income_change", "emergency_or_goal_need_for_money"]
    elif re.search(r"(support|customer care|ticket|help desk)", s):
        f["driver_any"] = ["trust_or_support_failure"]
    elif re.search(r"(fee|charge|hidden|commission)", s):
        f["driver_any"] = ["fees_or_hidden_charges"]
    elif re.search(r"(xirr|nav|confus|understand)", s):
        f["driver_any"] = ["confusing_numbers_or_terms"]
    elif re.search(r"(market (fall|falls|falling|crash|crashed|down|drop)|volatil|nifty (fall|down))", s):
        f["driver_any"] = ["negative_or_volatile_returns"]
    elif re.search(r"(return|loss|profit|expect)", s):
        f["driver_any"] = ["returns_below_expectation", "negative_or_volatile_returns"]
    inc = [v for k, v in (("salar", "salaried"), ("student", "student_no_income"), ("college", "student_no_income"),
                          ("variable", "variable_self_employed"), ("freelanc", "variable_self_employed"), ("self-employed", "variable_self_employed"),
                          ("business", "variable_self_employed")) if k in s]
    if inc:
        f["income"] = sorted(set(inc), key=inc.index)
    if re.search(r"step.?up", s):
        f["keyword"] = "step up|step-up|stepup|increase"
    if re.search(r"redemption|redeem|withdraw", s):
        f["keyword"] = "redeem|redemption|withdraw"
    field, title = "driver_any", "Reasons mentioned"
    if re.search(r"(check|look at|track|monitor|dekh)", s):
        field, title = "check_any", "What they check"
    elif re.search(r"(where|outside|help|unsure|turn to|go to|ask)", s) and "driver_any" not in f:
        field, title = "outside_any", "Where they turn"
    elif re.search(r"(influenc|who got|who made|recommended by)", s):
        field, title = "influencer", "Who influenced them"
    elif re.search(r"(which source|by source|per source|each source|channel)", s):
        field, title = "source", "By source"
    elif re.search(r"(which app|by app|per app|across apps|specific to)", s):
        field, title = "app", "By app"
    elif re.search(r"(what happen|outcome|result|do when|did they)", s) or ("driver_any" in f and not re.search(r"why|reason|kyun|kyu", s)):
        field, title = "event_any", "What people described happening"
    if "driver_any" in f and field == "driver_any":
        field, title = "event_any", "What people described happening"
    return f, field, title


def basic_answer(q, led):
    f, field, title = route(q)
    s = q.lower()
    E = D.engine_data()
    if re.search(r"(need|needs|want|wish|ask(ing)? for|request)", s) and "driver_any" not in f:
        N = E["questions"]["q9"]["needs"]
        led.note(E["questions"]["q9"]["need_items"], *[n["n"] for n in N], *[n["pct_of_needs"] for n in N])
        r = {"base_comments": E["questions"]["q9"]["need_items"], "values": [{"value": n["need"], "label": n["need"], "n": n["n"], "pct_of_base": n["pct_of_needs"]} for n in N[:6]]}
        txt = f"Across {r['base_comments']:,} comments where a need was recorded, the most repeated are: " + ", ".join(f"{v['label'].lower()} ({v['n']:,})" for v in r["values"][:3]) + "."
        return txt, r, D.quotes(f, led, 3), "Unmet needs"
    if re.search(r"(over time|trend|change(d)? (between|over|since)|by year|20(1|2)\d)", s):
        t = [y for y in D.trend(f, led)["years"] if y["year"] >= 2022]
        txt = "Share of relevant comments matching your question, by year: " + "; ".join(f"{y['year']}: {y['matching']:,} of {y['all_relevant']:,} ({y['pct']}%)" for y in t) + ". Years with few comments are noisy."
        r = {"base_comments": sum(y["matching"] for y in t), "values": [{"value": str(y["year"]), "label": str(y["year"]), "n": y["matching"], "pct_of_base": y["pct"]} for y in t]}
        return txt, r, D.quotes(f, led, 2), "Matches by year"
    if len(f.get("income", [])) > 1:
        parts = []
        for v in f["income"]:
            g = dict(f, income=[v])
            r = D.breakdown("driver_any" if field == "event_any" else field, g, led, 4)
            r["values"] = [x for x in r["values"] if x["value"] not in ("other", "habit_or_automation_positive")]
            parts.append((v, r))
        txt = ". ".join(f"{D.lab(v)} ({r['base_comments']:,} comments): " + (", ".join(f"{x['label'].lower()} ({x['pct_of_base']}%)" for x in r["values"][:2]) or "no clear pattern") for v, r in parts)
        return txt + ". Segment cuts are small, so treat differences as directional.", parts[0][1], D.quotes(f, led, 2), D.lab(parts[0][0])
    r = D.breakdown(field, f, led, 6)
    if field == "driver_any":
        r["values"] = [v for v in r["values"] if v["value"] not in ("other", "habit_or_automation_positive")]
    if not r["values"]:
        return "I couldn't find comments matching that question. Try asking about reasons for stopping, payment failures, what people check, or where they go for help.", None, [], title
    top = ", ".join(f"{v['label'].lower()} ({v['n']:,}, {v['pct_of_base']}%)" for v in r["values"][:3])
    small = ", which is a small sample" if r["small_sample"] else ""
    return (f"I counted {r['base_comments']:,} comments that match your question{small}. The most common: {top}. "
            "These are AI tags on public comments, so treat them as directional."), r, D.quotes(f, led, 3), title


def _result(route_name, text, checks, **kw):
    out = {"route": route_name, "text": text, "checks": checks, "breakdown": None, "quotes": None, "title": None, "reframe": None,
           "suggest": False, "issues": None, "model": None}
    out.update(kw)
    return out


def answer(q, history=None, use_ai=True):
    """Run one message through the full pipeline. Returns a dict with route, text, checks and evidence."""
    inp = G.check_input(q)
    v = inp["verdict"]
    if v != "ok":
        rt = {"abuse": "block_abuse", "pii": "block_pii", "injection": "block_injection", "advice": "decline_advice",
              "off_topic": "decline_offtopic", "too_long": "too_long", "empty": "empty"}[v]
        txt = REPLIES[v].format(kind=inp.get("kind", "detail")) if v == "pii" else REPLIES[v]
        return _result(rt, txt, [(f"Input check: {inp['reason'].lower()}", False), ("No AI call made", None)],
                       reframe=reframe_for(q) if v == "advice" else None, suggest=v == "off_topic")
    if use_ai and llm.api_key():
        try:
            return _ai_answer(q, history or [])
        except llm.QuotaExhausted:
            pass
    return _basic(q)


def _basic(q):
    if GREET.search(q.strip()):
        return _result("greeting", greeting(), [("Input check passed", True), ("Greeting", True)])
    if FIRST_PERSON.search(q) and DECISION.search(q) and not THIRD.search(q):
        return _result("decline_advice", REPLIES["advice"], [("Input check passed", True), ("Basic mode: personal money decision, treated as advice", False), ("Not answered", None)],
                       reframe=reframe_for(q))
    if not TOPIC.search(q):
        return _result("decline_offtopic", REPLIES["off_topic"], [("Input check passed", True), ("Off-topic (keyword check)", False)], suggest=True)
    led = D.Ledger()
    txt, r, qs, title = basic_answer(q, led)
    oc = G.check_output(txt, led.nums)
    g = oc["grounded"]
    return _result("answer", txt, [("Input check passed", True), ("Counted data only (basic mode)", None),
                                   (f"Numbers traced: {g['traced']} of {g['total']}", g["traced"] == g["total"]),
                                   ("Output guardrails passed" if oc["pass"] else "Output guardrail: " + oc["issues"][0], oc["pass"])],
                   breakdown=r, quotes=qs, title=title)


def _ai_answer(q, history):
    it, m1 = llm.json_call(INTENT_PROMPT.format(q=q[:800]), INTENT_SCHEMA)
    intent = it.get("intent", "research")
    base = [("Input check passed", True)]
    if intent == "abusive":
        return _result("block_abuse", REPLIES["abuse"], base + [("Intent check: abusive", False)], model=m1)
    if intent == "advice":
        return _result("decline_advice", REPLIES["advice"], base + [("Intent check: asks for advice", False), ("Not answered", None)],
                       reframe=it.get("reframe") or reframe_for(q), model=m1)
    if intent == "off_topic":
        return _result("decline_offtopic", REPLIES["off_topic"], base + [("Intent check: off-topic", False)], suggest=True, model=m1)
    if intent == "account_help":
        return _result("account_help", REPLIES["account_help"], base + [("Intent check: own account", False)],
                       reframe=it.get("reframe") or reframe_for(q), model=m1)
    if intent == "greeting":
        return _result("greeting", greeting(), base + [("Intent check: greeting", True)], model=m1)
    led = D.Ledger()
    turns = []
    for h in history[-4:]:
        turns += [{"role": "user", "text": "Earlier question: " + h["q"]}, {"role": "model", "text": h["a"]}]
    turns.append({"role": "user", "text": "Question: " + q})
    text, m2 = llm.tool_chat(ANSWER_RULES, turns, TOOLS, _executors(led))
    oc = G.check_output(text, led.nums)
    if not led.trace and oc["grounded"]["total"] > 0:
        oc["pass"] = False
        oc["issues"].insert(0, "gave numbers without counting")
    g = oc["grounded"]
    checks = base + [("Intent check: research question", True), (f"Counted with {len(led.trace)} tool call{'s' if len(led.trace) != 1 else ''}", len(led.trace) > 0),
                     (f"Numbers traced: {g['traced']} of {g['total']}", g["traced"] == g["total"]),
                     ("Output guardrails passed" if oc["pass"] else "Output guardrail: " + oc["issues"][0], oc["pass"])]
    if not text:
        return _result("blocked_output", "I couldn't produce an answer for that. Try rephrasing, or ask about a specific behaviour, app or source.", checks, model=m2)
    if not oc["pass"]:
        return _result("blocked_output", f"I held this answer back because it failed a quality check ({'; '.join(oc['issues'])}). Here is the counted data instead.",
                       checks, breakdown=led.last_break, quotes=led.last_quotes, title="Counted breakdown", issues=oc["issues"], model=m2, model_text=text)
    return _result("answer", text, checks, breakdown=led.last_break, quotes=led.last_quotes, title="Counted breakdown behind this answer", model=m2)
