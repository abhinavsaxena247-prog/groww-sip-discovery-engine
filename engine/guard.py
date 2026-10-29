"""Deterministic guardrails for the NL-Groww Discovery Engine.
Runs before and after every AI call. Pure functions, no network.
Ported from the browser version; tested by evals/run_evals.py."""
import re

LEET = {"0": "o", "1": "i", "!": "i", "3": "e", "4": "a", "@": "a", "5": "s", "$": "s", "7": "t", "8": "b"}


def norm(s):
    t = str(s or "").lower()
    t = re.sub(r"[0134578@$!]", lambda m: LEET.get(m.group(0), m.group(0)), t)
    t = re.sub(r"(\w)[*.\-_~]+(?=\w)", r"\1", t)   # f*ck, f.u.c.k
    t = re.sub(r"(\w)\1{2,}", r"\1\1", t)         # fuuuuck -> fuuck
    return t


def squash(t):
    """Join spaced-out letters: 'f u c k' -> 'fuck'."""
    return re.sub(r"\b(?:\w\s+){2,}\w\b", lambda m: re.sub(r"\s+", "", m.group(0)), t)


# Abusive terms: English, Hinglish (romanised) and Devanagari. Whole-word or compound matches only,
# chosen to avoid everyday words ("chhod do" = "leave it", "class", "assets", "bc" = "because").
ABUSE = [
    re.compile('\\bf+u+c*k+\\w*'),
    re.compile('\\bfck\\w*'),
    re.compile('\\bf+k\\s?(off|u|you)\\b'),
    re.compile('\\bmotherf\\w*'),
    re.compile('\\bmofo\\b'),
    re.compile('\\bsh[i1]t+(ty|head)?\\b'),
    re.compile('\\bbull\\s?sh[i1]t\\b'),
    re.compile('\\bbitch\\w*'),
    re.compile('\\bbastard\\w*'),
    re.compile('\\basshole\\w*'),
    re.compile('\\bass\\s?hole\\b'),
    re.compile('\\bdickhead\\b'),
    re.compile('\\bcunt\\w*'),
    re.compile('\\bwhore\\w*'),
    re.compile('\\bslut\\w*'),
    re.compile('\\bretard\\w*'),
    re.compile('\\bstfu\\b'),
    re.compile('\\bwtf\\b'),
    re.compile('\\bscum(bag)?\\b'),
    re.compile('\\bidiot\\w*'),
    re.compile('\\bmoron\\w*'),
    re.compile('\\bstupid (bot|ai|engine|app|bitch)\\b'),
    re.compile('\\bkill yourself\\b'),
    re.compile('\\bkys\\b'),
    re.compile('\\bmadar\\s?ch[o0]+d\\w*'),
    re.compile('\\bmaa?d[ae]rch[o0]+d\\w*'),
    re.compile('\\bm[ae]+\\s?ki\\s?ch[uo]+t\\w*'),
    re.compile('\\bbh[ae]+n\\s?ch[o0]+d\\w*'),
    re.compile('\\bbhench[o0]+d\\w*'),
    re.compile('\\bbehen\\s?ch[o0]+d\\w*'),
    re.compile('\\bbh[ae]+n\\s?k[ie]\\s?(l[ou]n?d|ch[uo]t)\\w*'),
    re.compile('\\bch[uo]+t(i|iy|iya|iye|iyo|iyapa|ye|ya)\\b'),
    re.compile('\\bchutia\\w*'),
    re.compile('\\bchut\\b'),
    re.compile('\\bbh[o0]sd[iae]\\w*'),
    re.compile('\\bbhosda\\w*'),
    re.compile('\\bg[a]+a?nd[u]+\\b'),
    re.compile('\\bgaand\\w*'),
    re.compile('\\bl[a]+v?u?d[ae]\\b'),
    re.compile('\\blau?ra\\b'),
    re.compile('\\blund\\w*'),
    re.compile('\\br[a]+nd[i]+\\w*'),
    re.compile('\\bharam(i|zada|zaade|khor)\\w*'),
    re.compile('\\bkutt[ae] ki (aulad|aulaad)\\b'),
    re.compile('\\bsuar ki\\b'),
    re.compile('^\\s*(bc|mc)\\b'),
    re.compile('\\b(bc|mc)\\b.{0,20}\\b(kya|yaar|ye|yeh|hai|teri|tera|tu|saala|sala|bakwas|bhai)\\b'),
    re.compile('\\bbsdk\\b'),
    re.compile('\\bmkc\\b'),
    re.compile('\\btmkc\\b'),
    re.compile('\\bbkl\\b'),
    re.compile('\\bchod(u|e)\\b'),
    re.compile('\\bsh[i1*#]t\\b'),
    re.compile('\\bf[u*#][c*#]k'),
    re.compile('\\bpiece of sh'),
    re.compile('\\bb[i1*]tch'),
    re.compile('मादरचोद'),
    re.compile('भेनचोद'),
    re.compile('बहनचोद'),
    re.compile('चूतिया'),
    re.compile('चुतिया'),
    re.compile('भोसड'),
    re.compile('गांडू'),
    re.compile('रंडी'),
    re.compile('हरामी'),
    re.compile('लौड़'),
    re.compile('लंड'),
]

