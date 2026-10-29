"""Knowledge layer: answers that don't come from counting comments.
1. SIP basics: general, neutral explanations (checked against AMFI, SEBI, fund-house and Groww help pages, Oct 2026). Never names a fund,
   never says what someone should do.
2. Research answers: the brief's discovery questions and the project's method, numbers and deliverables, built from data/engine_data.json.
Anything else goes to the counting tools (and the AI) in pipeline.py."""
import json
import os
import re

from engine import data as D

SRC_NOTE = "General information, not advice."
AMFI = "AMFI investor education (amfiindia.com)"


def _n(x):
    return f"{x:,}"


# ------------------------------------------------------------------ SIP basics
# topic: (trigger regexes, answer text, optional data hook (filter, phrase), follow-up research question)
BASICS = {
    "min_amount": ([r"\bmin(imum)?\b.{0,30}\b(amount|sip|invest|rupees?|rs)\b", r"\b(lowest|smallest|least)\b.{0,20}\b(amount|sip)\b",
                    r"\bstart\b.{0,25}\b(with|from)\b.{0,10}(₹|rs\.?|rupees?|\d)", r"kitne\s+(paise|rupaye|rupay|rs)", r"chh?oti\s+sip", r"\b(100|250|500)\s*(rs|rupees?|₹)?\b.{0,20}\bsip\b",
                    r"\bsip\b.{0,20}\b(100|250|500)\s*(rs|rupees?)\b"],
                   "Most fund houses let you start a SIP from about ₹100 to ₹500 a month; each scheme sets its own minimum, shown on the scheme page in the app. "
                   "SEBI and AMFI also introduced a ₹250 \"Chhoti SIP\" aimed at new investors, offered by the fund houses that choose to take part.",
                   None, "What do first-time investors say about starting with a small amount?"),
    "sip_vs_lumpsum": ([r"\blump\s?-?sum\b", r"\bways?\s+to\s+invest\b", r"\bone[- ]time\b.{0,20}\b(invest|payment)", r"\bmonthly\b.{0,20}\b(or|vs|versus)\b.{0,20}\bonce\b"],
                       "There are two ways to put money into a mutual fund. A lumpsum is a single payment that buys units at one day's NAV. "
                       "A SIP invests a fixed amount at regular intervals (usually monthly) through an automatic debit, so each instalment buys units at that day's NAV. "
                       "Neither is guaranteed to do better; which suits someone depends on their cash flow and goals, which this engine does not judge.",
                       ({"keyword": "lumpsum|lump sum"}, "mention a lumpsum"), "How do investors describe changes in their income affecting their SIP?"),
    "frequency": ([r"\b(weekly|daily|fortnightly|quarterly)\b.{0,30}\bsip\b|\bsip\b.{0,30}\b(weekly|daily|fortnightly|quarterly)\b", r"\bfrequenc(y|ies)\b", r"\bhow often\b.{0,20}\b(instal|debit|pay)"],
                  "Monthly is the most common, but many fund houses and apps also offer daily, weekly, fortnightly or quarterly SIPs. "
                  "The frequencies and minimum amounts available differ by scheme and app.",
                  None, "What do new investors check after starting?"),
    "sip_date": ([r"\b(sip|instal+ment|debit)\s+date\b", r"\bchange\b.{0,20}\bdate\b", r"\bchoose\b.{0,20}\bdate\b", r"\bwhich date\b"],
                 "You pick the SIP date when you set the SIP up. Most apps let you change the date by editing the SIP (some do it by cancelling and creating a new one). "
                 "Because each debit is scheduled in advance, a change can take one cycle to apply.",
                 None, "Do people ask to pause instead of cancel?"),
    "start_sip": ([r"\bhow\s+(do|can|to)\s+(i\s+)?(start|begin|open|set ?up)\b.{0,20}\bsip\b", r"\bsteps?\b.{0,15}\b(start|begin|set ?up)\b.{0,15}\bsip\b",
                   r"\bsip\b.{0,15}\b(kaise|kese)\s+(shuru|start)", r"\bhow\s+to\s+invest\s+in\s+(a\s+)?sip\b"],
                  "Starting a SIP usually takes four steps: complete KYC once; choose a scheme and an amount; pick the frequency and date; and approve a payment "
                  "mandate (UPI AutoPay or a bank e-mandate) so instalments are debited automatically. On Groww this is done from the mutual funds section of the app, "
                  "and groww.in/help has the current steps. Choosing the scheme is a personal decision this engine does not advise on.",
                  ({"stage": ["starting_setup"]}, "are about setting up or starting a SIP"), "What goes wrong for investors while setting up their first SIP?"),
    "stop_sip": ([r"\b(can|how)\b.{0,15}\b(stop|cancel|close|end|discontinue)\b.{0,15}\bsip\b", r"\bpenalt(y|ies)\b.{0,25}\b(stop|cancel)", r"\b(stop|cancel)\w*\b.{0,15}\bsip\b.{0,15}\b(anytime|any time|penalt|charge)",
                  r"\bsip\b.{0,15}\b(band|cancel|stop)\s+(kaise|kese)", r"\bhow\s+to\s+(stop|cancel)\b"],
                 "Yes. A SIP can be cancelled at any time, and fund houses do not charge a penalty for stopping. Cancelling stops future instalments only; "
                 "units already bought remain in the fund until you redeem them. On most apps it is done from the SIP's edit or manage option (on Groww: My SIPs, then the SIP). "
                 "If the next debit is already scheduled, the cancellation can take one cycle to apply. Redeeming the units is a separate step and may carry an exit load or tax.",
                 ({"event_any": ["stopped_cancelled"]}, "describe stopping or cancelling a SIP"), "Why do first-time investors stop their SIPs?"),
    "cancel_effect": ([r"\bwhat happens\b.{0,25}\b(money|units|investment)\b.{0,25}\b(stop|cancel)", r"\b(stop|cancel)\w*\b.{0,25}\bwhat happens\b.{0,20}\b(money|units|investment)",
                       r"\bmoney\b.{0,20}\bafter\b.{0,15}\b(stop|cancel)"],
                      "Stopping a SIP only stops future instalments. The money already invested stays in the fund as units, and its value keeps moving with the fund's NAV "
                      "until you redeem. Taking the money out is a separate step (redemption), which may carry an exit load or tax depending on how long the units were held.",
                      None, "Why do investors redeem or withdraw?"),
    "missed_instalment": ([r"\bmiss(ed)?\b.{0,20}\b(sip|instal|payment|debit)", r"\b(sip|instal+ment|payment|debit|autopay|mandate)\b.{0,20}\b(fail|bounce|bounced|decline)", r"\bbounce\b",
                           r"\b(3|three)\b.{0,20}\b(fail|miss|consecutive)", r"\binsufficient\s+(balance|funds)"],
                          "If an instalment's debit fails, usually because of low balance or a mandate problem, no units are bought for that instalment. Fund houses generally "
                          "do not charge a penalty, but your bank may charge a fee for a failed auto-debit. If several instalments in a row fail (commonly three), the fund house "
                          "may cancel the SIP. Units already bought are not affected.",
                          ({"driver_any": ["payment_mandate_failure"]}, "describe a payment, mandate or autopay failure"), "What goes wrong when Groww SIP payments fail?"),
    "pause_skip": ([r"\b(pause|skip|hold)\w*\b.{0,25}\b(sip|instal)", r"\bsip\b.{0,25}\b(pause|skip)", r"\bpause\s+(kaise|kese)", r"\bcan i pause\b", r"\bbreak\b.{0,15}\bsip\b"],
                   "Many apps and fund houses let you pause or skip upcoming instalments instead of cancelling. On Groww, its help centre describes: My SIPs, choose the SIP, "
                   "Edit SIP, then Skip instalment. How many instalments can be skipped, and how far ahead you must do it, differ by app and fund house. "
                   "The SIP resumes after the pause.",
                   ({"driver_any": ["missing_control_pause_skip_modify"]}, "describe wanting a pause, skip or change option they could not find"), "Do people ask to pause instead of cancel?"),
    "modify_amount": ([r"\b(increase|decrease|reduce|change|modify|edit|lower|raise)\b.{0,20}\b(sip|amount|instal)", r"\bsip\b.{0,15}\bamount\b.{0,15}\b(change|kam|badh)"],
                      "Most apps let you change a SIP's amount by editing it; some handle it by cancelling and starting a new SIP. A step-up option can raise the amount "
                      "automatically each year. The change usually applies from a later instalment.",
                      ({"event_any": ["reduced", "increased_stepup"]}, "describe reducing or increasing a SIP"), "What makes investors increase their SIP?"),
    "tax": ([r"\btax(ed|es|ation)?\b", r"\b(ltcg|stcg|capital gains?)\b"],
            "Tax applies when units are sold (redeemed), not when you invest. For equity-oriented funds (at least 65% in Indian shares), as of FY 2026-27: gains on units "
            "held 12 months or less are taxed at 20%; gains on units held longer are taxed at 12.5% on gains above ₹1.25 lakh in a financial year. In a SIP each "
            "instalment counts separately, so its holding period starts on its own date. Debt-oriented funds bought after 1 April 2023 are taxed at your income slab. "
            "Tax rules change with Budgets, so check the latest rules or a tax professional.",
            None, "What do investors say about fees and charges?"),
    "elss_lockin": ([r"\belss\b.{0,30}\block", r"\block[- ]?in\b"],
                    "ELSS funds have a three-year lock-in. In a SIP each instalment is locked for three years from its own date, so the last instalment unlocks three years "
                    "after it was invested. ELSS investments can be claimed under Section 80C only in the old tax regime.",
                    ({"keyword": "elss|tax sav|80c"}, "mention ELSS or tax saving"), "Why do first-time investors start a SIP?"),
    "nav_cutoff": ([r"\bcut[- ]?off\b", r"\bwhich nav\b", r"\bnav\b.{0,20}\b(get|apply|applicable|allot)", r"\b(units?|allotment)\b.{0,20}\b(when|late|delay|allot)"],
                   "For most schemes (other than liquid and overnight funds) the cut-off is 3 PM on a business day. You get the NAV of the day the fund house receives "
                   "your money: before 3 PM, that day's NAV; after, the next business day's. For a SIP, the NAV depends on when the debited money reaches the fund house, "
                   "which is why units can appear a day or two after the debit.",
                   ({"driver_any": ["confusing_numbers_or_terms"]}, "mention confusing numbers or terms"), "Do investors find numbers like XIRR confusing?"),
    "rupee_cost_avg": ([r"\brupee\s+cost\s+averag", r"\bcost\s+averag", r"\baveraging\b"],
                       "Rupee cost averaging describes what happens when the same amount is invested at regular intervals: it buys more units when the NAV is low and fewer "
                       "when it is high, so the average cost per unit evens out over time. It does not guarantee a profit or protect against losses.",
                       None, "What did investors expect from returns, and what did they describe happening?"),
    "compounding": ([r"\bcompound(ing)?\b(?!\s+annual)", r"\bpower of compounding\b"],
                    "Compounding means gains can earn further gains: growth applies to the whole accumulated amount, not just what was put in. In a SIP each instalment "
                    "compounds from its own date, so earlier instalments have longer to grow. Mutual fund returns are not fixed, so growth varies year to year and can be negative.",
                    None, "What did investors expect from returns, and what did they describe happening?"),
    "redemption": ([r"\b(withdraw|redeem|redemption|take out)\w*\b", r"\bpaise\s+(nikal|wapas)"],
                   "Redemption means selling mutual fund units to get the money back. In an app it is done from the fund's page (Redeem or Withdraw). SEBI requires fund "
                   "houses to pay redemptions within three working days, and many credit equity funds sooner. An exit load or tax may apply.",
                   ({"event_any": ["redeemed_withdrew"]}, "describe redeeming or withdrawing"), "Why do investors redeem or withdraw?"),
    "mandate_time": ([r"\bmandate\b.{0,30}\b(time|long|days|approv|pending|register)", r"\b(how long|time)\b.{0,30}\bmandate\b", r"\bautopay\b.{0,20}\b(time|long|approv|pending)"],
                     "A UPI AutoPay mandate is usually active as soon as you approve it in your UPI app. A bank e-mandate (via net banking or debit card) usually registers "
                     "within a few working days, and a paper mandate can take a few weeks. Until it is approved, instalments may fail or need to be paid manually.",
                     ({"driver_any": ["payment_mandate_failure"]}, "describe a payment, mandate or autopay failure"), "What goes wrong when Groww SIP payments fail?"),
    "multiple_sips": ([r"\b(more than one|multiple|several|two|many)\s+sips?\b", r"\bsips?\b.{0,15}\bat (the )?same time\b"],
                      "Yes. You can run several SIPs at once, in the same fund or different funds, each with its own amount and date. Each SIP is tracked separately.",
                      None, "What do new investors check after starting?"),
    "returns_guarantee": ([r"\b(guarantee|guaranteed|assured|fixed)\b.{0,20}\breturn", r"\breturns?\b.{0,20}\b(guarantee|guaranteed|assured|fixed)"],
                          "No. SIP returns are not guaranteed. A SIP is only a way of investing; returns depend on what the fund invests in and on markets, and they can be "
                          "negative, especially over short periods. Past returns shown in apps do not indicate future returns.",
                          ({"driver_any": ["returns_below_expectation"]}, "describe returns falling short of what they expected"),
                          "What did investors expect from returns, and what did they describe happening?"),
    "risk": ([r"\b(is|are)\s+(a\s+)?sips?\s+(risky|safe)\b", r"\brisk(s|y)?\b.{0,15}\b(sip|mutual)", r"\bsip\b.{0,15}\brisk", r"\briskometer\b", r"\bcan i lose\b"],
             "A SIP is only a method of investing; the risk comes from the fund it invests in. Equity funds can fall in value, especially over short periods; debt funds "
             "carry interest-rate and credit risk. Every scheme shows a riskometer level from low to very high. Whether a level of risk suits someone is a personal decision "
             "this engine does not advise on. Mutual fund investments are subject to market risks, read all scheme related documents carefully.",
             ({"driver_any": ["negative_or_volatile_returns"]}, "describe negative or volatile returns"), "What did investors expect from returns, and what did they describe happening?"),
    "fund_types": ([r"\btypes?\s+of\s+(mutual\s+)?funds?\b", r"\b(kinds?|categories|category)\s+of\s+(mutual\s+)?funds?\b", r"\bequity\b.{0,15}\bdebt\b.{0,15}\bhybrid\b"],
                   "SEBI groups mutual funds into five broad types: equity (mainly shares), debt (bonds and money-market instruments), hybrid (a mix of both), "
                   "solution-oriented (retirement or children's funds, with lock-ins), and others (index funds, ETFs and funds of funds). Each has sub-categories, "
                   "such as large-cap or liquid funds.",
                   None, "What do first-time investors say about choosing where to start?"),
    "index_fund": ([r"\bindex\s+funds?\b", r"\bpassive\s+funds?\b"],
                   "An index fund copies a market index, such as the Nifty 50, by holding the same shares in the same proportions instead of a manager picking them. "
                   "It usually has a lower expense ratio, and its returns follow the index, up or down.",
                   None, "What do first-time investors say about choosing where to start?"),
    "stp_swp": ([r"\b(stp|swp)\b", r"\bsystematic\s+(transfer|withdrawal)\b"],
                "An STP (systematic transfer plan) moves a fixed amount at regular intervals from one fund to another within the same fund house, for example from a "
                "liquid fund to an equity fund. An SWP (systematic withdrawal plan) is the reverse of a SIP: it redeems a fixed amount at regular intervals and pays it "
                "to your bank account.",
                None, "Why do investors redeem or withdraw?"),
    "folio_cas": ([r"\bfolio\b", r"\b(cas|consolidated account statement)\b", r"\ball my (mutual )?funds\b", r"\bone statement\b", r"\bcams\b|\bkfintech\b|\bmf ?central\b"],
                  "A folio number is the account number a fund house gives your investments with it. To see all your mutual funds across fund houses in one place, you "
                  "can get a Consolidated Account Statement (CAS) from the registrars CAMS or KFintech, or from MF Central, using the email linked to your investments. "
                  "Please don't share folio numbers here; this engine can't look up accounts.",
                  ({"outside_any": ["amc_or_cams_kfintech"]}, "describe going to the fund house or its registrar (CAMS, KFintech)"), "Where do investors go when they are unsure?"),
    "sip_vs_fd": ([r"\b(fd|fixed deposit|rd|recurring deposit|ppf|savings account)\b"],
                  "A fixed deposit (FD) or recurring deposit (RD) pays a fixed interest rate agreed upfront, and bank deposits are insured up to ₹5 lakh per bank by DICGC. "
                  "An RD is the deposit equivalent of a SIP: a fixed monthly amount. A SIP in a mutual fund has no fixed rate; its value moves with the market and can go "
                  "down as well as up. FD and RD interest is taxed at your income slab every year, while mutual fund gains are taxed when you redeem. "
                  "Which suits someone is a personal decision this engine does not advise on.",
                  None, "What did investors expect from returns, and what did they describe happening?"),
    "kyc": ([r"\bkyc\b", r"\bknow your customer\b"],
            "KYC (Know Your Customer) is a one-time identity check needed before investing in mutual funds in India. It usually needs your PAN, an address proof such "
            "as Aadhaar, and a photo and signature; most apps complete it online through Aadhaar-based eKYC, sometimes with a short video check. Once done, it works "
            "across fund houses. Please don't share these documents or numbers here.",
            ({"stage": ["starting_setup"]}, "are about setting up or starting a SIP"), "What goes wrong for investors while setting up their first SIP?"),
    "direct_regular": ([r"\bdirect\b.{0,25}\bregular\b", r"\bregular\b.{0,25}\bdirect\b", r"\bdirect (plan|fund)s?\b", r"\bregular (plan|fund)s?\b"],
                       "A direct plan is bought straight from the fund house with no distributor commission, so its expense ratio is lower. A regular plan is bought "
                       "through a distributor and includes their commission. Both invest in the same portfolio, so the difference in returns comes from the cost.",
                       ({"driver_any": ["fees_or_hidden_charges"]}, "mention fees or hidden charges"), "What do investors say about fees and charges?"),
    "sip_calculator": ([r"\bcalculator\b", r"\b(calculate|calculation)\b.{0,20}\b(sip|return|maturity)"],
                       "A SIP calculator estimates a future value from three inputs: the monthly amount, the number of months and an assumed yearly return, applying compound "
                       "growth to each instalment from its own date. The result is only as good as the assumed return, which is not guaranteed, so it shows a scenario, "
                       "not a forecast. This engine does not project returns.",
                       None, "What did investors expect from returns, and what did they describe happening?"),
}
BASICS_FROM_GLOSSARY = {"pause": "pause_skip", "lapse": "missed_instalment", "lumpsum": "sip_vs_lumpsum"}

