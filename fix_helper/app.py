"""NL-Groww SIP Fix Helper (independent concept, not a Groww product). Streamlit app built from the Figma design."""
import html, json, os, sys
import streamlit as st
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from fix_helper import core  # noqa: E402
from fix_helper.kb import REASONS, SOURCES, GROWW_HELP  # noqa: E402
from fix_helper import help as HELP  # noqa: E402

st.set_page_config(page_title="SIP Fix Helper · NL-Groww concept", page_icon=":material/build:", layout="centered")
CSS = """
<style>
html, body, p, li, label, input, textarea, button, h1, h2, h3, .stMarkdown { font-family: "Inter", system-ui, sans-serif; }
[data-testid="stIconMaterial"] { font-family: "Material Symbols Rounded" !important; }
[data-testid="stDecoration"] { display:none; }
.block-container { padding-top: 3.2rem; max-width: 820px; }
h1, h2, h3 { color:#44475B !important; letter-spacing:-.01em; }
p, li { color:#44475B; }
.bar { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; border:1px solid #E7E8EC; border-radius:12px; padding:10px 14px; }
.bar .logo { display:flex; gap:10px; align-items:center; font-weight:600; color:#44475B; }
.bar .logo b { width:16px; height:16px; border-radius:50%; background:#04B488; display:inline-block; }
.tag { font-size:.78rem; color:#00664C; background:#E5F7F1; border-radius:99px; padding:3px 10px; font-weight:500; }
.notice { background:#F0FAF6; border-left:3px solid #04B488; border-radius:8px; padding:8px 12px; font-size:.86rem; color:#44475B; margin:10px 0 4px; }
.msg { background:#F2F5F7; border-radius:10px; padding:10px 14px; font-size:.95rem; }
.msg small { display:block; font-size:.72rem; letter-spacing:.06em; text-transform:uppercase; color:#55586A; margin-bottom:4px; }
.card { border:1.5px solid #04B488; border-radius:14px; padding:16px 18px; margin-top:12px; }
.card.fb { border-color:#55586A; border-style:dashed; }
.lab { font-size:.72rem; letter-spacing:.06em; text-transform:uppercase; color:#55586A; }
.reason { font-size:1.45rem; font-weight:700; color:#44475B; margin:2px 0 6px; line-height:1.25; }
.conf { display:inline-block; background:#027F5F; color:#fff; border-radius:99px; padding:3px 12px; font-size:.82rem; font-weight:600; }
.conf.medium { background:#fff; color:#027F5F; border:1.5px solid #027F5F; }
.why { font-size:.9rem; color:#44475B; margin:8px 0 10px; }
.grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px; }
.blk { background:#F2F5F7; border-radius:10px; padding:10px 12px; font-size:.9rem; min-width:0; }
.blk h4 { margin:0 0 6px; font-size:.95rem; color:#027F5F; }
.blk h4 { padding:0 !important; }
.blk li, .blk ol, .blk ul { font-size:.9rem !important; line-height:1.45; margin-bottom:4px; }
.blk ol, .blk ul { margin:0; padding-left:18px; }
.src { font-size:.78rem; color:#55586A; }
.src a, .blk a { color:#027F5F; }
.gg { font-size:.72rem; color:#55586A; border:1px solid #C9CCD5; border-radius:99px; padding:0 6px; margin-left:4px; white-space:nowrap; }
.checks { margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }
.chk { font-size:.78rem; border-radius:99px; padding:3px 10px; background:#E5F7F1; color:#00664C; }
.chk.no { background:#F2F5F7; color:#44475B; }
.risk { font-size:.78rem; color:#55586A; margin-top:18px; }
.stButton button { border-radius:8px; border:1px solid #027F5F !important; color:#027F5F !important; background:#fff !important; font-weight:500; }
.stButton button[kind="primary"] { background:#027F5F !important; color:#fff !important; }
.stButton button[kind="primary"] p { color:#fff !important; }
.stButton button:hover { background:#E5F7F1 !important; }
.stButton button[kind="primary"]:hover { background:#00664C !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:#E5F7F1 !important; }
.tile { border:1px solid #E7E8EC; border-radius:12px; padding:12px 14px; }
.tile .v { font-size:1.6rem; font-weight:700; color:#027F5F; }
.tile .t { font-size:.82rem; color:#55586A; }
</style>"""
NOTICE = "Independent concept by a NextLeap student. Not affiliated with Groww. Not investment advice: it explains what happened to a payment and never recommends a fund or tells you whether to continue."
RISK = "Mutual fund investments are subject to market risks, read all scheme related documents carefully."
EXAMPLES = ["My SIP failed this month and I don't know why",
            "I increased my SIP amount last week and now the autopay failed",
            "Your SIP installment is in progress. We will update you once the payment is confirmed.",
            "autopay fail ho gaya, bank mein balance kam tha"]

