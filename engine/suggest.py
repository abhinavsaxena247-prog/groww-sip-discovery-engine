"""Suggested questions that follow what the person just asked, plus questions other visitors asked recently.
Follow-ups are built from what the question was about (topic, app, source, theme, segment), so they change with every answer."""
import random
import threading

from engine import pipeline as P

POOL = [  # first-screen starters: a varied mix, reshuffled per visit
    "Why do first-time investors stop their SIPs?", "What goes wrong when Groww SIP payments fail?",
    "What is the minimum amount to start a SIP?", "What happens if I miss a SIP installment?",
    "What is the biggest opportunity?", "log SIP kyun band karte hain?",
    "Do people ask to pause instead of cancel?", "How do Reddit and Play Store differ on why people stop?",
    "What do new investors check after starting?", "Is the autopay problem specific to Groww or common across apps?",
    "What unmet needs come up most often?", "How was insight quality validated?",
    "Can I stop my SIP anytime?", "How do salaried and self-employed investors differ?",
]

TOPIC_NEXT = {
    "min_amount": ["What happens if I miss a SIP installment?", "Can I pause my SIP?", "What do first-time investors say about starting small?"],
    "sip_vs_lumpsum": ["What is rupee cost averaging?", "Are SIP returns guaranteed?", "Why do first-time investors start a SIP?"],
    "missed_instalment": ["What goes wrong when Groww SIP payments fail?", "How many drop-offs are involuntary?", "Is the autopay problem specific to Groww or common across apps?"],
    "pause_skip": ["Do people ask to pause instead of cancel?", "What happens if I miss a SIP installment?", "Can I stop my SIP anytime?"],
    "stop_sip": ["Why do first-time investors stop their SIPs?", "What happens to my money if I stop the SIP?", "Can I pause my SIP?"],
    "mandate": ["What goes wrong when Groww SIP payments fail?", "How long does mandate approval take?", "What happens if I miss a SIP installment?"],
    "mandate_time": ["What goes wrong when Groww SIP payments fail?", "What happens if I miss a SIP installment?", "How many drop-offs are involuntary?"],
    "tax": ["What is exit load?", "How do I withdraw money from my SIP?", "What is the lock-in for ELSS?"],
    "q1": ["What do new investors check after starting?", "What changes in their behaviour in the months after starting?", "Why do first-time investors stop their SIPs?"],
    "q2": ["What leads investors to pause, reduce or stop a SIP?", "What separates investors who continue from those who drop off?", "How many drop-offs are involuntary?"],
    "q3": ["How many drop-offs are involuntary?", "What is the biggest opportunity?", "Do people ask to pause instead of cancel?"],
    "q4": ["Do investors find numbers like XIRR confusing?", "What confuses or worries them inside the app?", "Where do investors go when they are unsure?"],
    "q5": ["Where do investors go when they are unsure?", "What unmet needs come up most often?", "What do people say about Groww customer support?"],
    "q6": ["What confuses or worries them inside the app?", "What do YouTube comments say about stopping SIPs?", "What unmet needs come up most often?"],
    "q7": ["What leads investors to pause, reduce or stop a SIP?", "How do patterns differ across segments?", "What makes investors increase their SIP?"],
    "q8": ["Why do salaried investors pause their SIPs?", "Do students behave differently from salaried investors?", "Who influences first-time investors to start?"],
    "q9": ["What is the biggest opportunity?", "Do people ask to pause instead of cancel?", "What goes wrong when Groww SIP payments fail?"],
    "top_opportunity": ["How were the opportunities scored?", "Is the autopay problem specific to Groww or common across apps?", "How many drop-offs are involuntary?"],
    "opportunities": ["What is the biggest opportunity?", "How were the opportunities scored?", "What are the limitations of this data?"],
    "scoring": ["What is the biggest opportunity?", "What are the limitations of this data?", "How was insight quality validated?"],
    "validation": ["What are the limitations of this data?", "How did you evaluate the engine?", "What guardrails does this engine have?"],
    "drop_types": ["What goes wrong when Groww SIP payments fail?", "Is the autopay problem specific to Groww or common across apps?", "What is the biggest opportunity?"],
}
DRIVER_TXT = {"payment_mandate_failure": "failed payments or mandates", "missing_control_pause_skip_modify": "missing pause or skip options",
              "cashflow_or_income_change": "money pressure", "trust_or_support_failure": "support problems", "fees_or_hidden_charges": "fees",
              "confusing_numbers_or_terms": "confusing numbers", "negative_or_volatile_returns": "falling returns", "returns_below_expectation": "returns below expectation"}
