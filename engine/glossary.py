"""Plain definitions of basic SIP and mutual fund terms, so "what is a SIP?" gets a direct answer.
Definitions are general education only: no fund names, no recommendation, no advice.
Each entry also links the term to a counted fact from the research data."""
import re

from engine import data as D

# key: (synonyms, definition, data filter, what the counted comments describe, follow-up research question)
TERMS = {
    "sip": (["sip", "sips", "systematic investment plan", "systematic investment plans", "sip investment", "sip in mutual fund", "sip in mutual funds"],
            "A SIP (Systematic Investment Plan) is a way of investing a fixed amount in a mutual fund at regular intervals, usually monthly. "
            "The amount is debited automatically from your bank account, and each installment buys fund units at that day's price (NAV).",
            {"dropoff_only": True}, "describe a SIP being skipped, paused, stopped or lapsing",
            "Why do first-time investors stop their SIPs?"),
    "mutual_fund": (["mutual fund", "mutual funds", "mf", "mfs"],
            "A mutual fund pools money from many investors and invests it in stocks, bonds or other assets. It is run by an asset management "
            "company (AMC) and regulated by SEBI. Each investor holds units whose value moves with the value of the fund's holdings.",
            {"first_time": True}, "come from people who say they are first-time or new investors",
            "What do first-time investors say worries them?"),
    "nav": (["nav", "net asset value"],
            "NAV (Net Asset Value) is the price of one unit of a mutual fund. It is calculated at the end of each business day from the value "
            "of everything the fund holds, minus its expenses.",
            {"check_any": ["nav"]}, "mention checking the NAV",
            "What do new investors check after starting?"),
    "xirr": (["xirr"],
             "XIRR is a yearly return figure that accounts for money going in on different dates. Apps show it for SIPs because each "
             "installment is invested at a different time, so a simple percentage gain can mislead.",
             {"check_any": ["xirr"]}, "mention checking XIRR",
             "Do investors find numbers like XIRR confusing?"),
    "cagr": (["cagr", "compound annual growth rate"],
             "CAGR (compound annual growth rate) is the average yearly growth of a single investment over a period. For SIPs, where money "
             "goes in at different times, XIRR is used instead.",
             {"check_any": ["returns_pl"]}, "mention checking returns or profit and loss",
             "What did investors expect from returns, and what did they describe happening?"),
    "mandate": (["mandate", "mandates", "e-mandate", "emandate", "e mandate", "autopay", "auto pay", "auto-pay", "upi autopay", "nach", "auto debit", "autodebit", "autopay mandate", "upi autopay mandate", "sip mandate", "e-mandate for sip", "nach mandate"],
                "A mandate (e-mandate, NACH or UPI AutoPay) is the standing permission you give your bank so the SIP amount can be debited "
                "automatically on the due date. If the mandate is not approved, or the account lacks funds on that day, the installment fails.",
                {"driver_any": ["payment_mandate_failure"]}, "describe a payment, mandate or autopay failure",
                "What goes wrong when Groww SIP payments fail?"),
    "step_up": (["step up", "step-up", "stepup", "step up sip", "step-up sip", "top up sip", "top-up sip", "topup sip"],
                "A step-up (or top-up) SIP raises the installment automatically at set intervals, for example by a fixed percentage each year.",
                {"event_any": ["increased_stepup"]}, "describe increasing a SIP or using a step-up",
                "What makes investors increase their SIP?"),
    "pause": (["pause sip", "sip pause", "skip sip", "sip skip", "pausing a sip", "skipping a sip", "pause", "skip"],
              "Many platforms let investors pause or skip SIP installments for a period without cancelling the SIP. The options and limits "
              "differ by app and fund house.",
              {"driver_any": ["missing_control_pause_skip_modify"]}, "describe wanting a pause, skip or change option they could not find",
              "Do people ask to pause instead of cancel?"),
    "lapse": (["sip lapse", "lapsed sip", "lapse", "missed installment", "missed instalment", "failed installment", "failed instalment", "sip failure", "failed sip"],
              "An installment fails or is missed when the debit does not go through, usually because of low balance or a mandate problem. "
              "If several installments in a row fail, the fund house may cancel the SIP; the exact rule varies.",
              {"drop": ["involuntary"]}, "describe a SIP stopping without the investor choosing to",
              "Why do SIPs lapse without the investor deciding?"),
    "lumpsum": (["lumpsum", "lump sum", "lump-sum"],
                "A lumpsum is a one-time investment of a larger amount, as opposed to a SIP's regular installments.",
                {"keyword": "lumpsum|lump sum"}, "mention a lumpsum",
                "How do investors describe changes in their income affecting their SIP?"),
    "redemption": (["redemption", "redeem", "redeeming", "withdrawal", "withdraw"],
                   "Redemption means selling mutual fund units to get money back. The amount is credited to your bank account, usually "
                   "within a few working days.",
                   {"event_any": ["redeemed_withdrew"]}, "describe redeeming or withdrawing",
                   "Why do investors redeem or withdraw?"),
    "exit_load": (["exit load"],
                  "An exit load is a fee some funds charge if units are sold before a set period, often one year. It is a percentage of "
                  "the amount redeemed.",
                  {"driver_any": ["fees_or_hidden_charges"]}, "mention fees or hidden charges",
                  "What do investors say about fees and charges?"),
    "expense_ratio": (["expense ratio", "ter", "total expense ratio"],
                      "The expense ratio is the yearly fee a fund charges to manage the money, shown as a percentage of assets. It is "
                      "taken out of the fund's value, so it is already reflected in the NAV.",
                      {"driver_any": ["fees_or_hidden_charges"]}, "mention fees or hidden charges",
                      "What do investors say about fees and charges?"),
    "kyc": (["kyc", "know your customer", "ekyc", "e-kyc"],
            "KYC (Know Your Customer) is the identity check every investor completes once before investing in mutual funds in India.",
            {"stage": ["starting_setup"]}, "are about the setup stage, before or while starting a SIP",
            "What goes wrong for investors while setting up their first SIP?"),
    "direct_regular": (["direct plan", "regular plan", "direct vs regular", "direct and regular plan", "direct and regular plans", "direct fund", "regular fund"],
                       "A direct plan is bought straight from the fund house with no distributor commission, so its expense ratio is lower. "
                       "A regular plan includes a distributor commission. Both invest in the same portfolio.",
                       {"driver_any": ["fees_or_hidden_charges"]}, "mention fees or hidden charges",
                       "What do investors say about fees and charges?"),
    "elss": (["elss", "tax saving fund", "tax saver fund", "tax saving mutual fund"],
             "ELSS (Equity Linked Savings Scheme) is a type of equity mutual fund with a three-year lock-in. Investments in it can be claimed "
             "as a deduction under Section 80C in the old tax regime.",
             {"keyword": "elss|tax sav|80c"}, "mention ELSS or tax saving",
             "Why do first-time investors start a SIP?"),
    "groww": (["groww", "groww app"],
              "Groww is an Indian investing app for mutual funds, stocks and other products. This engine is an independent student project, "
              "not affiliated with Groww, and studies public comments about Groww and nine other apps.",
              {"app": ["Groww"]}, "are store reviews of the Groww app",
              "What problems do investors describe most often on each app?"),
    "amc": (["amc", "asset management company", "fund house"],
            "An AMC (asset management company), or fund house, is the company that runs mutual fund schemes and invests the pooled money.",
            {"outside_any": ["amc_or_cams_kfintech"]}, "describe going to the fund house or its registrar (CAMS, KFintech)",
            "Where do investors go when they are unsure?"),
}