def header():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"<div class='bar'><div class='logo'><b></b>SIP Fix Helper</div><span class='tag'>Independent concept · Not investment advice</span></div>"
                f"<div class='notice'>{NOTICE}</div>", unsafe_allow_html=True)

def esc(s):
    return html.escape(str(s))

def steps_html(items):
    out = []
    for text, src in items:
        if src:
            name, url = SOURCES[src]
            out.append(f"<li>{esc(text)} <a href='{url}' target='_blank' title='{esc(name)}'>[source]</a></li>")
        else:
            out.append(f"<li>{esc(text)} <span class='gg'>general guidance</span></li>")
    return "".join(out)

def checks_html(checks):
    tick, dot = "\u2713 ", "\u25cf "
    return "<div class='checks'>" + "".join("<span class='chk" + ("" if ok else " no") + "'>" + (tick if ok else dot) + esc(t) + "</span>" for t, ok in checks) + "</div>"

def show_result(text, r, echo=True, how=""):
    if echo:
        st.markdown(f"<div class='msg'><small>Your message</small>“{esc(text)}”</div>", unsafe_allow_html=True)
    if r["kind"] == "answer":
        kb = REASONS[r["reason"]]
        why = f"Why we think so: your message says “{esc(r['evidence'])}”." if r.get("evidence") else esc(how)
        ctx = ""
        if kb.get("context"):
            t, s = kb["context"]; name, url = SOURCES[s]
            ctx = f"<p class='src'>{esc(t)} <a href='{url}' target='_blank'>[source]</a></p>"
        conf = r["confidence"]
        st.markdown(f"""<div class='card'><div class='lab'>Likely reason</div><div class='reason'>{esc(kb['title'])}</div>
<span class='conf'>Reason found</span>
<div class='why'>{why}</div>
<div class='grid'><div class='blk'><h4>What it means</h4>{esc(kb['means'])}</div>
<div class='blk'><h4>What to do now</h4><ol>{steps_html(kb['now'])}</ol></div>
<div class='blk'><h4>How to avoid it next time</h4><ul>{steps_html(kb['next'])}</ul></div></div>
{ctx}<p class='src'>The AI only notes what you said; fixed rules pick the reason; the steps are written in advance from official help pages.</p>
{checks_html(r['checks'])}</div>""", unsafe_allow_html=True)
        st.caption("This explains your payment, not your investment. It won't suggest a fund or tell you whether to continue.")
    elif r["kind"] == "fallback":
        st.markdown(f"""<div class='card fb'><div class='lab'>Not sure</div><div class='reason'>I can't tell the reason yet, so I won't guess</div>
<div class='why'>Three checks cover most failed installments:<ol><li>In the app, open My SIPs and check the installment's status and any reason shown.</li>
<li>Check your AutoPay is active and its limit covers the installment amount.</li>
<li>Make sure the linked bank account had enough balance on the debit date.</li></ol>
You can pay a missed installment with “Pay one-time”. Groww's help page explains the common reasons.</div>
<p><a href='{GROWW_HELP}' target='_blank'>Open Groww help: why did my installment fail</a></p>
<p class='src'>Tip: paste the exact status or SMS text if you have it. You can also contact Groww support from the app's help section.</p>
{checks_html(r['checks'])}</div>""", unsafe_allow_html=True)
    elif r["kind"] == "decline":
        if r["why"] == "advice":
            body = "I can't advise on funds, returns, or whether to stop or continue a SIP. I can explain why an installment failed and how to fix it."
        elif r["why"] == "off_topic":
            body = ("I can only help with SIP payments and SIP basics. Try: \u201cMy SIP failed this month\u201d, \u201cWhat is a SIP?\u201d, "
                    "\u201cHow do I skip an installment?\u201d or \u201cHow do I contact Groww support?\u201d.")
        else:
            body = r["why"]
        st.markdown(f"<div class='card fb'><div class='lab'>Can't help with this</div><div class='reason'>That's outside what I do</div><div class='why'>{esc(body)}</div>{checks_html(r['checks'])}</div>", unsafe_allow_html=True)
    elif r["kind"] == "help":
        show_help(r)
    else:
        st.markdown(f"<div class='card fb'><div class='lab'>Check your message</div><div class='why'>{esc(r['why'])}</div>{checks_html(r['checks'])}</div>", unsafe_allow_html=True)
    if r.get("mode") == "basic":
        st.caption("The AI is busy right now, so this used simple rules. Rules only answer when the message states the cause clearly.")

