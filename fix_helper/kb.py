"""Checked fix steps for each failure reason. The AI never writes or edits these; it only picks the reason.
Every step is either sourced (S1..S8) or labelled 'General guidance'. Sources accessed 2 Nov 2026."""

SOURCES = {
    "S1": ("Groww Help: Why did my installment fail", "https://groww.in/help/mutual-funds/order/why-did-my-installment-fail--25"),
    "S2": ("Groww Help: What are ECS charges", "https://groww.in/help/mutual-funds/mf-autopay/what-are-ecs-charges--96"),
    "S3": ("Groww Help: Can I pause SIP for next month", "https://groww.in/help/mutual-funds/order/can-i-pause-sip-for-next-month"),
    "S5": ("Business Standard: RBI raises recurring-payment limit for mutual funds (press report, Dec 2023)", "https://business-standard.com/finance/news/automatic-payment-limit-through-upi-raised-to-rs-1-lakh-says-rbi-123121201097_1.html"),
    "S6": ("Zerodha Support: AMC SIPs cancelled after 3 failed installments", "https://support.zerodha.com/category/mutual-funds/features-on-coin/systematic-investment-plan/articles/amc-sips-cancelled"),
    "S8": ("Kotak Mutual Fund: Why did my SIP installment fail", "https://www.kotakmf.com/Information/blogs/why-did-sip-installment-failed"),
}
GROWW_HELP = "https://groww.in/help/mutual-funds/order/why-did-my-installment-fail--25"
G = None  # marks general guidance (not from an official page)

REASONS = {
    "still_processing": {
        "title": "Your installment is still being processed",
        "means": "The payment has started but isn't confirmed yet, so the installment isn't complete.",
        "now": [("Check your bank statement to see whether the amount was debited.", G),
                ("If nothing was debited, wait for the status to update in the app.", G),
                ("If the status doesn't change after a few working days, contact Groww support with the date and amount.", G)],
        "next": [("Keep the balance ready in your linked account 4 days before the installment date.", "S1")],
    },
    "autopay_not_setup": {
        "title": "AutoPay isn't set up or isn't approved yet",
        "means": "Your SIP has no working permission to debit your bank, so the installment couldn't be collected.",
        "now": [("Pay this installment with “Pay one-time”: My SIPs → choose the SIP → Pay one-time. NAV applies from when the payment completes.", "S1"),
                ("Set up AutoPay, or link the SIP to an AutoPay that's already approved.", "S1"),
                ("A new AutoPay can take a few working days to be approved.", "S8")],
        "next": [("Check that the SIP shows a linked, approved AutoPay before the next date.", G)],
    },
    "mandate_stopped": {
        "title": "Your AutoPay mandate has expired, been paused or cancelled",
        "means": "The permission your bank gave for automatic debits is no longer active.",
        "now": [("Pay this installment with “Pay one-time”.", "S1"),
                ("Create a new AutoPay mandate and link the SIP to it.", "S8"),
                ("If you didn't cancel it yourself, ask your bank why it stopped.", G)],
        "next": [("Check your AutoPay's status in the app before each installment date.", G)],
    },
    "above_limit": {
        "title": "The amount is above your AutoPay limit",
        "means": "The installment is larger than the maximum your AutoPay allows, so the bank declines it. This often happens right after increasing a SIP.",
        "now": [("Pay this installment with “Pay one-time”.", "S1"),
                ("Check the limit on your AutoPay in the app.", G),
                ("If the new amount is above it, update or set up an AutoPay with a higher limit before the next date.", G)],
        "next": [("Before increasing a SIP, compare the new amount with your AutoPay limit. Use “Check a SIP change first” here.", G)],
        "context": ("Context: RBI allows recurring mutual fund debits of up to ₹1,00,000 per transaction without an extra authentication step.", "S5"),
    },
    "low_balance": {
        "title": "There wasn't enough balance on the debit day",
        "means": "Your bank account didn't have enough money when the debit was attempted.",
        "now": [("Pay this installment with “Pay one-time”. NAV applies from when the payment completes.", "S1"),
                ("Groww doesn't charge for a failed SIP order; your bank may charge an ECS rejection fee.", "S2")],
        "next": [("Keep the amount in your linked account 4 days before the installment date.", "S1"),
                 ("If you can't fund a month, you can skip an installment: Edit SIP → Skip Installment.", "S3")],
    },
    "bank_declined": {
        "title": "Your bank declined the debit or had a technical error",
        "means": "The bank or payment network rejected the debit for a reason other than balance, such as a technical issue or bank details that don't match.",
        "now": [("Pay this installment with “Pay one-time” if the option is shown.", "S1"),
                ("Check that your AutoPay is still active and your bank details are correct.", "S8"),
                ("If it happens again, ask your bank for the decline reason.", G)],
        "next": [("Keep your KYC and bank details up to date.", "S8")],
    },
    "app_error": {
        "title": "Something went wrong in the app",
        "means": "The app couldn't complete the payment or setup step, for example an error message or a page that won't load.",
        "now": [("Update the app and try again later.", G),
                ("If the installment was missed, pay it with “Pay one-time”.", "S1"),
                ("If the error continues, contact Groww support and describe what you saw.", G)],
        "next": [("After any change to a SIP, check that the next installment shows as completed.", G)],
    },
    "cancelled_after_failures": {
        "title": "Your SIP was cancelled after repeated failed installments",
        "means": "After 3 consecutive failed installments, the fund house cancels the SIP.",
        "now": [("Check the SIP's status in the app and any message from the fund house.", G),
                ("If you want to keep investing regularly, set up a new SIP with a working AutoPay.", G)],
        "next": [("Fix a failed installment before the next one; one successful debit resets the count.", "S8")],
        "context": ("Since April 2024, fund houses cancel a SIP after 3 consecutive failed installments.", "S6"),
    },
}
LABELS = {"still_processing": "Still processing", "autopay_not_setup": "AutoPay not set up or not approved",
          "mandate_stopped": "Mandate expired, paused or cancelled", "above_limit": "Amount above the AutoPay limit",
          "low_balance": "Not enough balance", "bank_declined": "Bank declined or technical error", "app_error": "App-side error",
          "cancelled_after_failures": "SIP cancelled after repeated failures", "unclear": "Unclear / not a failure"}