PII = [
    ('PAN', re.compile('\\b[a-z]{5}[0-9]{4}[a-z]\\b', re.I)),
    ('Aadhaar', re.compile('\\b[2-9][0-9]{3}[\\s-]?[0-9]{4}[\\s-]?[0-9]{4}\\b')),
    ('card number', re.compile('\\b(?:[0-9][\\s-]?){15,16}\\b')),
    ('IFSC', re.compile('\\b[a-z]{4}0[a-z0-9]{6}\\b', re.I)),
    ('account number', re.compile('\\b(a/?c|acc(ount)?|folio|demat|client id)\\b[^0-9]{0,20}[0-9][0-9\\s-]{7,20}', re.I)),
    ('long number', re.compile('\\b[0-9]{9,18}\\b')),
    ('phone number', re.compile('(\\+91[\\s-]?)?\\b[6-9][0-9]{4}[\\s-]?[0-9]{5}\\b')),
    ('email address', re.compile('\\b[\\w.+-]+@[\\w-]+\\.[\\w.-]+\\b')),
    ('screenshot or statement', re.compile("\\b(here('s| is) my (portfolio|statement|cas)|attached (my )?(portfolio|statement|screenshot))\\b", re.I)),
]

INJECTION = [
    re.compile('ignore (all |any |the )?(previous|prior|above|earlier|your) (instructions|rules|prompt|messages)', re.I),
    re.compile('disregard (the |your |all )?(rules|instructions|guardrails)', re.I),
    re.compile('\\b(system|developer) prompt\\b', re.I),
    re.compile('reveal (your|the) (prompt|instructions|rules)', re.I),
    re.compile('\\byou are now\\b', re.I),
    re.compile('\\bact as (a |an )?(financial|investment) (advisor|adviser|expert)\\b', re.I),
    re.compile('\\bjailbreak\\b', re.I),
    re.compile('\\bDAN\\b'),
    re.compile('\\bdo anything now\\b', re.I),
    re.compile('pretend (you are|to be|there are no)', re.I),
    re.compile('\\bno (rules|restrictions|guardrails)\\b', re.I),
    re.compile('^\\s*(system|admin|developer|assistant)\\s*:', re.I),
    re.compile('\\b(hidden|secret|internal) (rules|instructions|prompt)\\b', re.I),
    re.compile('\\bno restrictions\\b', re.I),
    re.compile('\\boverride\\b.*\\b(rules|safety|guardrail)', re.I),
    re.compile('\\bsudo\\b', re.I),
    re.compile('</?(system|instructions?)>', re.I),
    re.compile('\\bnew instructions\\b', re.I),
    re.compile('forget (everything|your rules|the rules)', re.I),
]