FACT_LABEL = {
    "app_status": ("App shows", {"in_progress": "In progress / pending", "failed": "Failed", "sip_cancelled": "SIP cancelled"}),
    "debited": ("Money taken", {"yes": "Yes", "no": "No", "refunded": "Taken, then returned"}),
    "recent_change": ("Changed the SIP recently", {"yes": "Yes", "no": "No"}),
    "stated_cause": ("Reason given", {"low_balance": "Not enough balance", "over_limit": "Above the AutoPay limit", "mandate_not_ready": "AutoPay not set up or approved",
                                      "mandate_stopped": "AutoPay expired or cancelled", "bank_error": "Bank or technical error", "app_error": "App error"}),
}

def facts_html(facts, ev, answers):
    rows = []
    for k, (name, vals) in FACT_LABEL.items():
        v = answers.get(k, facts.get(k))
        if v in vals:
            src = ("you confirmed" if v == facts.get(k) else "you told me") if k in answers else (f"from your message: \u201c{esc(ev.get(k, ''))}\u201d" if ev.get(k) else "from your message")
            rows.append(f"<li><b>{esc(name)}:</b> {esc(vals[v])} <span class='src'>({src})</span></li>")
        elif k in answers:
            shown = "no reason given" if v == "none" else "not sure"
            who = "you confirmed" if v == facts.get(k) else "you told me"
            rows.append(f"<li><b>{esc(name)}:</b> {shown} <span class='src'>({who})</span></li>")
    return "<ul>" + "".join(rows) + "</ul>" if rows else "<p class='src'>Nothing specific yet.</p>"

def start_over():
    reset_flow()
    st.session_state.fx_text = ""

def reset_flow():
    for k in ("fx_read", "fx_answers", "fx_asked", "fx_confirmed", "fx_qn"):
        st.session_state.pop(k, None)

def help_lines_html(lines):
    out = []
    for text, src in lines:
        if src:
            name, url = HELP.H[src]
            out.append(f"<li>{esc(text)} <a href='{url}' target='_blank' title='{esc(name)}'>[source]</a></li>")
        else:
            out.append(f"<li>{esc(text)} <span class='gg'>general guidance</span></li>")
    return "<ul>" + "".join(out) + "</ul>"

