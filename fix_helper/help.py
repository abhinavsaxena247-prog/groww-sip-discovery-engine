"""Help answers for questions that are not a failed installment: SIP basics, where to find your own SIP details,
contacting support, managing a SIP, and starting one. Every line is sourced (Groww Help, accessed 5 Nov 2026) or
marked general guidance (None). No fund names, no advice on what to buy, stop or continue, no urgency."""
import re

H = {
    "S1": ("Groww Help: Why did my installment fail", "https://groww.in/help/mutual-funds/order/why-did-my-installment-fail--25"),
    "S2": ("Groww Help: What are ECS charges", "https://groww.in/help/mutual-funds/mf-autopay/what-are-ecs-charges--96"),
    "S3": ("Groww Help: Can I pause SIP for next month", "https://groww.in/help/mutual-funds/order/can-i-pause-sip-for-next-month"),
    "S9": ("Groww Help: How to set up AutoPay", "https://groww.in/help/mutual-funds/mf-autopay/how-to-set-up-autopay--45"),
    "S10": ("Groww Help: How to change the AutoPay linked to a SIP", "https://groww.in/help/mutual-funds/discoverable/how-to-change-my-autopay-linked-to-an-sip--23"),
    "S11": ("Groww Help: How to contact Groww customer care", "https://groww.in/help/my-account/searchable/how-to-contact-groww-customer-care--74"),
    "S12": ("Groww Help: How to skip a SIP instalment", "https://groww.in/help/mutual-funds/mf-sip/how-to-skip-an-sip-instalment--79"),
    "S13": ("Groww Help: How to cancel my SIP", "https://groww.in/help/mutual-funds/mf-sip/how-to-cancel-my-sip"),
    "S14": ("Groww Help: How to change SIP date or amount", "https://groww.in/help/mutual-funds/mf-sip/how-to-change-sip-date-or-amount"),
    "S15": ("Groww Help: How to start a SIP on Groww", "https://groww.in/help/mutual-funds/mf-sip/how-to-start-a-sip-on-groww"),
    "S16": ("Groww Help: My next SIP due date is 2 months away, why?", "https://groww.in/help/mutual-funds/order/my-next-sip-due-date-is-2-months-away-why"),
    "S6": ("Zerodha Support: AMC SIPs cancelled after 3 failed installments", "https://support.zerodha.com/category/mutual-funds/features-on-coin/systematic-investment-plan/articles/amc-sips-cancelled"),
}
G = None

TOPICS = {
    "faq_sip": {
        "title": "What a SIP is",
        "lines": [("A SIP (systematic investment plan) invests a fixed amount in a mutual fund automatically, on the same date each month.", G),
                  ("The money is debited from your bank through AutoPay (a standing permission your bank approves), so you don't pay by hand each month.", "S15"),
                  ("On Groww, SIPs are monthly. The first and second installments need at least 30 days between them, so the second one can be about two months after you start.", "S16")],
        "more": "If an installment fails, describe what happened on the first page and I'll help you fix it.",
    },
    "faq_fail_effect": {
        "title": "What happens when a SIP installment fails",
        "lines": [("The money you've already invested stays invested; a failed installment only means that month's amount wasn't invested.", G),
                  ("Groww doesn't charge you for a failed installment. Your bank may charge a return fee for a failed auto-debit.", "S1"),
                  ("Bank charges for a failed debit are set by your bank, not by Groww.", "S2"),
                  ("If 3 installments in a row fail or are skipped, the SIP is cancelled automatically. One successful installment resets that count.", "S12"),
                  ("You can pay a missed installment with “Pay one-time”: My SIPs → choose the SIP → Pay one-time.", "S1")],
        "more": "To find out why yours failed and how to fix it, describe what happened on the first page.",
    },
    "account": {
        "title": "Your own SIP details are in the Groww app",
        "lines": [("I can't see your account, and I'll never ask for your login, PAN or account numbers.", G),
                  ("To see your next installment: Mutual Funds → SIPs (My SIPs) → choose the SIP. The upcoming installment is shown there.", "S12"),
                  ("For a new SIP, the second installment can be about two months after the first, because of a 30-day minimum gap.", "S16"),
                  ("Your holdings and amounts are under Mutual Funds in the app.", G)],
        "more": "If an installment didn't go through, describe what happened on the first page.",
    },
    "support": {
        "title": "How to reach Groww support",
        "lines": [("Groww customer care: +91 9108800000, listed as available 24×7.", "S11"),
                  ("Head of customer care: 080 4616 1210, Monday to Friday, 9 AM to 5 PM (for escalations).", "S11"),
                  ("You can also use Help or Contact Us inside the Groww app.", G),
                  ("Keep the SIP name, the installment date and what the app shows ready. Never share your PIN, OTP or password with anyone.", G)],
        "more": "Many failed installments can be fixed in a few taps without calling: describe what happened on the first page.",
    },
    "manage_pause": {
        "title": "How to skip or pause an installment",
        "lines": [("My SIPs → choose the SIP → Skip next to the upcoming installment (or Edit SIP → Skip Installment) → confirm.", "S12"),
                  ("If the next installment is within 2 days, the skip applies from the one after.", "S12"),
                  ("Skipping or missing 3 installments in a row cancels the SIP automatically.", "S12")],
        "more": None,
    },
    "manage_cancel": {
        "title": "How to cancel (stop) a SIP",
        "lines": [("Mutual Funds → SIPs tab → choose the SIP → Cancel SIP (top right) → choose a reason → Cancel SIP to confirm.", "S13"),
                  ("You can't cancel if the next installment is due within 7 days; that one needs to be paid first.", "S13"),
                  ("Cancelling stops future installments. What you've already invested stays invested until you redeem it.", "S13"),
                  ("Cancelling can't be undone; you can start a new SIP later.", "S13")],
        "more": "Whether to stop is your decision. If you're stopping because payments keep failing, the first page can help you find out why.",
    },
    "manage_change": {
        "title": "How to change a SIP's amount or date",
        "lines": [("Mutual Funds → SIPs tab → choose the SIP → Change Amount/Date → enter the new amount or date → confirm.", "S14"),
                  ("If the next installment is within 2 working days, the change applies from the one after.", "S14"),
                  ("Before raising the amount, check it fits within your AutoPay limit, or the next installment can fail. Use “Check a change”.", G)],
        "more": None,
    },
    "manage_autopay": {
        "title": "How to set up or change AutoPay",
        "lines": [("Set up: profile icon → Bank and AutoPay → choose your bank → Set Up AutoPay. Bank approval takes 2 to 7 working days.", "S9"),
                  ("Link it to a SIP: SIPs → choose the SIP → Change AutoPay → pick an approved AutoPay.", "S10")],
        "more": None,
    },
    "greeting": {
        "title": "Hi! I help when a SIP installment doesn't go through",
        "lines": [("Tell me what happened in your own words, or paste the app status or bank SMS. I'll check what I understood with you and show the exact fix.", G),
                  ("I can also explain what a SIP is, how to skip, change or cancel one, how to start one, and how to reach Groww support.", G)],
        "more": None,
    },
    "vent": {
        "title": "Sorry this has been frustrating",
        "lines": [("I can help you find out what went wrong with a SIP payment and how to fix it. Tell me what the app shows or what happened.", G),
                  ("If you'd rather talk to someone: Groww customer care, +91 9108800000, listed as available 24\u00d77.", "S11")],
        "more": None,
    },
    "start": {
        "title": "Start a SIP",
        "lines": [],  # the Start a SIP page holds this content
        "more": None,
    },
}