_SYN = {}
for k, (syns, *_rest) in TERMS.items():
    for s in syns:
        _SYN[s] = k
_ALT = "|".join(sorted((re.escape(s) for s in _SYN), key=len, reverse=True))
_FILL = r"(?:\s+(?:in|of|for)\s+(?:a\s+)?(?:mutual\s+funds?|mfs?|investing|investment|groww|sips?))?(?:\s+and\s+how\s+(?:does\s+)?(?:it|they)\s+works?)?"
PATTERNS = [
    re.compile(rf"^(?:what\s*(?:'s|is|are|r)|whats|wht\s+is|define|definition\s+of|meaning\s+of|explain|tell\s+me\s+about|what\s+do\s+you\s+mean\s+by)\s+(?:an?\s+|the\s+)?(?:term\s+)?(?P<t>{_ALT}){_FILL}$"),
    re.compile(rf"^what\s+(?:does|do)\s+(?:an?\s+|the\s+)?(?P<t>{_ALT})\s+(?:mean|stand\s+for){_FILL}$"),
    re.compile(rf"^how\s+(?:does|do)\s+(?:an?\s+|the\s+)?(?P<t>{_ALT})\s+work{_FILL}$"),
    re.compile(rf"^(?P<t>{_ALT}){_FILL}\s+(?:kya|kia)\s+(?:hai|hota\s+hai|hoti\s+hai|hote\s+hain|hain|h)$"),
    re.compile(rf"^(?P<t>{_ALT}){_FILL}\s+(?:ka\s+)?(?:matlab|meaning)(?:\s+kya\s+hai)?$"),
    re.compile(rf"^(?P<t>{_ALT})\s*(?:meaning|definition)?$"),
]
FINANCE = re.compile(r"(fund|sip|demat|index|equity|debt|stock|share|bond|etf|nps|ppf|\bfd\b|fixed deposit|tax|insurance|account|loan|gold|invest|portfolio|dividend|nifty|sensex|sebi|amfi|folio|units?\b|nav|return|interest|broker|trading|market|ipo|smallcase|crypto|rd\b|annuit)", re.I)
CONCEPT_OPENER = re.compile(r"^(?:what\s*(?:'s|is|are)|whats|define|meaning\s+of|explain|what\s+does\s+\S+(?:\s+\S+)?\s+mean)\b|\b(?:kya\s+(?:hai|hota\s+hai)|matlab)\s*$")