def show_help(r):
    t = HELP.TOPICS[r["topic"]]
    if r["topic"] == "start":
        st.markdown("<div class='card'><div class='lab'>Start a SIP</div><div class='reason'>Want to start a SIP?</div>"
                    "<div class='why'>The Start a SIP page shows Groww's steps and how to set it up so installments don't fail. It never suggests a fund.</div></div>", unsafe_allow_html=True)
        st.page_link(PAGE_START, label="Open Start a SIP", icon=":material/rocket_launch:")
        return
    more = f"<p class='src'>{esc(t['more'])}</p>" if t.get("more") else ""
    st.markdown(f"<div class='card'><div class='lab'>Answer</div><div class='reason'>{esc(t['title'])}</div>"
                f"<div class='blk'>{help_lines_html(t['lines'])}</div>{more}{checks_html(r['checks'])}</div>", unsafe_allow_html=True)
    if r.get("can_continue"):
        if st.button("Find out why my installment failed", key="help_continue", use_container_width=True):
            text = st.session_state.fx_read[0]
            with st.spinner("Reading your message\u2026"):
                st.session_state.fx_read = (text, core.read_facts(text, skip_route=True))
            st.session_state.fx_answers, st.session_state.fx_asked = {}, []
            st.rerun()

GOOD_TO_KNOW = [("Money you've already invested stays invested; only this month's amount wasn't invested.", None),
                ("Groww doesn't charge for a failed installment; your bank may charge a return fee.", "S1"),
                ("3 failed or skipped installments in a row cancel the SIP automatically.", "S12")]

def page_helper():
    header()
    st.title("What happened to my SIP installment?")
    st.write("Tell me in your own words, or paste the app status or bank SMS (English or Hinglish). "
             "I'll show what I understood for you to check, ask up to 3 quick questions for anything missing, then show the fix.")
    st.caption("Don't paste PAN, account or phone numbers. Nothing is stored.")
    if "fx_text" not in st.session_state:
        st.session_state.fx_text = ""
    cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES):
        if cols[i % 2].button(ex if len(ex) < 60 else ex[:57] + "\u2026", key=f"ex{i}", use_container_width=True):
            st.session_state.fx_text = ex
            reset_flow()
    text = st.text_area("What happened?", key="fx_text", height=100, max_chars=800, placeholder="For example: my SIP failed this month and I don't know why")
    b1, b2 = st.columns([3, 1])
    if b1.button("Continue", type="primary", use_container_width=True) and text.strip():
        reset_flow()
        with st.spinner("Reading your message\u2026"):
            st.session_state.fx_read = (text, core.read_facts(text))
        st.session_state.fx_answers, st.session_state.fx_asked = {}, []
    b2.button("Start over", key="clear", use_container_width=True, on_click=start_over)
    if not st.session_state.get("fx_read"):
        st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)
        return
    text, r = st.session_state.fx_read
    st.markdown(f"<div class='msg'><small>Your message</small>\u201c{esc(text)}\u201d</div>", unsafe_allow_html=True)
    if r["kind"] != "facts":
        show_result(text, r, echo=False)
        st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)
        return
    answers, asked = st.session_state.fx_answers, st.session_state.fx_asked
    if not st.session_state.get("fx_confirmed"):
        st.markdown("<div class='lab' style='margin-top:14px'>Step 1 \u00b7 Check what I understood</div>"
                    "<div class='reason' style='font-size:1.15rem'>Is this right? Change anything I got wrong.</div>", unsafe_allow_html=True)
        picks = {}
        for f in core.CONFIRM_FACTS:
            q, opts = core.QUESTIONS[f]
            codes = [c for c, _ in opts]
            ai_val = r["facts"].get(f)
            idx = codes.index(ai_val) if ai_val in codes else codes.index("not_said")
            ev = r["evidence"].get(f)
            if ev:
                hint = f"I read this from your message: \u201c{ev}\u201d"
            elif f == "stated_cause":
                hint = "Your message doesn't name a reason. Pick one if the app or your bank SMS gives it."
            else:
                hint = "Your message doesn't say, so I picked Not sure. Change it if you know."
            picks[f] = st.radio(q, codes, index=idx, format_func=dict(opts).get, key=f"cf_{f}", help=None)
            st.caption(hint)
        if st.button("Looks right, continue", type="primary", use_container_width=True, key="cf_go"):
            for f, v in picks.items():
                answers[f] = v
                asked.append(f)
            st.session_state.fx_confirmed = True
            st.session_state.fx_qn = 0
            st.rerun()
        st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)
        return
    merged = dict(r["facts"]); merged.update(answers)
    kind, val = core.decide(merged, skip=set(asked))
    if kind == "ask" and st.session_state.get("fx_qn", 0) >= core.MAX_QUESTIONS:
        kind, val = "fallback", None
    st.markdown(f"<div class='card fb'><div class='lab'>What I understood</div>{facts_html(r['facts'], r['evidence'], answers)}</div>", unsafe_allow_html=True)
    if kind == "ask":
        q, opts = core.QUESTIONS[val]
        st.markdown(f"<div class='lab' style='margin-top:14px'>Question {st.session_state.get('fx_qn', 0) + 1} of up to {core.MAX_QUESTIONS}</div><div class='reason' style='font-size:1.15rem'>{esc(q)}</div>", unsafe_allow_html=True)
        oc = st.columns(2)
        for i, (code, label) in enumerate(opts):
            if oc[i % 2].button(label, key=f"q_{val}_{code}", use_container_width=True):
                answers[val] = code
                asked.append(val)
                st.session_state.fx_qn = st.session_state.get("fx_qn", 0) + 1
                st.rerun()
        st.caption("Not sure is a fine answer. You can check the status under My SIPs in the app, and your bank SMS.")
    elif kind == "reason":
        res = {"kind": "answer", "reason": val, "label": core.LABELS.get(val, val), "evidence": "",
               "confidence": "medium", "mode": r.get("mode"),
               "checks": r["checks"] + [("You checked what I understood", True), ("Reason picked by fixed rules from the facts above", True), ("Fix steps from checked sources", True), ("Output guardrails passed", True)]}
        show_result(text, res, echo=False, how="Based on the facts above" + (" and your answers." if answers else "."))
        st.markdown(f"<div class='blk' style='margin-top:10px'><h4>Good to know</h4>{help_lines_html(GOOD_TO_KNOW)}</div>", unsafe_allow_html=True)
    else:
        show_result(text, {"kind": "fallback", "checks": r["checks"] + [("Not enough facts to name a reason, so no guess", True)], "mode": r.get("mode")}, echo=False)
    if r.get("advice_note"):
        st.caption("You also asked for an opinion on funds or returns. I can't advise on that; this covers the payment only.")
    if r.get("mode") == "basic":
        st.caption("The AI is busy right now, so simple rules read your message. The questions still work.")
    st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)