DATA_ASK = re.compile(r"\b(quotes?|comments?|reviews?|people|investors|users|say|said|says|complain\w*|mention\w*|log|reddit|play store|app store|youtube|trend|over time|"
                      r"what goes wrong|groww|zerodha|coin|upstox|indmoney|angel|paytm|kuvera|et money)\b", re.I)
HOWTO = re.compile(r"\b(how (do|can|to)|can i|kaise|kese|steps?|what happens|is there|are there|what is|what are|what's)\b", re.I)
ADVICE_WORDS = re.compile(r"\b(should|shall i|best|better|top \d|highest|good time|right time|worth it|recommend|suggest|which fund|which scheme|kaun\w*|konsa|lena chahiye|"
                          r"karna chahiye|for me|my portfolio|will .{0,20}(give|return|grow)|predict|how much should|safe for me|good for me)\b"
                          r"|\bwhich\b.{0,25}\b(fund|scheme|elss|stock|share|app|amc)s?\b|\b(most|maximum|max|highest|least)\b.{0,15}\b(tax|return|profit|gain|safe)"
                          r"|\b(enough|karu|karun|karoon|karoo|lu|lun|loon|abhi|is it ok|okay to|right for|suit\w* me|meri|mere|mera)\b"
                          r"|\b(name|suggest|tell me)\b.{0,15}\b(a|some|good|the)?\s*(fund|scheme|stock)s?\b", re.I)

