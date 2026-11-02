"""NL-Groww SIP Fix Helper (independent concept, not a Groww product). Streamlit app built from the Figma design."""
import html, json, os, sys
import streamlit as st
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from fix_helper import core  # noqa: E402
from fix_helper.kb import REASONS, SOURCES, GROWW_HELP  # noqa: E402

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
.tag { font-size:.78rem; color:#00875F; background:#E5F7F1; border-radius:99px; padding:3px 10px; font-weight:500; }
.notice { background:#F0FAF6; border-left:3px solid #04B488; border-radius:8px; padding:8px 12px; font-size:.86rem; color:#44475B; margin:10px 0 4px; }
.msg { background:#F2F5F7; border-radius:10px; padding:10px 14px; font-size:.95rem; }
.msg small { display:block; font-size:.72rem; letter-spacing:.06em; text-transform:uppercase; color:#6B6E80; margin-bottom:4px; }
.card { border:1.5px solid #04B488; border-radius:14px; padding:16px 18px; margin-top:12px; }
.card.fb { border-color:#6B6E80; border-style:dashed; }
.lab { font-size:.72rem; letter-spacing:.06em; text-transform:uppercase; color:#6B6E80; }
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
.src { font-size:.78rem; color:#6B6E80; }
.src a, .blk a { color:#027F5F; }
.gg { font-size:.72rem; color:#6B6E80; border:1px solid #C9CCD5; border-radius:99px; padding:0 6px; margin-left:4px; white-space:nowrap; }
.checks { margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }
.chk { font-size:.78rem; border-radius:99px; padding:3px 10px; background:#E5F7F1; color:#00664C; }
.chk.no { background:#F2F5F7; color:#44475B; }
.risk { font-size:.78rem; color:#6B6E80; margin-top:18px; }
.stButton button { border-radius:8px; border:1px solid #027F5F !important; color:#027F5F !important; background:#fff !important; font-weight:500; }
.stButton button[kind="primary"] { background:#027F5F !important; color:#fff !important; }
.stButton button[kind="primary"] p { color:#fff !important; }
.stButton button:hover { background:#E5F7F1 !important; }
.stButton button[kind="primary"]:hover { background:#00664C !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:#E5F7F1 !important; }
.tile { border:1px solid #E7E8EC; border-radius:12px; padding:12px 14px; }
.tile .v { font-size:1.6rem; font-weight:700; color:#027F5F; }
.tile .t { font-size:.82rem; color:#6B6E80; }
</style>"""
NOTICE = "Independent concept by a NextLeap student. Not affiliated with Groww. Not investment advice: it explains what happened to a payment and never recommends a fund or tells you whether to continue."
RISK = "Mutual fund investments are subject to market risks, read all scheme related documents carefully."
EXAMPLES = ["Your SIP installment is in progress. We will update you once the payment is confirmed.",
            "I increased my SIP amount last week and now the autopay failed",
            "SIP installment failed. Reason: AutoPay mandate not approved by bank.",
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

def show_result(text, r):
    st.markdown(f"<div class='msg'><small>Your message</small>“{esc(text)}”</div>", unsafe_allow_html=True)
    if r["kind"] == "answer":
        kb = REASONS[r["reason"]]
        why = f"Why we think so: your message says “{esc(r['evidence'])}”." if r.get("evidence") else ""
        ctx = ""
        if kb.get("context"):
            t, s = kb["context"]; name, url = SOURCES[s]
            ctx = f"<p class='src'>{esc(t)} <a href='{url}' target='_blank'>[source]</a></p>"
        conf = r["confidence"]
        st.markdown(f"""<div class='card'><div class='lab'>Likely reason</div><div class='reason'>{esc(kb['title'])}</div>
<span class='conf {'medium' if conf=='medium' else ''}'>Confidence: {conf.capitalize()}</span>
<div class='why'>{why}</div>
<div class='grid'><div class='blk'><h4>What it means</h4>{esc(kb['means'])}</div>
<div class='blk'><h4>What to do now</h4><ol>{steps_html(kb['now'])}</ol></div>
<div class='blk'><h4>How to avoid it next time</h4><ul>{steps_html(kb['next'])}</ul></div></div>
{ctx}<p class='src'>Steps are written in advance from official help pages; the AI only picks the reason.</p>
{checks_html(r['checks'])}</div>""", unsafe_allow_html=True)
        st.caption("This explains your payment, not your investment. It won't suggest a fund or tell you whether to continue.")
    elif r["kind"] == "fallback":
        st.markdown(f"""<div class='card fb'><div class='lab'>Not sure</div><div class='reason'>I'm not sure what happened from this message</div>
<div class='why'>Rather than guess, here's where to check. Groww's help page explains the common reasons an installment fails
(AutoPay not set up, not enough balance, AutoPay not approved), and how to pay a missed installment with “Pay one-time”.</div>
<p><a href='{GROWW_HELP}' target='_blank'>Open Groww help: why did my installment fail</a></p>
<p class='src'>Tip: paste the exact status or SMS text if you have it. You can also contact Groww support from the app's help section.</p>
{checks_html(r['checks'])}</div>""", unsafe_allow_html=True)
    elif r["kind"] == "decline":
        if r["why"] == "advice":
            body = "I can't advise on funds, returns, or whether to stop or continue a SIP. I can explain why an installment failed and how to fix it."
        elif r["why"] == "off_topic":
            body = "I can only help with SIP installment payments: why one failed and how to fix it."
        else:
            body = r["why"]
        st.markdown(f"<div class='card fb'><div class='lab'>Can't help with this</div><div class='reason'>That's outside what I do</div><div class='why'>{esc(body)}</div>{checks_html(r['checks'])}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='card fb'><div class='lab'>Check your message</div><div class='why'>{esc(r['why'])}</div>{checks_html(r['checks'])}</div>", unsafe_allow_html=True)
    if r.get("mode") == "basic":
        st.caption("The AI is busy right now, so this used simple rules. Rules only answer when the message states the cause clearly.")

def page_helper():
    header()
    st.title("What happened to my SIP installment?")
    st.write("Paste the status you see in the app, a bank SMS, or describe it in your own words (English or Hinglish).")
    st.caption("Don't paste PAN, account or phone numbers. Nothing is stored.")
    if "fx_text" not in st.session_state:
        st.session_state.fx_text = ""
    cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES):
        if cols[i % 2].button(ex if len(ex) < 60 else ex[:57] + "…", key=f"ex{i}", use_container_width=True):
            st.session_state.fx_text = ex
    text = st.text_area("Your message", key="fx_text", height=110, max_chars=800, placeholder="For example: Autopay failed after I increased my SIP")
    if st.button("Explain what happened", type="primary", use_container_width=True) and text.strip():
        with st.spinner("Reading your message…"):
            st.session_state.fx_last = (text, core.explain(text))
    if st.session_state.get("fx_last"):
        show_result(*st.session_state.fx_last)
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
        st.info("Eval results appear here after the helper is scored against human labels. Targets set before building: reason correct at least 80% of the time, unclear messages fall back at least 90% of the time, guardrail violations = 0.")
    st.markdown("- **Golden set:** real failure messages from public comments, common status wordings and guardrail tests, labelled by a person without seeing the AI's answer.\n"
                "- **Guards:** personal data is blocked before any AI call; advice, off-topic and rule-override requests are declined; the AI's quoted evidence must appear in the message.\n"
                "- **Fix steps:** written in advance from Groww help and other official pages; the AI only picks the reason, so it can't invent steps.")
    st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)

pg = st.navigation([st.Page(page_helper, title="What happened?", icon=":material/help:", default=True),
                    st.Page(page_change, title="Check a change", icon=":material/rule:", url_path="change"),
                    st.Page(page_quality, title="Quality", icon=":material/verified:", url_path="quality")])
pg.run()