def _norm(q):
    s = q.lower().strip().replace("instalment", "installment")
    s = re.sub(r"[?!.。,;:\"“”]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def match(q):
    """Return the glossary key if the whole question is 'what is <term>' (or a Hinglish form), else None."""
    s = _norm(q)
    if len(s.split()) > 12:
        return None
    for p in PATTERNS:
        m = p.match(s)
        if m:
            return _SYN[m.group("t")]
    return None


PAIR = [re.compile(rf"^(?:what\s+is\s+(?:the\s+)?)?difference\s+between\s+(?:an?\s+|the\s+)?(?P<a>{_ALT})\s+(?:and|&|vs|versus)\s+(?:an?\s+|the\s+)?(?P<b>{_ALT})$"),
        re.compile(rf"^(?P<a>{_ALT})\s+(?:vs|versus|or|and)\s+(?P<b>{_ALT})(?:\s+(?:difference|kya\s+fark\s+hai|fark))?$")]


def match_pair(q):
    s = _norm(q)
    for p in PAIR:
        m = p.match(s)
        if m:
            return _SYN[m.group("a")], _SYN[m.group("b")]
    return None


def answer(key, led):
    syns, definition, flt, phrase, follow = TERMS[key]
    from engine import guard as G
    led.note(*G.numbers_in(definition))
    c = D.count(flt, led)
    fact = (f"In this engine's data, {c['matching_comments']:,} of {c['total_relevant']:,} relevant public comments ({c['share_pct']}%) {phrase}."
            if c["matching_comments"] else "")
    text = f"{definition} This is a general definition, not advice. {fact}".strip()
    return text, follow