# Investment-advice intent (deterministic backstop; the AI intent check runs too)
ADVICE = [
    re.compile('\\b(which|what|best|top|good|recommend\\w*|suggest\\w*)\\b.{0,40}\\b(fund|funds|scheme|stock|stocks|share|shares|sip|mf|mutual fund|etf|portfolio|nfo|ipo)\\b.{0,40}\\b(buy|invest|choose|pick|start|for me|should|to get|returns?|202\\d|now)\\b', re.I),
    re.compile('\\bshould i\\b.{0,60}\\b(invest|buy|sell|stop|start|continue|pause|cancel|redeem|withdraw|switch|increase|reduce|skip|exit|hold|put)\\b', re.I),
    re.compile('\\b(is|are)\\b.{0,40}\\b(fund|scheme|stock|sip|etf|small ?cap|mid ?cap|large ?cap|index fund)s?\\b.{0,30}\\b(good|safe|worth|better|best|bad|risky)\\b', re.I),
    re.compile('\\b(recommend|suggest)\\w*\\b.{0,25}\\b(me|a|an|some|good|best|any|which)\\b', re.I),
    re.compile('\\bgood time to (start|invest|buy|sell|stop|enter|exit|begin)\\b', re.I),
    re.compile('\\b(right|best|good) time (to|for)\\b.{0,20}\\b(sip|invest|buy|start|stop)', re.I),
    re.compile('\\bshould (i|we|my \\w+|he|she|they|one)\\b.{0,60}\\b(invest|buy|sell|stop|start|continue|pause|cancel|redeem|withdraw|switch|keep|hold|exit|put|move)\\b', re.I),
    re.compile('\\bbest (sip |investment )?(amount|fund|scheme|plan|sip|time|strategy|option|portfolio|allocation)\\b', re.I),
    re.compile('\\b(which|what|best|good|top)\\b.{0,15}\\b(elss|index|flexi ?cap|small ?cap|mid ?cap|large ?cap|debt|liquid|hybrid|gold|silver|international|tax ?saving|nfo)\\b.{0,25}\\b(fund|scheme|etf|option)s?\\b', re.I),
    re.compile('\\b(kis|kaun|konsa|kaunsa|kon ?sa|kaunse|konse)\\b.{0,15}\\b(fund|sip|scheme|stock|share|mf)\\b', re.I),
    re.compile('\\bpaisa\\b.{0,25}\\b(lagana|lagaun|lagau|lagaye|invest)\\b.{0,15}\\b(chahiye|karu|karun|karoon|kare|karna)\\b', re.I),
    re.compile('\\bpredict\\w*\\b.{0,25}\\b(my|returns?|market|nav|nifty|sensex|price|fund|worth)\\b', re.I),
    re.compile('\\bhow much (will|would|can) (my|i|the|this)\\b.{0,30}\\b(be worth|grow|become|get|make|earn|return)\\b', re.I),
    re.compile('\\bworth in \\d+ (years?|months?)\\b', re.I),
    re.compile('\\bwill\\b.{0,40}\\b(give|return|grow|deliver|make)\\b.{0,15}\\d+ ?%', re.I),
    re.compile('\\b(do you think|in your opinion|your (view|opinion)|what do you suggest|help me (choose|pick|decide))\\b', re.I),
    re.compile('\\bhow much (should|must|do) i (invest|put|save)\\b', re.I),
    re.compile('\\b(which|what) (app|platform|broker)\\b.{0,40}\\b(best|better|should|for me|choose|use)\\b', re.I),
    re.compile('\\bis it (bad|good|wise|okay|ok|smart|safe|right|wrong|better|fine) to (stop|start|continue|pause|cancel|skip|redeem|invest|keep|withdraw)', re.I),
    re.compile('\\bwhat returns? (will|would|can) i (get|make|earn)\\b', re.I),
    re.compile('\\b(how much|what) (will|would) (i|my money|my sip) (get|make|grow|earn|become)\\b', re.I),
    re.compile('\\b(will|would) (the )?(market|nifty|sensex|fund|nav|stock)s? (go up|go down|rise|fall|crash|recover)\\b', re.I),
    re.compile('\\b(predict|forecast)\\b.{0,30}\\b(return|market|nav|price|nifty)\\b', re.I),
    re.compile('\\bguaranteed returns?\\b', re.I),
    re.compile('\\b(double|multiply) my money\\b', re.I),
    re.compile('\\b(tell|give) me (a |some )?(tips?|stock tips?|fund names?)\\b', re.I),
    re.compile('\\bkaun ?sa (fund|sip|stock)\\b', re.I),
    re.compile('\\b(sip|fund) (band|bandh) (karu|kar du|karun|karoon|kare)\\b', re.I),
    re.compile('\\b(kahan|kaha|kidhar) (invest|paisa laga)', re.I),
    re.compile('\\bmujhe kya karna chahiye\\b', re.I),
]

OFFTOPIC = [
    re.compile('\\b(weather|cricket|ipl|movie|film|song|lyrics|recipe|cook|poem|joke|story|homework|essay|code|python|javascript|sql query|girlfriend|boyfriend|dating)\\b', re.I),
    re.compile('\\b(bitcoin|crypto|ethereum|forex|f&o|options trading|intraday|lottery|betting|casino)\\b', re.I),
    re.compile('\\b(prime minister|election|politic\\w*|religion)\\b', re.I),
    re.compile('\\b(capital of|translate|write me|who won)\\b', re.I),
    re.compile('\\b(restaurant|hotel|flight|travel|trip|vacation|holiday|weight|diet|workout|gym|doctor|medicine|resume|cover letter|interview tips|relationship|game|gaming|news|horoscope|astrology|shopping|phone to buy|laptop)\\b', re.I),
]