# ------------------------------------------------------------------ research answers (brief questions, method, deliverables)
RESEARCH = {
    "q1": [r"\bwhy\b.{0,25}\b(start|begin|invest)\w*\b.{0,15}\bsips?\b", r"\b(expect|expectation)\w*\b.{0,40}\b(start|invest|sip)", r"\breasons?\b.{0,15}\b(to|for)\s+start", r"\bsip\b.{0,15}\bkyun\s+shuru"],
    "q2": [r"\b(behaviou?r|habits?)\b.{0,30}\b(change|after)", r"\bmonths? after (starting|they start)", r"\bafter the first (few )?months\b", r"\bchanges?\b.{0,30}\bafter\s+start"],
    "q3": [r"\bwhy\b.{0,30}\b(stop|pause|reduce|cancel|quit|discontinu)\w*\b", r"\b(lead|cause|make|reasons?)\w*\b.{0,30}\b(stop|pause|reduc|cancel|discontinu)", r"\bdiscontinu", r"\bkyun\b.{0,15}\b(band|rok|chhod)"],
    "q4": [r"\bwhat\b.{0,20}\b(check|track|monitor|look at)\b", r"\bhow often\b.{0,20}\b(check|look)"],
    "q5": [r"\b(confus|worr)\w*\b"],
    "q6": [r"\boutside\b.{0,15}\bapp\b", r"\b(where|who)\b.{0,25}\b(go|turn|ask)\b.{0,20}\b(help|unsure|doubt)", r"\bwhen\b.{0,10}\b(unsure|confused|in doubt)"],
    "q7": [r"\b(separat|differen|distinguish)\w*\b.{0,40}\b(continu|stay|keep)\w*\b.{0,40}\b(drop|stop|quit)", r"\bcontinu\w*\b.{0,15}\b(vs|versus|and)\b.{0,25}\bdrop", r"\bwho (stays|continues)\b"],
    "q8": [r"\bsegments?\b", r"\b(salaried|self[- ]employed|freelanc|variable income|students?|age|younger|older|income stability|source of money|influenc)\w*\b.{0,60}\b(differ|vs|versus|compare|behave)",
           r"\b(differ|vs|versus|compare|behave)\w*\b.{0,60}\b(salaried|self[- ]employed|students?|age|income)"],
    "q9": [r"\bunmet\s+needs?\b", r"\bwhat\b.{0,20}\b(do|did)\b.{0,15}\b(investors|people|users)\b.{0,10}\b(want|wish|need|ask for)\b", r"\b(don'?t|do not) get\b"],
    "metric": [r"\b(business|north star|success|key|goal)\s+metric\b", r"\bmetric\b.{0,20}\b(project|goal|this)\b", r"\b12[- ]month\b.{0,20}\b(continuation|metric)"],
    "active_sip": [r"\bactive sip\b", r"\bcounts? as active\b"],
    "problem": [r"\bproblem\s+(statement|are you|is this|this engine)\b", r"\bwhat problem\b", r"\bwhat is (this|the) (project|engine) (about|for)\b", r"\bpurpose of (this|the) (engine|project)\b"],
    "sources": [r"\b(which|what)\s+(data\s+)?sources\b", r"\bhow (many|much)\b.{0,15}\b(comments|reviews|data|posts)\b", r"\bwhere\b.{0,15}\bdata\b.{0,15}\bfrom\b", r"\bsources?\b.{0,20}\b(collect|use|scrap)"],
    "cleaning": [r"\b(clean|filter|dedup)\w*\b.{0,20}\bdata\b", r"\bdata\b.{0,20}\b(clean|filter)", r"\bhow\b.{0,15}\b(clean|filter)"],
    "tagging": [r"\b(themes?|tags?|tagging|codebook|label)\w*\b.{0,30}\b(identif|found|creat|made|work|how)", r"\bhow\b.{0,25}\b(ai|model)\b.{0,15}\b(tag|label|classif)", r"\b(which|what)\s+(ai|llm|model)s?\b", r"\bprompt\b"],
    "validation": [r"\bgolden\s+set\b", r"\b(valid|accura|quality)\w*\b.{0,30}\b(insight|tag|ai|data|output)", r"\b(insight|tag|data|output)\w*\s+quality\b", r"\bvalidat\w*\b", r"\bhow (accurate|reliable|good)\b", r"\bevidence log\b", r"\bhuman label"],
    "guardrails": [r"\bguardrails?\b", r"\b(stop|prevent|avoid|block)\w*\b.{0,50}\b(advice|abus|fund names?|recommend)", r"\bsafety\b", r"\bhow\b.{0,20}\b(safe|safety)\b.{0,20}\bengine\b"],
    "evals": [r"\bevals?\b", r"\bevaluat\w*\b", r"\btest (results|cases|suite)\b", r"\bhow (did|do) you test\b"],
    "opportunities": [r"\bopportunit(y|ies)\b(?!.{0,30}\b(biggest|largest|top|best|first|focus|priorit|scor|rank))", r"\bopportunity areas\b"],
    "top_opportunity": [r"\b(biggest|largest|top|best|main|first|highest|strongest)\b.{0,20}\bopportunit", r"\bopportunit\w*\b.{0,30}\b(focus|priorit|first|biggest|largest|top)",
                        r"\bwhat should groww (build|fix|focus|do)\b", r"\bwhere should groww focus\b", r"\bwhich problem\b.{0,20}\b(solve|fix|first)"],
    "scoring": [r"\bopportunit\w*\b.{0,25}\b(scor|rank|prioriti)\w*", r"\b(score|scored|scoring|rank|ranked|ranking|prioriti[sz])\w*\b.{0,30}\b(opportunit|area|how)", r"\bhow\b.{0,20}\b(score|rank|prioriti)"],
    "limitations": [r"\blimitations?\b", r"\b(bias|biased|caveats?|weakness)\w*\b", r"\bcan (we|i) trust\b"],
    "drop_types": [r"\b(involuntary|voluntary|passive drift)\b", r"\b(types?|kinds?)\s+of\s+drop", r"\bwithout (deciding|choosing)\b"],
    "how_it_works": [r"\bhow\b.{0,15}\b(does|do)\b.{0,15}\b(this|the|your)\s+(discovery\s+)?engine\s+work", r"\bhow (it|this) works\b", r"\bpipeline\b", r"\barchitecture\b", r"\bhow (was|is) (this|it) built\b"],
    "next_steps": [r"\bnext\s+steps?\b", r"\bwhat happens next\b", r"\b(interviews?|mvp|deck)\b.{0,20}\b(status|done|plan|when)", r"\bwhat'?s next\b"],
}