SRC_TXT = {"reddit": "Reddit", "play_store": "Play Store reviews", "app_store": "App Store reviews", "youtube": "YouTube comments", "tradingqna": "TradingQnA"}


def starters(seed, n=6):
    rnd = random.Random(seed)
    return rnd.sample(POOL, n)


def follow_ups(q, out, asked, n=3):
    """Up to n questions that build on the last question and answer."""
    cands = []
    t = (out or {}).get("topic")
    if t and t in TOPIC_NEXT:
        cands += TOPIC_NEXT[t]
    if (out or {}).get("route") in ("answer", "blocked_output") or not cands:
        f, _, _ = P.route(q)
        app = (f.get("app") or [None])[0]
        drv = (f.get("driver_any") or [None])[0]
        src = (f.get("source") or [None])[0]
        theme = DRIVER_TXT.get(drv, "stopping SIPs")
        if app:
            a = app.title() if app.islower() else app
            cands += [f"Are complaints about {theme} specific to {a} or common across apps?", f"What do first-time investors on {a} say about {theme}?"]
        if drv:
            cands += [f"Are complaints about {theme} more common among first-time investors?", f"How have complaints about {theme} changed over time?",
                      f"Show me quotes about {theme}"]
        if src and src in SRC_TXT:
            other = "Play Store reviews" if src != "play_store" else "Reddit"
            cands += [f"How do {SRC_TXT[src]} and {other} differ on {theme}?"]
        if f.get("first_time"):
            cands += [f"How do experienced investors differ on {theme}?"]
        else:
            cands += [f"What do first-time investors say about {theme}?"]
        if f.get("dropoff_only"):
            cands += ["How many drop-offs are involuntary?"]
    cands += ["What is the biggest opportunity?", "What unmet needs come up most often?"]
    import re as _re
    kinds = [r"specific to|common across|other apps", r"first[- ]time", r"over time|changed", r"quotes?\b"]
    same = [k for k in kinds if _re.search(k, q, _re.I)]          # don't re-suggest the same kind of question in other words
    seen, res = {a.strip().lower() for a in asked}, []
    for c in cands:
        if c.strip().lower() in seen or c in res or any(_re.search(k, c, _re.I) for k in same):
            continue
        if _answerable(c):                 # never suggest a question that would come back empty
            res.append(c)
        if len(res) == n:
            break
    return res


_OK = {}


def _answerable(q):
    if q not in _OK:
        o = P.answer(q, use_ai=False)
        _OK[q] = o["route"] in ("answer", "basics", "research") and "couldn't find" not in o["text"]
    return _OK[q]


# ---- questions other visitors asked recently (kept in memory only, never on disk) ----
_LOCK = threading.Lock()
_ASKED = {}


def record(q, route):
    """Remember a question only if it passed every check and was answered (never blocked, declined or personal)."""
    if route not in ("answer", "basics", "research") or len(q) > 120:
        return
    k = " ".join(q.strip().split())
    if not k:
        return
    k = k[0].upper() + k[1:]
    with _LOCK:
        _ASKED[k] = _ASKED.get(k, 0) + 1


def popular(exclude, n=4):
    ex = {e.strip().lower() for e in exclude}
    with _LOCK:
        items = sorted(_ASKED.items(), key=lambda kv: -kv[1])
    return [k for k, _ in items if k.lower() not in ex][:n]
