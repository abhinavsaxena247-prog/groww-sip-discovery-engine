"""Corpus loading and the counting tools the chat uses. Every number the engine states comes from here."""
import json
import os
from functools import lru_cache

from engine import guard as G

DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

SRC = {"play_store": "Play Store", "app_store": "App Store", "reddit": "Reddit", "youtube": "YouTube",
       "tradingqna": "TradingQnA", "zerodha_varsity": "Zerodha Varsity", "team_bhp": "Team-BHP"}
SRC_ORDER = ["play_store", "app_store", "reddit", "youtube", "tradingqna", "zerodha_varsity", "team_bhp"]
L = {
    "app_friction_or_bug": "App bug or friction", "trust_or_support_failure": "Trust or support failure",
    "payment_mandate_failure": "Payment, mandate or autopay failure", "returns_below_expectation": "Returns below expectation",
    "negative_or_volatile_returns": "Negative or volatile returns", "missing_control_pause_skip_modify": "No way to pause, skip or change",
    "fees_or_hidden_charges": "Fees or hidden charges", "goal_clarity_or_tracking": "Goal clarity or tracking",
    "cashflow_or_income_change": "Cash-flow or income change", "emergency_or_goal_need_for_money": "Needed the money",
    "advice_from_others_or_media": "Advice from others or media", "confusing_numbers_or_terms": "Confusing numbers or terms",
    "habit_or_automation_positive": "Habit or automation (keeps them going)", "other": "Other",
    "returns_pl": "Returns, profit or loss", "portfolio_value": "Portfolio value", "instalment_status": "Whether the instalment went through",
    "nav": "NAV", "xirr": "XIRR", "fund_rank_or_category": "Fund rank or category",
    "customer_support": "Contact customer support", "amc_or_cams_kfintech": "Check AMC, CAMS or KFintech",
    "youtube_social": "YouTube or social media", "other_app_or_tracker": "Another app or tracker", "forum_reddit": "Forums or Reddit",
    "advisor": "An advisor", "bank_statement": "Bank statement", "asked_friend_family": "Friends or family",
    "started": "Started", "continued": "Continued", "checked_tracked": "Checked or tracked", "skipped": "Skipped", "paused": "Paused",
    "reduced": "Reduced", "increased_stepup": "Increased or stepped up", "stopped_cancelled": "Stopped or cancelled",
    "lapsed_failed_payment": "Payment failed or lapsed", "redeemed_withdrew": "Redeemed or withdrew", "switched_platform": "Switched platform",
    "voluntary": "Voluntary", "involuntary": "Involuntary", "passive_drift": "Passive drift", "none": "None described",
    "salaried": "Salaried", "student_no_income": "Student or no income", "variable_self_employed": "Variable income",
    "under_25": "Under 25", "25_35": "25 to 35", "over_35": "Over 35", "self": "Self", "friend_family": "Friend or family",
    "social_media": "Social media", "app_nudge": "App nudge", "employer": "Employer",
    "first_instalments_1_3m": "Months 1 to 3", "months_4_12": "Months 4 to 12", "beyond_12m": "After 12 months",
    "starting_setup": "Setting up", "pre_start": "Before starting", "unclear": "Unclear", "yes": "Yes", "no": "No",
}


def lab(k):
    return SRC.get(k) or L.get(k) or k


FIELD_ALIASES = {"source": "source", "app": "app", "first_time": "ft", "stage": "stage", "event_any": "event", "drop": "drop",
                 "driver_any": "driver", "check_any": "check", "outside_any": "outside", "income": "income", "age": "age",
                 "influencer": "influencer"}
MULTI = {"event", "driver", "check", "outside"}
DROP_EVENTS = ["skipped", "paused", "reduced", "stopped_cancelled", "lapsed_failed_payment"]


@lru_cache(maxsize=1)
def corpus():
    with open(os.path.join(DATA, "corpus.json"), encoding="utf-8") as f:
        c = json.load(f)
    c["ci"] = {k: i for i, k in enumerate(c["cols"])}
    return c


@lru_cache(maxsize=1)
def engine_data():
    with open(os.path.join(DATA, "engine_data.json"), encoding="utf-8") as f:
        return json.load(f)


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def _matcher(f):
    C = corpus()
    ci, d = C["ci"], C["dict"]
    f = f or {}
    tests = []
    for k, col in FIELD_ALIASES.items():
        v = f.get(k)
        if v is None or v == "" or v == []:
            continue
        if k == "first_time":
            want = 0 if v in (True, "yes", "true") else 1 if v in (False, "no", "false") else None
            if want is not None:
                tests.append(lambda r, w=want: r[ci["ft"]] == w)
            continue
        vals = v if isinstance(v, list) else [v]
        ids = []
        for x in vals:
            s = str(x)
            if s in d[col]:
                ids.append(d[col].index(s))
            elif col == "app":
                for i, a in enumerate(d[col]):
                    if a.lower() == s.lower():
                        ids.append(i)
        if not ids:
            tests.append(lambda r: False)
            continue
        if col in MULTI:
            m = 0
            for i in ids:
                m |= 1 << i
            tests.append(lambda r, m=m, j=ci[col]: (r[j] & m) != 0)
        else:
            tests.append(lambda r, ids=tuple(ids), j=ci[col]: r[j] in ids)
    if f.get("dropoff_only"):
        ev = d["event"]
        m = 0
        for x in DROP_EVENTS:
            m |= 1 << ev.index(x)
        ds = tuple(d["drop"].index(x) for x in ("voluntary", "involuntary", "passive_drift"))
        tests.append(lambda r, m=m: (r[ci["event"]] & m) != 0 or r[ci["drop"]] in ds)
    if f.get("year_min"):
        tests.append(lambda r, y=int(f["year_min"]): r[ci["year"]] >= y)
    if f.get("year_max"):
        tests.append(lambda r, y=int(f["year_max"]): r[ci["year"]] and r[ci["year"]] <= y)
    if f.get("min_severity"):
        tests.append(lambda r, s=int(f["min_severity"]): r[ci["sev"]] >= s)
    if f.get("keyword"):
        kws = [k.strip().lower() for k in str(f["keyword"]).split("|") if k.strip()]
        tests.append(lambda r: any(k in (r[ci["evidence"]] + " " + r[ci["need"]]).lower() for k in kws))
    return lambda r: all(t(r) for t in tests)