def _E():
    return D.engine_data()


def _top(rows, k=3):
    return ", ".join(f"{D.lab(a).lower()} ({_n(b)})" for a, b in rows[:k])


def _chart(rows, title, base=None):
    vals = [{"value": str(a), "label": D.lab(a) if isinstance(a, str) else str(a), "n": b, "pct_of_base": round(100 * b / base, 1) if base else 0} for a, b in rows]
    return {"base_comments": base or sum(v["n"] for v in vals), "values": vals, "title": title}


def research(topic, led):
    """Returns (text, breakdown or None, quote filter or None, follow-up)."""
    E = _E()
    F, A, Q, O = E["funnel"], E["anatomy"], E["questions"], E["opportunities"]
    drops = F["dropoffs"]
    inv, vol = A["type"].get("involuntary", 0), A["type"].get("voluntary", 0)
    fti, ftn = A["first_time_type"].get("involuntary", 0), sum(A["first_time_type"].values())
    nums = []
    if topic == "q1":
        q = Q["q1"]
        out = [r for r in q["influencer"] if r[0] != "self"]
        nums += [q["started_n"], q["first_time_started"]] + [b for _, b in q["influencer"]]
        txt = (f"{_n(q['started_n'])} comments describe starting a SIP ({_n(q['first_time_started'])} from self-described first-time investors). Most say they decided "
               f"themselves ({_n(q['influencer'][0][1])}); the visible outside triggers are {_top(out, 3)}. Expectations show up mostly as gaps later: "
               f"{_n(dict(Q['q3']['drivers']).get('returns_below_expectation', 0))} drop-off comments say returns fell short of what they expected.")
        nums.append(dict(Q["q3"]["drivers"]).get("returns_below_expectation", 0))
        res = (txt, _chart(out, "Who influenced them to start (excluding 'self')"), {"event_any": ["started"]}, "Why do first-time investors stop their SIPs?")
    elif topic == "q2":
        q = Q["q2"]
        a, b, c = q["first_instalments_1_3m"], q["months_4_12"], q["beyond_12m"]
        nums += [a["drop_pct"], b["drop_pct"], c["drop_pct"], a["n"], b["n"], c["n"]]
        txt = (f"Drop-off talk roughly doubles after the first quarter: {a['drop_pct']}% of comments about months 1 to 3 describe a drop-off ({_n(a['n'])} comments), "
               f"against {b['drop_pct']}% for months 4 to 12 ({_n(b['n'])}) and {c['drop_pct']}% beyond 12 months ({_n(c['n'])}). Early comments are about starting and "
               "checking; later ones add stopping, redeeming and step-ups. Only comments where the stage is clear are counted.")
        rows = [("Months 1 to 3", a["drop_pct"]), ("Months 4 to 12", b["drop_pct"]), ("Beyond 12 months", c["drop_pct"])]
        res = (txt, {"base_comments": a["n"] + b["n"] + c["n"], "values": [{"value": k, "label": f"{k}: % describing a drop-off", "n": v, "pct_of_base": v} for k, v in rows]},
               {"stage": ["first_instalments_1_3m", "months_4_12"], "dropoff_only": True}, "What do new investors check after starting?")
    elif topic == "q3":
        q = Q["q3"]
        nums += [q["n"], q["ft_n"]] + [b for _, b in q["drivers"]] + [b for _, b in q["ft_drivers"]] + [inv, vol]
        txt = (f"Across {_n(q['n'])} comments describing a SIP being skipped, paused, reduced, stopped or lapsing, the most common reasons are {_top(q['drivers'], 4)}. "
               f"{_n(inv)} of these drop-offs ({round(100*inv/drops,1)}%) were not the investor's choice: a failed debit, mandate or app error. For self-described first-time "
               f"investors (n={q['ft_n']}) the top reasons are {_top(q['ft_drivers'], 3)}. Market falls are one reason among many, not the main one.")
        nums.append(round(100 * inv / drops, 1))
        res = (txt, _chart(q["drivers"][:7], "Reasons in drop-off comments", q["n"]), {"dropoff_only": True}, "How many drop-offs are involuntary?")
    elif topic == "q4":
        q = Q["q4"]
        nums += [b for _, b in q["first_time"]] + [b for _, b in q["all"]]
        txt = (f"First-time investors mostly check {_top(q['first_time'], 3)}; XIRR and NAV matter far less to them than to experienced investors "
               f"(all investors: {_top(q['all'], 3)}). How often they check is rarely stated in public text, so the interviews cover frequency.")
        res = (txt, _chart(q["first_time"], "What first-time investors check"), {"first_time": True, "check_any": ["instalment_status", "returns_pl"]}, "Do investors find numbers like XIRR confusing?")
    elif topic == "q5":
        q = Q["q5"]
        nums += [b for _, b in q]
        txt = (f"Inside the app, the biggest worries are {_top(q, 3)}, then {_top(q[3:], 3)}. Confusing figures (returns, XIRR, NAV) are a smaller but steady theme.")
        res = (txt, _chart(q, "What confuses or worries them"), {"driver_any": ["confusing_numbers_or_terms", "trust_or_support_failure"]}, "Do investors find numbers like XIRR confusing?")
    elif topic == "q6":
        q = Q["q6"]
        nums += [b for _, b in q["first_time"]] + [b for _, b in q["all"]]
        txt = (f"When unsure, first-time investors turn to {_top(q['first_time'], 3)}, ahead of other routes; experienced investors go first to "
               f"{_top(q['all'], 3)}.")
        res = (txt, _chart(q["first_time"], "Where first-time investors turn"), {"first_time": True, "outside_any": ["youtube_social", "forum_reddit"]}, "Where do investors go when they are unsure?")
    elif topic == "q7":
        q = Q["q7"]
        nums += [q["continuers_n"], q["dropoffs_n"]] + [b for _, b in q["continuer"]] + [b for _, b in q["dropoff"]]
        txt = (f"Comments from people still investing (n={_n(q['continuers_n'])}) credit {_top(q['continuer'], 1)} most, while drop-off comments (n={_n(q['dropoffs_n'])}) cite "
               f"{_top(q['dropoff'], 3)}. Both groups mention weak returns, so returns alone don't decide who stays; whether the platform keeps working does.")
        rows = [(f"Still investing: {D.lab(k)}", n) for k, n in q["continuer"][:3]] + [(f"Dropped off: {D.lab(k)}", n) for k, n in q["dropoff"][:3]]
        res = (txt, {"base_comments": q["continuers_n"] + q["dropoffs_n"], "values": [{"value": k, "label": k, "n": n, "pct_of_base": 0} for k, n in rows]},
               {"event_any": ["continued"]}, "What makes investors increase their SIP?")
    elif topic == "q8":
        q = Q["q8"]
        parts = []
        for f in ("income", "age_hint"):
            for k, v in q[f].items():
                parts.append((k, v))
                nums += [v["n"], v["pct_dropoff"]] + [b for _, b in v["top_drivers"]]
        inc = q["income"]
        txt = (f"Salaried writers (n={_n(inc['salaried']['n'])}) describe a drop-off in {inc['salaried']['pct_dropoff']}% of comments and variable-income writers "
               f"(n={_n(inc['variable_self_employed']['n'])}) in {inc['variable_self_employed']['pct_dropoff']}%; both name cash-flow change as their top reason. Students "
               f"(n={_n(inc['student_no_income']['n'])}) describe fewer ({inc['student_no_income']['pct_dropoff']}%). By age: under 25 {q['age_hint']['under_25']['pct_dropoff']}% "
               f"(n={_n(q['age_hint']['under_25']['n'])}), 25 to 35 {q['age_hint']['25_35']['pct_dropoff']}% (n={_n(q['age_hint']['25_35']['n'])}). Those influenced by friends "
               f"or family describe drop-offs in {q['influencer']['friend_family']['pct_dropoff']}% (n={q['influencer']['friend_family']['n']}). Few comments state income or age, "
               "so these cuts are thin and directional; interviews fill the gap.")
        nums += [q["influencer"]["friend_family"]["pct_dropoff"], q["influencer"]["friend_family"]["n"]]
        res = (txt, {"base_comments": sum(v["n"] for _, v in parts), "values": [{"value": k, "label": f"{D.lab(k)} (n={_n(v['n'])}): % describing a drop-off", "n": v["pct_dropoff"], "pct_of_base": v["pct_dropoff"]} for k, v in parts]},
               None, "How do salaried and self-employed investors differ on why they stop?")
    elif topic == "q9":
        q = Q["q9"]
        N = q["needs"]
        nums += [q["need_items"], q["advice_seekers"]] + [x["n"] for x in N] + [x["pct_of_needs"] for x in N]
        txt = (f"Across {_n(q['need_items'])} comments where a need was recorded, the most repeated are: " + "; ".join(f"{x['need'].lower()} ({_n(x['n'])})" for x in N[:4]) +
               f". About {_n(q['advice_seekers'])} comments ask which fund to pick; the engine records that as a need but never answers it.")
        res = (txt, {"base_comments": q["need_items"], "values": [{"value": x["need"], "label": x["need"], "n": x["n"], "pct_of_base": x["pct_of_needs"]} for x in N[:6]]},
               None, "What do investors want instead of cancelling?")
    elif topic == "metric":
        txt = ("The project's business metric is the share of first-time mutual fund investors who still have an active SIP 12 months after starting their first one. "
               "An active SIP means at least one successful instalment in the last 30 days. This engine looks for what breaks that continuation; the metric itself is "
               "broken down into product outcomes and behaviours in the next part of the project.")
        res = (txt, None, None, "What leads investors to pause, reduce or stop a SIP?")
    elif topic == "active_sip":
        txt = ("For this project, an active SIP is one with at least one successful instalment in the last 30 days. So a SIP whose debits keep failing stops being "
               f"active even if the investor never cancelled it, which matters because {_n(inv)} of {_n(drops)} drop-off comments describe exactly that kind of lapse.")
        nums += [inv, drops]
        res = (txt, None, {"drop": ["involuntary"]}, "How many drop-offs are involuntary?")
    elif topic == "problem":
        top = O[0]
        nums += [drops, inv, round(100 * inv / drops, 1), top["opportunity_score"]]
        txt = ("This engine supports a growth project on Groww: why do first-time investors' SIPs stop being active within 12 months, despite good starting intent? The "
               "user problem is not given; it has to be discovered from evidence. What the public comments show so far: of "
               f"{_n(drops)} comments describing a drop-off, {_n(inv)} ({round(100*inv/drops,1)}%) describe a SIP that lapsed without the investor choosing to stop, and the "
               f"highest-scoring opportunity is \"{top['area']}\" (score {top['opportunity_score']}). The final problem statement comes after the interviews test this.")
        res = (txt, None, {"drop": ["involuntary"]}, "What is the biggest opportunity?")
    elif topic == "sources":
        rb = F["relevant_by_source"]
        nums += [F["collected"], F["cleaned"], F["tagged"], F["relevant"]] + list(rb.values())
        txt = (f"{_n(F['collected'])} public items were collected from Play Store and App Store reviews (Groww and 9 other investing apps), Reddit, YouTube comments on personal "
               f"finance videos, TradingQnA, Zerodha Varsity and Team-BHP. After cleaning, {_n(F['cleaned'])} remained; {_n(F['tagged'])} were AI-tagged and {_n(F['relevant'])} "
               "were judged relevant to SIPs. Relevant comments by source: " + ", ".join(f"{D.SRC.get(k, k)} {_n(v)}" for k, v in sorted(rb.items(), key=lambda kv: -kv[1])) + ".")
        res = (txt, {"base_comments": F["relevant"], "values": [{"value": k, "label": D.SRC.get(k, k), "n": v, "pct_of_base": round(100 * v / F['relevant'], 1)} for k, v in sorted(rb.items(), key=lambda kv: -kv[1])]},
               None, "How do Reddit and Play Store differ on why people stop?")
    elif topic == "cleaning":
        r = F["removed"]
        nums += [F["collected"], F["cleaned"]] + list(r.values())
        txt = (f"From {_n(F['collected'])} collected items, cleaning removed {_n(r['duplicates_removed'])} duplicates, {_n(r['too_short_removed'])} items too short to carry "
               f"meaning, {_n(r['not_relevant_removed'])} not about SIPs or mutual funds, and {_n(r['promotional_removed'])} promotional posts, leaving {_n(F['cleaned'])}. "
               "Usernames are never stored, and comments are tagged with their language (English, Hinglish or Hindi).")
        res = (txt, None, None, "Which sources did you collect data from?")
    elif topic == "tagging":
        m = F["models"]
        nums += [F["tagged"]] + list(m.values())
        txt = (f"Each of the {_n(F['tagged'])} cleaned comments was tagged by Google Gemini ({', '.join(f'{k} {_n(v)}' for k, v in m.items())}) against a fixed codebook, with a "
               f"strict output schema and temperature 0 (prompt {E['prompt_version']}). Tags record: relevance, first-time signal, lifecycle stage, events (started, paused, "
               "stopped, lapsed and so on), drop-off type, drivers, what they check, what they do outside the app, segment hints, severity, the unmet need and a verbatim "
               "evidence quote. Themes are counts of these tags, grouped into opportunity areas. Three early tagging errors were caught and corrected (see Quality and evals).")
        res = (txt, None, None, "How was insight quality validated?")
    elif topic == "validation":
        g, gr, rr = E["golden"], E["guardrail"], E["reddit_robustness"]
        nums += [g["size"], gr["checked"], gr["flags"], gr["true_violations"], rr["sample"]["drop%"], rr["all_tagged"]["drop%"]]
        txt = (f"Quality is checked four ways. 1) A golden set of {g['size']} comments sampled across themes is being hand-labelled; the agreement rate will be reported once the "
               f"labels are in (status: {g['status']}). 2) A guardrail review of all {_n(gr['checked'])} AI-written fields found {gr['flags']} keyword flags and "
               f"{gr['true_violations']} real issues (fund-house names repeated from the user's text, now masked). 3) A robustness check: a Reddit sample and the full Reddit set "
               f"give similar results (drop-off share {rr['sample']['drop%']}% vs {rr['all_tagged']['drop%']}%). 4) Early tagging errors were rejected and corrected: the model "
               "copied label definitions, counted generic praise as relevant, and treated support complaints as drop-offs.")
        res = (txt, None, None, "What are the limitations of this data?")
    elif topic == "guardrails":
        txt = ("Every message passes four checks. 1) A rule check blocks abuse (English, Hinglish and Hindi, including masked spellings), personal data (PAN, account, "
               "phone, email), attempts to override the rules, investment-advice requests and off-topic questions; blocked messages never reach the AI and are hidden. "
               "2) An AI intent check classifies the question. 3) The answer must be built from counting tools over the tagged comments. 4) An output check confirms every "
               "number traces to a count and that there are no fund names, advice wording, urgency or personal data; a failing answer is held back and replaced by the "
               "counted data. Quotes that name funds or give advice are never shown.")
        res = (txt, None, None, "How did you evaluate the engine?")
    elif topic == "evals":
        txt = _eval_text(nums)
        res = (txt, None, None, "What guardrails does this engine have?")
    elif topic in ("opportunities", "top_opportunity", "scoring"):
        nums += [o["opportunity_score"] for o in O] + [o["share_of_all_dropoffs_pct"] for o in O] + [o["n"] for o in O] + [o["avg_severity"] for o in O]
        if topic == "opportunities":
            txt = ("Seven opportunity areas were compared on drop-off reach, severity, how addressable they are by a product change, and fit with the brief's constraints: "
                   + "; ".join(f"{o['area'].split(' (')[0]} (score {o['opportunity_score']}, {o['share_of_all_dropoffs_pct']}% of drop-offs)" for o in O) + ".")
        elif topic == "top_opportunity":
            t = O[0]
            nums += [t["dropoff_n"], t["pct_of_area_with_dropoff"], t["first_time_n"], t["groww_n"]]
            txt = (f"The highest-scoring area is \"{t['area']}\" with a score of {t['opportunity_score']}, well ahead of the next ({O[1]['opportunity_score']}). It covers "
                   f"{t['share_of_all_dropoffs_pct']}% of all drop-off comments, {t['pct_of_area_with_dropoff']}% of its comments describe a drop-off, and its severity is the "
                   f"highest ({t['avg_severity']} of 3). Why it ranks first: {t['why']} This is a research ranking, not a final decision; the segment and opportunity are chosen "
                   "after interviews.")
        else:
            txt = ("Each area's score multiplies four parts, each scaled 0 to 1: its share of all drop-off comments (relative to the largest), average severity out of 3, "
                   "addressability by a product change (1 to 3, analyst judgement) and fit with the brief's constraints (1 to 3). So a frequent theme that is mild, hard for "
                   "the product to fix, or would need advice to solve scores lower than a less frequent but severe, fixable one. Scores: "
                   + "; ".join(f"{o['area'].split(' (')[0]} {o['opportunity_score']}" for o in O) + ".")
        res = (txt, {"base_comments": drops, "values": [{"value": o["area"], "label": o["area"].split(" (")[0], "n": o["opportunity_score"], "pct_of_base": o["opportunity_score"]} for o in O]},
               None, "What is the biggest opportunity?" if topic != "top_opportunity" else "How were the opportunities scored?")
    elif topic == "limitations":
        txt = ("Main limitations: 1) Public comments over-represent complaints and people who write online, so shares describe what people write, not the whole investor "
               "base. 2) Tags are AI-made and directional until the hand-labelled golden set confirms them. 3) Few comments state income or age, so segment cuts are thin. "
               "4) Quietly forgetting a SIP (passive drift) is rarely written about, so it is under-counted. 5) There is no behavioural data from Groww itself. The interviews "
               "and survey are designed to test these gaps.")
        res = (txt, None, None, "How was insight quality validated?")
    elif topic == "drop_types":
        dr = A["type"].get("passive_drift", 0)
        nums += [drops, vol, inv, dr, fti, ftn, round(100 * inv / drops, 1), round(100 * fti / ftn, 1)]
        txt = (f"Of {_n(drops)} comments describing a drop-off, {_n(vol)} were voluntary (the investor chose to stop, skip, pause or reduce), {_n(inv)} "
               f"({round(100*inv/drops,1)}%) were involuntary (a failed debit, broken mandate or app error stopped the SIP without the investor deciding), and {dr} were "
               f"passive drift. Among self-described first-time investors, {fti} of {ftn} ({round(100*fti/ftn,1)}%) were involuntary.")
        res = (txt, {"base_comments": drops, "values": [{"value": "v", "label": "Voluntary", "n": vol, "pct_of_base": round(100 * vol / drops, 1)},
                                                         {"value": "i", "label": "Involuntary", "n": inv, "pct_of_base": round(100 * inv / drops, 1)},
                                                         {"value": "p", "label": "Passive drift", "n": dr, "pct_of_base": round(100 * dr / drops, 1)}]},
               {"drop": ["involuntary"]}, "What goes wrong when Groww SIP payments fail?")
    elif topic == "how_it_works":
        nums += [F["collected"], F["cleaned"], F["tagged"], F["relevant"]]
        txt = (f"Five stages. 1) Collect: {_n(F['collected'])} public items from app stores, Reddit, YouTube and investing forums. 2) Clean: remove duplicates, very short, "
               f"promotional and off-topic items ({_n(F['cleaned'])} left). 3) Tag: an AI tags each comment against a fixed codebook ({_n(F['tagged'])} tagged, "
               f"{_n(F['relevant'])} relevant). 4) Analyse: count themes, compare sources and segments, and score opportunity areas. 5) Answer: this chat answers any "
               "question by counting the tagged comments, with guardrails before and after. The How it works page shows the full pipeline and limits.")
        res = (txt, None, None, "What guardrails does this engine have?")
    elif topic == "next_steps":
        txt = ("Next in the project: break the 12-month continuation metric into product outcomes and behaviours, choose a target segment and opportunity area, run 5 to 6 "
               "interviews with that segment to validate or challenge these findings, write the problem definition, then build and test an MVP. This engine's findings are "
               "directional until the interviews and the golden-set check are done.")
        res = (txt, None, None, "What is the biggest opportunity?")
    else:
        return None
    led.note(*[x for x in nums if isinstance(x, (int, float))])
    led.note(1, 2, 3, 4, 5, 6, 9, 12, 25, 30, 35, *[float(x) for x in re.findall(r"\d+", E["prompt_version"])])  # structural: list numbering, month ranges, age bands, 30-day rule, 9 comparison apps, 5-6 interviews, prompt version
    led.trace.append(f"Read pre-computed results for {topic}")
    return res