def page_change():
    header()
    st.title("Check a SIP change first")
    st.write("Planning to increase a SIP or change its date? Check it against your AutoPay limit so the next installment doesn't fail.")
    c1, c2 = st.columns(2)
    amt = c1.number_input("New installment amount (₹)", min_value=0, step=500, value=0)
    lim = c2.number_input("Your AutoPay limit (₹), if you know it", min_value=0, step=1000, value=0, help="Find it in the app under your AutoPay details. Leave 0 if unsure.")
    st.radio("AutoPay type", ["UPI AutoPay", "Bank mandate (e-NACH)", "Not sure"], horizontal=True, key="cc_type")
    if st.button("Check this change", type="primary"):
        kind, msg = core.change_check(amt, lim or None)
        label = {"ok": "✓ Likely fine", "close": "● Likely fine, but close", "exceeds": "▲ May exceed your limit", "unsure": "? Not sure"}[kind]
        st.markdown(f"<div class='card{' fb' if kind in ('unsure',) else ''}'><div class='reason'>{esc(label)}</div><div class='why'>{esc(msg)}</div>"
                    "<p class='src'>Rules only: this compares the numbers you enter. It never quotes a current limit as fact.</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)

def page_start():
    header()
    st.title("Start a SIP")
    st.write("Groww's steps to start a SIP, plus a set-up checklist so your installments go through from the first month. "
             "Which fund to choose is your decision; this page never suggests one.")
    st.markdown(f"""<div class='card'><div class='lab'>Steps in the Groww app</div><div class='blk'><ol>
<li>From Home, open Mutual Funds and tap Explore. <a href='{HELP.H["S15"][1]}' target='_blank'>[source]</a></li>
<li>Find the fund you've chosen and tap Start SIP. <a href='{HELP.H["S15"][1]}' target='_blank'>[source]</a></li>
<li>Enter the amount and choose the monthly date. <a href='{HELP.H["S15"][1]}' target='_blank'>[source]</a></li>
<li>Pay the first installment with UPI or net banking. <a href='{HELP.H["S15"][1]}' target='_blank'>[source]</a></li>
<li>Complete AutoPay (OTP or form) so later installments are debited automatically. <a href='{HELP.H["S15"][1]}' target='_blank'>[source]</a></li>
</ol></div></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class='card'><div class='lab'>Set it up so it doesn't fail</div><div class='blk'><ul>
<li>Pick a date when your linked account usually has the money, for example a few days after your salary arrives. <span class='gg'>general guidance</span></li>
<li>Keep the balance ready 4 days before the installment date. <a href='{SOURCES["S1"][1]}' target='_blank'>[source]</a></li>
<li>Set an AutoPay limit above your planned amount, with room if you plan to increase it later. <span class='gg'>general guidance</span></li>
<li>Check AutoPay shows as approved; bank approval takes 2 to 7 working days. <a href='{HELP.H["S9"][1]}' target='_blank'>[source]</a></li>
<li>Expect the second installment about two months after the first: there's a 30-day minimum gap. <a href='{HELP.H["S16"][1]}' target='_blank'>[source]</a></li>
</ul></div></div>""", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    amt = c1.number_input("Planned monthly amount (\u20b9)", min_value=0, step=500, value=0, key="st_amt")
    lim = c2.number_input("AutoPay limit you'll set (\u20b9), if you know it", min_value=0, step=1000, value=0, key="st_lim")
    if st.button("Check my set-up", type="primary", key="st_go"):
        kind, msg = core.change_check(amt, lim or None)
        label = {"ok": "\u2713 Looks fine", "close": "\u25cf Fine, but close to the limit", "exceeds": "\u25b2 Above your AutoPay limit", "unsure": "? Not sure"}[kind]
        st.markdown(f"<div class='card{' fb' if kind == 'unsure' else ''}'><div class='reason'>{esc(label)}</div><div class='why'>{esc(msg)}</div>"
                    "<p class='src'>Rules only: this compares the numbers you enter.</p></div>", unsafe_allow_html=True)
    st.caption("Mutual fund investing involves market risk. This page explains set-up steps only and isn't investment advice.")
    st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)

def page_quality():
    header()
    st.title("How the helper is checked")
    p = os.path.join(os.path.dirname(__file__), "eval_results.json")
    if os.path.exists(p):
        R = json.load(open(p))
        cols = st.columns(4)
        for c, (v, t) in zip(cols, R["tiles"]):
            c.markdown(f"<div class='tile'><div class='v'>{esc(v)}</div><div class='t'>{esc(t)}</div></div>", unsafe_allow_html=True)
        st.write(R.get("summary", ""))
    else:
        st.info("Eval results appear here after the helper is scored against human labels on a fresh test set. Targets set before labelling: each fact read correctly at least 85% of the time; when the message doesn't pin down a reason, the helper asks or falls back at least 90% of the time; guardrail violations = 0.")
    st.markdown("- **Golden set:** real failure messages from public comments, common status wordings and guardrail tests, labelled by a person without seeing the AI's answer.\n"
                "- **Guards:** personal data is blocked before any AI call; advice, off-topic and rule-override requests are declined; the AI's quoted evidence must appear in the message.\n"
                "- **How it decides:** the AI pre-fills only what your message states (each backed by your own words); you confirm or change it; fixed rules pick the reason; it asks up to 3 questions for anything missing.\n"
                "- **Fix steps:** written in advance from Groww help and other official pages, so the AI can't invent steps.")
    st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)

PAGE_START = st.Page(page_start, title="Start a SIP", icon=":material/rocket_launch:", url_path="start")
pg = st.navigation([st.Page(page_helper, title="What happened?", icon=":material/help:", default=True),
                    PAGE_START,
                    st.Page(page_change, title="Check a change", icon=":material/rule:", url_path="change"),
                    st.Page(page_quality, title="Quality", icon=":material/verified:", url_path="quality")])
pg.run()