class Ledger:
    """Collects every number the tools return, so the answer's numbers can be traced."""
    def __init__(self):
        self.nums, self.trace, self.last_break, self.last_quotes = [], [], None, None

    def note(self, *xs):
        for x in xs:
            if isinstance(x, (int, float)) and x == x:
                self.nums.append(float(x))


def count(f, led):
    C = corpus()
    m = _matcher(f)
    n = sum(1 for r in C["rows"] if m(r))
    tot = len(C["rows"])
    p = round(100 * n / tot, 1)
    led.note(n, tot, p)
    led.trace.append(f"Counted {n:,} matching comments")
    return {"matching_comments": n, "total_relevant": tot, "share_pct": p}


def breakdown(field, f, led, top=8):
    C = corpus()
    col = FIELD_ALIASES.get(field, field)
    if col not in C["ci"] or col not in C["dict"]:
        raise ValueError("Unknown field " + str(field) + ". Use one of: " + ", ".join(FIELD_ALIASES))
    j, vals = C["ci"][col], C["dict"][col]
    m = _matcher(f)
    rows = [r for r in C["rows"] if m(r)]
    cnt = {}
    for r in rows:
        if col in MULTI:
            for i, v in enumerate(vals):
                if r[j] & (1 << i):
                    cnt[v] = cnt.get(v, 0) + 1
        else:
            v = vals[r[j]] if 0 <= r[j] < len(vals) else None
            if v not in (None, "", "unclear", "forum", "youtube"):
                cnt[v] = cnt.get(v, 0) + 1
    base = len(rows)
    out = [{"value": v, "label": lab(v), "n": n, "pct_of_base": round(100 * n / max(base, 1), 1)}
           for v, n in sorted(cnt.items(), key=lambda kv: -kv[1])[: min(15, int(top or 8))]]
    led.note(base, *[x["n"] for x in out], *[x["pct_of_base"] for x in out])
    res = {"base_comments": base, "small_sample": base < 30, "values": out}
    led.trace.append(f"Broke down {lab(col).lower()} across {base:,} comments")
    led.last_break = res
    return res


def compare(field, a, b, led, la="group_a", lb="group_b"):
    r = {la or "group_a": breakdown(field, a, led), lb or "group_b": breakdown(field, b, led)}
    led.trace.append("Compared two groups")
    return r


def trend(f, led):
    C = corpus()
    yi = C["ci"]["year"]
    m = _matcher(f)
    allc, hit = {}, {}
    for r in C["rows"]:
        y = r[yi]
        if not y or y < 2018:
            continue
        allc[y] = allc.get(y, 0) + 1
        if m(r):
            hit[y] = hit.get(y, 0) + 1
    years = [{"year": y, "matching": hit.get(y, 0), "all_relevant": allc[y], "pct": round(100 * hit.get(y, 0) / allc[y], 1)} for y in sorted(allc)]
    for y in years:
        led.note(y["matching"], y["all_relevant"], y["pct"])
    led.trace.append("Counted matches by year")
    return {"years": years}


def quotes(f, led, limit=4):
    C = corpus()
    ci, d = C["ci"], C["dict"]
    m = _matcher(f)

    def ok(r):
        e = r[ci["evidence"]]
        return (e and len(e.split()) >= 6 and not G.FUNDS.search(e) and not G.ADVICE_OUT.search(e)
                and not G.URGENCY.search(e) and G.check_input(e)["verdict"] not in ("abuse", "pii"))
    rows = sorted((r for r in C["rows"] if m(r) and ok(r)), key=lambda r: -r[ci["sev"]])
    k = max(1, min(6, int(limit or 4)))
    step = max(1, len(rows) // k)
    pick = rows[::step][:k]
    for r in pick:
        led.note(r[ci["year"]], *G.numbers_in(r[ci["evidence"]]))
    out = [{"source": SRC[d["source"][r[ci["source"]]]],
            "app": "" if d["app"][r[ci["app"]]] in ("forum", "youtube", "") else d["app"][r[ci["app"]]],
            "year": r[ci["year"]] or None, "quote": r[ci["evidence"]], "url": r[ci["url"]]} for r in pick]
    led.trace.append(f"Pulled {len(out)} quotes")
    led.last_quotes = out
    return out