FUNDS_IN = re.compile('\\b(parag parikh|ppfas|nippon|mirae|quant|canara robeco|motilal oswal|axis (bluechip|small|midcap|flexi)|sbi (bluechip|small|contra|magnum)|hdfc (flexi|mid|small|top|index|balanced)|icici pru\\w*|kotak (emerging|flexi)|uti nifty|tata (digital|small)|dsp (small|midcap)|franklin|aditya birla|bandhan|edelweiss|invesco)\\b', re.I)
FUNDS = re.compile('\\b(parag parikh|ppfas|nippon|hdfc (mf|mutual|flexi|mid|small|top|index|balanced)|icici pru\\w*|sbi (mf|mutual|bluechip|small|contra|magnum)|axis (mf|mutual|bluechip|small|midcap)|mirae|quant (small|mid|active)|kotak (mf|emerging|flexi)|uti (nifty|flexi|mf)|motilal oswal (mf|midcap|nasdaq)|tata (digital|small|mf)|canara robeco|dsp (mf|small|midcap)|franklin|aditya birla|bandhan|edelweiss|hsbc (mf|small)|invesco)\\b', re.I)
ADVICE_OUT = re.compile("\\b(you should (buy|invest|sell|stop|continue|start|pause|cancel|switch|increase|reduce|hold|keep)|i (would |'d )?(recommend|suggest) (you )?(invest|buy|choose|pick|start|stop|continue|switch)|we recommend|best (fund|sip|scheme)s? (is|are|for you)|keep (your )?sips? (going|running)|don'?t stop (your )?sip|do not stop (your )?sip|stay invested|invest in [A-Z])", re.I)
URGENCY = re.compile("\\b(act now|hurry|before it'?s too late|don'?t miss|last chance|limited time|you will regret|lose out|missing out|fomo|right now or|immediately invest)\\b", re.I)
_FUND_OPINION = re.compile(r"\b(good|best|safe|buy|invest|better|worth|risky|bad|start|returns?)\b", re.I)
_TOPIC_WORDS = re.compile(r"\b(sip|mutual|fund|invest|groww|mf)\b", re.I)


def check_input(text):
    t = str(text or "").strip()
    if not t:
        return {"verdict": "empty", "reason": "Empty message"}
    if len(t) > 800:
        return {"verdict": "too_long", "reason": "Over 800 characters"}
    n = norm(t)
    sq = squash(n)
    low = t.lower()
    for r in ABUSE:
        if r.search(n) or r.search(sq) or r.search(low):
            return {"verdict": "abuse", "reason": "Abusive or offensive language"}
    for kind, r in PII:
        if r.search(t):
            return {"verdict": "pii", "reason": "Looks like a " + kind, "kind": kind}
    for r in INJECTION:
        if r.search(t):
            return {"verdict": "injection", "reason": "Tries to change the engine's rules"}
    if FUNDS_IN.search(t) and _FUND_OPINION.search(t):
        return {"verdict": "advice", "reason": "Asks for an opinion on a specific fund"}
    for r in ADVICE:
        if r.search(t):
            return {"verdict": "advice", "reason": "Asks for investment advice"}
    for r in OFFTOPIC:
        if r.search(t) and not _TOPIC_WORDS.search(t):
            return {"verdict": "off_topic", "reason": "Outside SIP and investor research"}
    return {"verdict": "ok"}


def numbers_in(s):
    out = []
    for x in re.findall(r"\d[\d,]*(?:\.\d+)?", str(s)):
        try:
            out.append(float(x.replace(",", "")))
        except ValueError:
            pass
    return out


ALLOWED_NUMBERS = {0, 1, 2, 3, 12, 30, 100, 2024, 2025, 2026}  # months, scale, years


def check_output(answer, tool_numbers=None):
    a = str(answer or "")
    issues = []
    if FUNDS.search(a):
        issues.append("names a fund or fund house")
    if ADVICE_OUT.search(a):
        issues.append("uses advice wording")
    if URGENCY.search(a):
        issues.append("uses urgency or FOMO wording")
    for kind, r in PII:
        if kind not in ("long number", "screenshot or statement") and r.search(a):
            issues.append("contains personal data (" + kind + ")")
            break
    grounded, ungrounded = None, []
    if tool_numbers is not None:
        pool = set()
        for x in tool_numbers:
            pool.update({x, round(x), round(x * 10) / 10})
        nums = [x for x in numbers_in(a) if x not in ALLOWED_NUMBERS]
        for x in nums:
            ok = x in pool or round(x) in pool or (x % 1 != 0 and any(abs(p - x) <= 0.15 for p in pool))
            if not ok:
                ungrounded.append(x)
        grounded = {"total": len(nums), "traced": len(nums) - len(ungrounded)}
        if ungrounded:
            issues.append("states numbers not found in the counted data (" + ", ".join(f"{u:g}" for u in ungrounded[:4]) + ")")
    return {"pass": not issues, "issues": issues, "grounded": grounded, "ungrounded": ungrounded}