def _eval_text(nums):
    parts = []
    for mode, label in (("basic", "basic mode (rule checks and direct counts)"), ("ai", "full pipeline with AI")):
        p = os.path.join(D.DATA, f"eval_results_{mode}.json")
        if os.path.exists(p):
            s = json.load(open(p))["summary"]
            nums += [s["pass"], s["total"]]
            parts.append(f"{label}: {s['pass']} of {s['total']} passed")
    cases = len(D.load_json("eval_cases.json"))
    nums.append(cases)
    txt = (f"The engine is tested on {cases} questions in three sets (a development set used to tune the rules, and two held-out sets written before each round of "
           "fixes), covering research questions, basic terms, advice requests, off-topic questions, abuse in English, Hinglish and Hindi, personal data and attempts to "
           "override the rules. Each case is graded on whether the engine answered, declined or blocked correctly. Latest results: " + ("; ".join(parts) or "not run yet") + ".")
    if not any("AI" in x for x in parts):
        txt += " The AI run is scheduled for the next free Gemini quota window."
    return txt + " The Quality and evals page lists every case."


# ------------------------------------------------------------------ matching
def _norm(q):
    s = q.lower().replace("’", "'")
    s = re.sub(r"[?!.,;:\"“”]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _best(table, s):
    best, score = None, 0
    for key, pats in table.items():
        for p in pats:
            m = re.search(p, s)
            if m:
                sc = len(m.group(0)) + 1
                if sc > score:
                    best, score = key, sc
    return best


def match_basics(q):
    s = _norm(q)
    if ADVICE_WORDS.search(s):
        return None
    if DATA_ASK.search(s) and not HOWTO.search(s):
        return None                       # asks what investors say: answer from the comments instead
    return _best({k: v[0] for k, v in BASICS.items()}, s)


def match_research(q):
    return _best(RESEARCH, _norm(q))


def basics_answer(topic, led):
    pats, text, hook, follow = BASICS[topic]
    from engine import guard as G
    led.note(*G.numbers_in(text))          # reference facts in the authored text, checked against official pages (Oct 2026)
    led.facts = True
    fact = ""
    if hook:
        c = D.count(hook[0], led)
        if c["matching_comments"]:
            fact = f" In this engine's data, {c['matching_comments']:,} of {c['total_relevant']:,} relevant public comments ({c['share_pct']}%) {hook[1]}."
    return f"{text}{fact} {SRC_NOTE} For more, see {AMFI}.", follow


# ------------------------------------------------------------------ concept matching (generalises beyond exact phrasings)
# Each topic needs every word group to appear (any word in a group). More groups matched = more specific.
_W = lambda *ws: r"\b(" + "|".join(ws) + r")\b"
SIPW = _W("sips?", "instal+ments?", "mutual funds?", "mf", "investment", "invest")
CONCEPTS = {
    # basics
    "min_amount": [_W("least", "minimum", "min", "lowest", "smallest", "kitne", "kam se kam", "\\d+\\s*(rs|rupees|₹)", "₹\\s*\\d+", "small amount"), SIPW + "|\\b(put|start)"],
    "sip_vs_lumpsum": [_W("all at once", "one[- ]?time", "lump\\s?-?sum", "at once", "in one go", "single payment", "ek saath"), _W("parts", "monthly", "sips?", "instal+ments?", "regular", "options", "difference", "vs")],
    "frequency": [_W("weekly", "daily", "fortnightly", "quarterly", "every week", "every day", "frequenc"), _W("sips?", "possible", "can", "allowed", "option")],
    "sip_date": [_W("date", "tarikh"), _W("change", "choose", "pick", "shift", "move", "badal")],
    "start_sip": [_W("start", "begin", "open", "set ?up", "shuru", "create"), _W("sips?"), _W("how", "kaise", "steps?", "process", "new")],
    "stop_sip": [_W("stop", "cancel", "end", "close", "discontinue", "band", "terminate"), _W("sips?"), _W("charged?", "penalt\\w*", "fees?", "how", "can", "anytime", "allowed", "early", "kaise", "kya")],
    "cancel_effect": [_W("stop", "cancel", "band", "discontinue"), _W("money", "invested", "units", "lose", "investment", "paisa", "corpus", "already")],
    "missed_instalment": [_W("miss\\w*", "fail\\w*", "bounc\\w*", "low balance", "balance (was|is) low", "insufficient", "nahi kata", "not debited", "not deducted", "didn'?t go through", "declined", "balance"),
                          _W("sips?", "instal\\w*", "debit\\w*", "payment", "paisa", "autopay", "mandate", "bank")],
    "pause_skip": [_W("pause\\w*", "skip\\w*", "on hold", "hold", "break", "rok", "temporar\\w*", "stop for"), _W("sips?", "instal\\w*", "months?")],
    "modify_amount": [_W("reduce", "decrease", "increase", "lower", "raise", "change", "modify", "kam", "badha"), _W("amount", "sip amount", "instal\\w*")],
    "tax": [_W("tax\\w*", "ltcg", "stcg", "capital gains?", "short term capital", "long term capital")],
    "nav_cutoff": [_W("allot\\w*", "nav", "units"), _W("late", "later", "delay\\w*", "next day", "a day", "when", "which", "cut[- ]?off", "time")],
    "redemption": [_W("redeem\\w*", "redemption", "withdraw\\w*", "take out", "nikal", "sell"), _W("days?", "how long", "time", "how", "when", "money")],
    "exit_load": [_W("charge\\w*", "fees?", "penalt\\w*", "load", "deduct\\w*"), _W("withdraw\\w*", "redeem\\w*", "sell\\w*", "exit"), _W("before", "early", "within", r"\\d+\\s*(year|month)")],
    "expense_ratio": [_W("fees?", "charges?", "costs?", "expense"), _W("every year", "annual\\w*", "yearly", "ratio", "manage\\w*", "fund (charge|take)")],
    "kyc": [_W("kyc", "know your customer", "verification", "verify")],
    "mandate_time": [_W("mandate", "autopay", "auto pay", "e-?mandate", "nach"), _W("pending", "how long", "time", "days", "approv\\w*", "register\\w*", "stuck")],
    "multiple_sips": [_W("more than one", "multiple", "several", "two", "many", "another"), _W("sips")],
    "returns_guarantee": [_W("fixed", "guarantee\\w*", "assured", "sure shot", "certain"), _W("returns?", "income", "profit")],
    "risk": [_W("lose", "loss", "risk\\w*", "safe", "danger\\w*", "dub", "doob"), _W("sips?", "mutual funds?", "money", "investment")],
    "rupee_cost_avg": [_W("averag\\w*", "average out"), _W("cost", "price", "units", "nav")],
    "compounding": [_W("compound\\w*")],
    "sip_vs_fd": [_W("fd", "fixed deposit", "rd", "recurring deposit", "ppf", "bank deposit", "savings account", "post office")],
    "stp_swp": [_W("stp", "swp", "systematic (transfer|withdrawal)", "transfer plan", "withdrawal plan")],
    "folio_cas": [_W("folio", "cas", "consolidated", "all (my )?(mutual )?funds", "one statement", "cams", "kfintech", "mf ?central", "account statement")],
    "fund_types": [_W("types?", "kinds?", "categor\\w*"), _W("funds?", "mutual funds?")],
    "index_fund": [_W("index funds?", "passive funds?", "nifty 50 fund", "etf")],
    "direct_regular": [_W("direct"), _W("regular")],
    # research
    "q1": [_W("start\\w*", "begin\\w*", "motivat\\w*", "shuru", "first invest\\w*", "get into", "decide to invest"), _W("why", "what makes", "motivat\\w*", "reasons?", "kyun", "expect\\w*", "trigger\\w*")],
    "q2": [_W("behaviou?r", "habits?", "do they do", "change"), _W("after", "later", "months?", "over time", "first few")],
    "q3": [_W("quit\\w*", "stop\\w*", "cancel\\w*", "pause\\w*", "discontinu\\w*", "drop\\w*", "give up", "band", "chhod\\w*", "leave", "abandon\\w*", "reduc\\w*"),
           _W("why", "reasons?", "makes?", "cause\\w*", "lead\\w*", "kyun", "kyu", "what drives", "behind")],
    "q4": [_W("check\\w*", "track\\w*", "monitor\\w*", "look at", "keep looking", "dekh\\w*", "watch\\w*"), _W("investors?", "people", "users", "they", "new", "first")],
    "q5": [_W("confus\\w*", "worr\\w*", "anxious", "scared", "fear\\w*", "unclear", "don'?t understand", "frustrat\\w*")],
    "q6": [_W("outside", "where", "look for", "turn to", "go to", "go for", "who do they ask", "ask"), _W("help", "answers?", "confused", "unsure", "doubt\\w*", "advice", "guidance", "information")],
    "q7": [_W("different", "differ\\w*", "separat\\w*", "distinguish\\w*", "what do .{0,20} have in common", "special about"), _W("keep\\w*", "continu\\w*", "stay\\w*", "going", "stick\\w*", "persist\\w*")],
    "q8": [_W("age", "older", "younger", "young", "income", "salaried", "students?", "self[- ]employed", "freelanc\\w*", "segments?", "gender", "influenc\\w*", "source of money"),
           _W("differ\\w*", "change", "behav\\w*", "compare", "vs", "versus", "affect\\w*", "impact\\w*", "pattern\\w*")],
    "q9": [_W("features?", "want\\w*", "wish\\w*", "asking for", "unmet", "needs?", "request\\w*", "missing", "expect from (the )?app", "improv\\w*"), _W("investors?", "people", "users", "they", "customers?")],
    "metric": [_W("metric", "kpi", "measure of success", "north star", "goal of (the|this) project"), _W("project", "improve", "this", "what", "business")],
    "sources": [_W("data", "sources?", "comments?", "reviews?", "dataset"), _W("use", "used", "collect\\w*", "where", "how many", "how much", "scrap\\w*", "gather\\w*", "analys\\w*", "from")],
    "limitations": [_W("reliable", "reliability", "trust\\w*", "limitation\\w*", "bias\\w*", "caveat\\w*", "weakness\\w*", "how sure", "confidence")],
    "how_it_works": [_W("built", "build", "works?", "made", "pipeline", "architecture", "under the hood", "design\\w*"), _W("engine", "this", "you", "tool", "system")],
    "drop_types": [_W("without (choosing|deciding|wanting)", "involuntar\\w*", "voluntar\\w*", "by mistake", "not by choice", "accidental\\w*", "unintentional\\w*", "passive")],
    "top_opportunity": [_W("fix", "build", "focus", "priorit\\w*", "solve", "work on", "tackle"), _W("first", "most", "groww", "biggest", "top", "main")],
    "sip": [_W("explain", "meaning", "define", "samjha\\w*", "simple words", "simply", "basics of", "kya hota"), _W("sips?")],
    "guardrails": [_W("advice", "abus\\w*", "recommend\\w*", "tips?", "fund names?", "foul", "gali", "personal data", "pan"),
                   _W("stop\\w*", "prevent\\w*", "avoid\\w*", "block\\w*", "never", "guard\\w*", "handle\\w*", "filter\\w*"), _W("engine", "you", "bot", "chat\\w*", "tool", "system", "it")],
    "validation": [_W("validat\\w*", "golden set", "accura\\w*", "agreement", "evidence log", "hand[- ]label\\w*")],
}
RESEARCH_KEYS = {k for k in CONCEPTS if k in RESEARCH}
THIRD_P = re.compile(r"\b(investors?|people|users|customers|log|they|others|comments?|reviews?|first[- ]time)\b", re.I)


def match_concept(q, allow_basics=True):
    """Best topic by concept groups. Returns (topic, kind, score) or (None, None, 0)."""
    s = _norm(q)
    third = bool(THIRD_P.search(s))
    best, score = None, 0
    for k, groups in CONCEPTS.items():
        if not allow_basics and k not in RESEARCH_KEYS:
            continue
        if all(re.search(g, s) for g in groups):
            sc = 10 * len(groups)
            sc += 5 if (k in RESEARCH_KEYS) == third else 0      # questions about other investors favour research topics
            if sc > score:
                best, score = k, sc
    if not best:
        return None, None, 0
    return best, ("research" if best in RESEARCH_KEYS else "basics"), score