def _r(p):
    return re.compile(p, re.I)

# Rule-based intent routing (English and Hinglish). Order matters: first match wins.
RULES = [
    ("greeting", _r(r"^\s*(hi+|hello+|hey+|namaste|namaskar|good (morning|afternoon|evening)|thanks?( you)?|thank u|thx|ok(ay)?|cool|great|bye)\s*[!.\s]*$")),
    ("start", _r(r"\b(start|begin|shuru|open|create|new)\w*\b.{0,25}\b(sip|invest\w*)\b|\b(begin|start)\w* investing\b|\binvest(ing)? (kaise|karna)\b|\bsip (kaise )?(shuru|start)")),
    ("support", _r(r"customer ?(care|support|service)|\bhelp ?line\b|\bagent\b|\bsupport team\b|talk to (a |someone|somebody|human|person)|speak to|\bcall (you|groww|support)\b|\bcontact (groww|support|you)\b|complain|complaint|grievance|\bescalat")),
    ("manage_cancel", _r(r"\b(how|want|wanna|can i|kaise|karna|karu|karun|need to|help me|steps)\b.{0,30}\b(cancel|stop|band|close|discontinue)\w*\b|\b(stop|cancel) (all )?(my )?sips?\b")),
    ("manage_pause", _r(r"\b(how|want|can i|kaise|karna|need to|help me|steps)\b.{0,30}\b(pause|skip|hold)\w*\b|\b(pause|skip) (my |next |this )?(sip|instal+ment|month)")),
    ("manage_autopay", _r(r"\b(how|want|can i|kaise|karna|need to|help me|steps)\b.{0,30}\b(set ?up|create|add|change|link)\b.{0,15}\b(autopay|auto pay|mandate|e-?nach)\b")),
    ("manage_change", _r(r"\b(how|want|can i|kaise|karna|need to|help me|steps)\b.{0,30}\b(increase|decrease|reduce|change|modify|edit|step.?up|badha\w*)\b|^\s*change (sip )?(date|amount)")),
    ("account", _r(r"\b(next|agli|agla|upcoming)\b.{0,25}\b(sip|instal+ment|due|debit|kab)\b|when (is|will) my (next )?(sip|instal+ment)|\bkab (kategi|katega|aayegi|hogi)\b|\bmy (balance|portfolio|holdings|returns)\b|how much (money )?(do i have|is in my|have i invested)|show my")),
    ("faq_fail_effect", _r(r"(what happens|kya hoga|will i lose|lose (my|all)|penalty|\bfine\b|charges?)\b.{0,40}\b(fail|miss|bounce|not paid|nahi hu)|\b(fail|miss|bounce|nahi hu|nahi kat|didn.?t go through|not go through)\w*\b.{0,40}\b(what happens|kya hoga|penalty|fine|charge|lose)")),
    ("faq_sip", _r(r"\bwhat (is|are) (a |an |the )?(sip|nav|mandate|autopay|auto pay|e-?nach|mutual funds?|sips)\b|\b(sip|nav|mandate|autopay)\b.{0,12}\bkya (hota|hai|hoti)|how (does|do) (a )?sips? work|meaning of (sip|nav)")),
    ("vent", _r(r"\b(useless|worst|pathetic|bakwas|bekar|rubbish|stupid|wtf|hate|terrible|horrible|f\*+k?|f\*\*\*)\b")),
]

def route(text):
    t = text.strip()
    for name, rx in RULES:
        if rx.search(t):
            return name
    return None

FAILURE_WORDS = _r(r"fail|bounce|declin|reject|unsuccessful|not deducted|didn.?t deduct|missed|miss (ho|kr|kar)|pending|in progress|cancel+ed|insufficient|not enough|mandate|autopay|auto pay|debit")
