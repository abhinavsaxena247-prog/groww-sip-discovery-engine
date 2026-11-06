"""NL-Groww SIP Fix Helper (independent concept, not a Groww product). Streamlit app built from the Figma design."""
import html, json, os, sys
import streamlit as st
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import hashlib, importlib  # noqa: E402
import engine.guard, engine.llm, fix_helper.kb, fix_helper.help, fix_helper.core  # noqa: E402,F401
# Streamlit Cloud keeps imported modules between deploys: reload any whose source changed.
import builtins  # noqa: E402
_H = getattr(builtins, "_nlg_fix_hashes", None)
if _H is None:
    _H = {}
    builtins._nlg_fix_hashes = _H
for _m in (engine.guard, engine.llm, fix_helper.kb, fix_helper.help, fix_helper.core):
    try:
        _h = hashlib.md5(open(_m.__file__, "rb").read()).hexdigest()
        if _H.get(_m.__name__) not in (None, _h):
            importlib.reload(_m)
        _H[_m.__name__] = _h
    except Exception:
        pass
from fix_helper import core  # noqa: E402
from fix_helper.kb import REASONS, SOURCES, GROWW_HELP  # noqa: E402
from fix_helper import help as HELP  # noqa: E402

st.set_page_config(page_title="SIP Fix Helper · NL-Groww concept", page_icon=":material/build:", layout="centered", initial_sidebar_state="collapsed")
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
.msg small { display:block; font-size:.8rem; font-weight:600; color:#55586A; margin-bottom:4px; }
.card { border:1.5px solid #04B488; border-radius:14px; padding:16px 18px; margin-top:12px; }
.card.fb { border-color:#55586A; border-style:dashed; }
.lab { font-size:.82rem; font-weight:600; color:#55586A; }
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
[data-testid="stSidebarNav"] a[href$="/quality"] { display:none; }
.alert { background:#fff; border:1px solid #D5D9E0; border-radius:16px; padding:12px 14px; margin:14px 0 6px; box-shadow:0 2px 8px rgba(20,30,50,.08); }
.alert .ahd { font-size:.8rem; color:#55586A; display:flex; align-items:center; gap:6px; }
.alert .adot { width:10px; height:10px; border-radius:3px; background:#027F5F; display:inline-block; }
.alert .att { font-weight:600; color:#22232B; margin-top:4px; }
.alert .abd { color:#22232B; font-size:.95rem; }
.checks { margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }
.chk { font-size:.78rem; border-radius:99px; padding:3px 10px; background:#E5F7F1; color:#00664C; }
.chk.no { background:#F2F5F7; color:#44475B; }
.risk { font-size:.78rem; color:#55586A; margin-top:18px; }
.stButton button { border-radius:8px; border:1px solid #027F5F !important; color:#027F5F !important; background:#fff !important; font-weight:500; }
.stButton button[kind="primary"] { background:#027F5F !important; color:#fff !important; }
.stButton button[kind="primary"] p { color:#fff !important; }
.stButton button:hover { background:#E5F7F1 !important; }
.stButton button[kind="primary"]:hover { background:#00664C !important; }
.stButton button:disabled, .stButton button:disabled:hover { background:#ECEEF2 !important; color:#55586A !important; border-color:#C9CDD6 !important; cursor:not-allowed; }
.stButton button:disabled p { color:#55586A !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background:#E5F7F1 !important; }
.tile { border:1px solid #E7E8EC; border-radius:12px; padding:12px 14px; }
.tile .v { font-size:1.6rem; font-weight:700; color:#027F5F; }
.tile .t { font-size:.82rem; color:#55586A; }
.pgbar { display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin:6px 0 10px; font-size:.9rem; }
.pg { color:#55586A; padding:3px 10px; border-radius:99px; border:1px solid #DDE3E6; }
.pg b { margin-right:2px; }
.pg.on { color:#fff; background:#027F5F; border-color:#027F5F; }
.pg.done { color:#00664C; background:#E5F7F1; border-color:#E5F7F1; }
.pgsep { color:#55586A; }
.tiles-h { font-size:1.05rem; font-weight:700; color:#44475B; margin:18px 0 6px; }
[data-testid="stPageLink"] a { border:1px solid #027F5F; border-radius:8px; justify-content:center; padding:6px 10px; }
[data-testid="stPageLink"] a p { color:#027F5F !important; font-weight:500; }
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
            out.append(f"<li>{esc(text)} <a href='{url}' target='_blank' title='{esc(name)}'>Learn more</a></li>")
        else:
            out.append(f"<li>{esc(text)}</li>")
    return "".join(out)

def checks_html(checks):
    return ""  # internal checks stay out of the investor's view (they are on the Quality page)
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
            ctx = f"<p class='src'>{esc(t)} <a href='{url}' target='_blank'>Learn more</a></p>"
        conf = r["confidence"]
        st.markdown(f"""<div class='card'><div class='lab'>Likely reason</div><div class='reason'>{esc(kb['title'])}</div>
<div class='why'>{why}</div>
<div class='grid'><div class='blk'><h4>What it means</h4>{esc(kb['means'])}</div>
<div class='blk'><h4>What to do now</h4><ol>{steps_html(kb['now'])}</ol></div>
<div class='blk'><h4>How to avoid it next time</h4><ul>{steps_html(kb['next'])}</ul></div></div>
{ctx}</div>""", unsafe_allow_html=True)
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
            rows.append(f"<li><b>{esc(name)}:</b> {esc(vals[v])}</li>")
        elif k in answers:
            shown = "no reason given" if v == "none" else "not sure"
            rows.append(f"<li><b>{esc(name)}:</b> {shown}</li>")
    return "<ul>" + "".join(rows) + "</ul>" if rows else "<p class='src'>Nothing specific yet.</p>"

def start_over():
    reset_flow()
    st.session_state.fx_text = ""

def reset_flow():
    for k in ("fx_read", "fx_answers", "fx_asked", "fx_confirmed", "fx_qn", "fx_guide", "fx_editing", "fx_tile", "fx_edit_err", "fx_alert", "fx_demo"):
        st.session_state.pop(k, None)
    for k in [k for k in st.session_state if str(k).startswith("cf_")]:
        st.session_state.pop(k, None)

def help_lines_html(lines):
    out = []
    for text, src in lines:
        if src:
            name, url = HELP.H[src]
            out.append(f"<li>{esc(text)} <a href='{url}' target='_blank' title='{esc(name)}'>Learn more</a></li>")
        else:
            out.append(f"<li>{esc(text)}</li>")
    return "<ul>" + "".join(out) + "</ul>"

def show_help(r):
    if r["topic"] == "manage_menu":
        st.markdown("<div class='card'><div class='lab'>Manage a SIP</div><div class='reason'>What would you like to do?</div></div>", unsafe_allow_html=True)
        for lab, top in [("Skip or pause an installment", "manage_pause"), ("Change the amount or date", "manage_change"),
                         ("Cancel a SIP", "manage_cancel"), ("Set up or change AutoPay", "manage_autopay")]:
            st.button(lab, key=f"m_{top}", use_container_width=True, on_click=open_topic, args=(lab, top))
        return
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

def set_example(ex):
    reset_flow()
    st.session_state.fx_text = ex

def open_topic(label, topic):
    reset_flow()
    st.session_state.fx_read = (label, {"kind": "help", "topic": topic, "can_continue": False,
                                        "checks": [("Answer from checked sources", True)]})
    st.session_state.fx_tile = True

def start_edit():
    tile = st.session_state.get("fx_tile") or st.session_state.get("fx_alert")
    st.session_state.fx_edit = "" if tile else st.session_state.fx_read[0]
    st.session_state.fx_editing = True
    st.session_state.pop("fx_edit_err", None)

def cancel_edit():
    st.session_state.fx_editing = False
    st.session_state.pop("fx_edit_err", None)

def apply_edit():
    t = (st.session_state.get("fx_edit") or "").strip()
    if not t:
        st.session_state.fx_edit_err = "Type your message first, or tap Cancel."
        return
    reset_flow()
    st.session_state.fx_text = t
    with st.spinner("Reading your message\u2026"):
        st.session_state.fx_read = (t, core.read_facts(t))
    st.session_state.fx_answers, st.session_state.fx_asked = {}, []

def message_card(text):
    if st.session_state.get("fx_editing"):
        st.text_area("Edit your message, or write a new one", key="fx_edit", height=100, max_chars=800)
        err = st.session_state.get("fx_edit_err")
        if err:
            st.warning(err)
        c1, c2 = st.columns(2)
        c1.button("Cancel", key="ed_cancel", use_container_width=True, on_click=cancel_edit)
        c2.button("Update", key="ed_go", type="primary", use_container_width=True, on_click=apply_edit)
        st.caption("Your answers so far are cleared and I'll read the new message from the start. Don't include PAN, Aadhaar, account or phone numbers.")
        return
    alert = st.session_state.get("fx_alert")
    lab = "From the alert" if alert else ("You chose" if st.session_state.get("fx_tile") else "Your message")
    shown = esc(text) if (st.session_state.get("fx_tile") or alert) else f"\u201c{esc(text)}\u201d"
    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    c1.markdown(f"<div class='msg'><small>{lab}</small>{shown}</div>", unsafe_allow_html=True)
    c2.button("Type instead" if (st.session_state.get("fx_tile") or alert) else "Edit", key="ed_open", use_container_width=True, on_click=start_edit,
              help="Change your message or write a new one")

ALERTS = [
    ("Your SIP installment didn't go through", "Reason from your bank: not enough balance in the linked account.",
     {"app_status": "failed", "debited": "no", "stated_cause": "low_balance"}),
    ("Your SIP installment didn't go through", "Reason from your bank: the amount is above your AutoPay limit.",
     {"app_status": "failed", "debited": "no", "stated_cause": "over_limit"}),
    ("Your SIP installment didn't go through", "Your bank didn't share a reason.",
     {"app_status": "failed", "debited": "no", "stated_cause": "none"}),
]

def open_demo():
    reset_flow()
    st.session_state.fx_demo = True

def open_alert(i):
    title, body, facts = ALERTS[i]
    reset_flow()
    st.session_state.fx_read = (f"{title}. {body}", {"kind": "facts", "facts": dict(facts, recent_change="not_said"), "evidence": {},
                                                  "checks": [], "mode": "alert"})
    st.session_state.fx_answers, st.session_state.fx_asked = {}, []
    st.session_state.fx_alert = True

def demo_page():
    st.button("\u2190 Back", key="demo_back", on_click=start_over)
    st.title("See it from a failure alert")
    st.markdown("<div class='notice'>Demo only. This shows what an alert at the moment of failure could look like. "
                "Real alerts would need Groww's payment data, so none are sent here.</div>", unsafe_allow_html=True)
    st.write("Tap “See how to fix it” on one of these example alerts.")
    for i, (title, body, _) in enumerate(ALERTS):
        st.markdown(f"<div class='alert'><div class='ahd'><span class='adot'></span>SIP Fix Helper · now</div>"
                    f"<div class='att'>{esc(title)}</div><div class='abd'>{esc(body)}</div></div>", unsafe_allow_html=True)
        st.button("See how to fix it", key=f"al_{i}", type="primary", use_container_width=True, on_click=open_alert, args=(i,))
    st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)

def go_back():
    asked, answers = st.session_state.get("fx_asked", []), st.session_state.get("fx_answers", {})
    if st.session_state.get("fx_qn", 0) > 0 and asked:
        f = asked.pop()
        answers.pop(f, None)
        st.session_state.fx_qn -= 1
    else:
        for f in core.CONFIRM_FACTS:
            answers.pop(f, None)
            if f in asked:
                asked.remove(f)
        st.session_state.fx_confirmed = False

def exit_row(key):
    st.button("Ask something else", key=key, type="primary", use_container_width=True, on_click=start_over)

def on_voice():
    audio = st.session_state.get("fx_audio")
    if audio is None:
        return
    with st.spinner("Listening to your recording\u2026"):
        t, err = core.transcribe(audio.getvalue(), getattr(audio, "type", None) or "audio/wav")
    if t:
        reset_flow()
        st.session_state.fx_text = t
        st.session_state.fx_voice_msg = ("ok", "Here's what I heard. Check it, fix anything that's wrong, then tap Continue.")
    else:
        st.session_state.fx_voice_msg = ("err", {"no_speech": "I couldn't hear any words. Try again a little closer to the mic, or type instead.",
                                                 "too_long": "That recording is too long. Keep it under a minute.",
                                                 "unavailable": "Voice isn't available right now. Please type your message instead."}.get(err, "Please try again or type instead."))

def progress(stage):
    labels = ["Tell me", "Check", "Fix"]
    parts = []
    for i, lab in enumerate(labels, 1):
        cls = "on" if i == stage else ("done" if i < stage else "")
        mark = "\u2713" if i < stage else str(i)
        parts.append(f"<span class='pg {cls}'><b>{mark}</b> {lab}</span>")
    st.markdown("<div class='pgbar' role='list' aria-label='Progress'>" + "<span class='pgsep'>\u203a</span>".join(parts) + "</div>", unsafe_allow_html=True)

def read_aloud(text, key):
    import json as _json
    import streamlit.components.v1 as components
    components.html(f"""<button id="b" style="font:500 15px system-ui,sans-serif;border:1px solid #027F5F;color:#027F5F;background:#fff;border-radius:8px;padding:6px 12px;cursor:pointer">\U0001F50A Read aloud</button>
<script>const t={_json.dumps(text)};document.getElementById('b').onclick=()=>{{try{{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t);u.lang='en-IN';u.rate=0.95;speechSynthesis.speak(u);}}catch(e){{}}}};</script>""", height=46)

def guide(reason):
    kb = REASONS[reason]
    steps = list(kb["now"])
    i = st.session_state.get("fx_guide", 0)
    if i >= len(steps):
        st.markdown("<div class='card'><div class='lab'>All steps done</div><div class='reason'>You've gone through every step</div>"
                    f"<div class='why'>Next time: {esc(kb['next'][0][0])}</div></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.button("\u2190 Back to the last step", key="g_back_end", use_container_width=True, on_click=lambda: st.session_state.update(fx_guide=len(steps) - 1))
        c2.button("Done", key="g_done", type="primary", use_container_width=True, on_click=start_over)
        return
    text, src = steps[i]
    link = f"<a href='{SOURCES[src][1]}' target='_blank'>Learn more on Groww Help</a>" if src else ""
    st.markdown(f"<div class='card'><div class='lab'>Step {i + 1} of {len(steps)}</div><div class='reason' style='font-size:1.3rem'>{esc(text)}</div>" +
                (f"<p class='src'>{link}</p>" if link else "") + "</div>", unsafe_allow_html=True)
    read_aloud(f"Step {i + 1} of {len(steps)}. {text}", key=f"ra{i}")
    c1, c2 = st.columns(2)
    c1.button("\u2190 Back", key=f"g_back{i}", use_container_width=True, disabled=i == 0, on_click=lambda: st.session_state.update(fx_guide=max(0, i - 1)))
    c2.button("Done, next step" if i < len(steps) - 1 else "Done, finish", key=f"g_next{i}", type="primary", use_container_width=True,
              on_click=lambda: st.session_state.update(fx_guide=i + 1))
    st.button("Show all steps at once", key="g_all", use_container_width=True, on_click=lambda: st.session_state.pop("fx_guide", None))

def page_helper():
    header()
    if "fx_text" not in st.session_state:
        st.session_state.fx_text = ""
    if st.session_state.get("fx_demo") and not st.session_state.get("fx_read"):
        demo_page()
        return
    if not st.session_state.get("fx_read"):
        st.title("What happened to your SIP?")
        st.write("Describe it in your own words, or paste the app status or bank SMS. English or Hinglish is fine.")
        progress(1)
        vm = st.session_state.pop("fx_voice_msg", None)
        if vm:
            (st.success if vm[0] == "ok" else st.warning)(vm[1])
        text = st.text_area("Your message", key="fx_text", height=100, max_chars=800,
                            placeholder="For example: my SIP failed this month and I don't know why")
        if hasattr(st, "audio_input") or hasattr(st, "experimental_audio_input"):
            mic = getattr(st, "audio_input", None) or st.experimental_audio_input
            mic("Or tap the mic and say what happened (English, Hindi or Hinglish)", key="fx_audio", on_change=on_voice)
            st.caption("Your recording is only used to write the text above, then discarded. Don't say PAN, Aadhaar, account or phone numbers.")
        if st.button("Continue", type="primary", use_container_width=True, key="go") and text.strip():
            with st.spinner("Reading your message\u2026"):
                st.session_state.fx_read = (text, core.read_facts(text))
            st.session_state.fx_answers, st.session_state.fx_asked = {}, []
            st.rerun()
        st.caption("Don't paste PAN, Aadhaar, account or phone numbers. Nothing is stored.")
        with st.expander("Not sure what to write? Try an example"):
            for i, ex in enumerate(EXAMPLES):
                st.button(ex, key=f"ex{i}", use_container_width=True, on_click=set_example, args=(ex,))
        st.button("See it from a failure alert (demo)", key="t_demo", use_container_width=True, on_click=open_demo,
                  help="How this could work if an alert reached you the moment an installment fails")
        st.markdown("<div class='tiles-h'>Something else?</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.page_link(PAGE_START, label="Start a SIP", icon=":material/rocket_launch:", use_container_width=True)
            st.button("Contact Groww support", key="t_support", use_container_width=True, on_click=open_topic, args=("Contact Groww support", "support"))
        with c2:
            st.button("Skip, change or cancel a SIP", key="t_manage", use_container_width=True, on_click=open_topic, args=("Skip, change or cancel a SIP", "manage_menu"))
            st.button("What is a SIP?", key="t_faq", use_container_width=True, on_click=open_topic, args=("What is a SIP?", "faq_sip"))
        st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)
        return
    st.button("\u2190 Ask something else", key="top_exit", on_click=start_over)
    text, r = st.session_state.fx_read
    message_card(text)
    if r["kind"] != "facts":
        show_result(text, r, echo=False)
        exit_row("exit_help")
        st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)
        return
    answers, asked = st.session_state.fx_answers, st.session_state.fx_asked
    progress(2 if not st.session_state.get("fx_confirmed") else 3)
    if not st.session_state.get("fx_confirmed"):
        st.markdown("<div class='lab' style='margin-top:14px'>Quick check</div>"
                    "<div class='reason' style='font-size:1.15rem'>Is this right? Change anything that's wrong.</div>", unsafe_allow_html=True)
        st.caption("Filled in from the alert. Change anything that's wrong." if st.session_state.get("fx_alert") else "Don't know an answer? Pick Not sure.")
        picks = {}
        for f in core.CONFIRM_FACTS:
            q, opts = core.QUESTIONS[f]
            codes = [c for c, _ in opts]
            ai_val = r["facts"].get(f)
            if f"cf_{f}" not in st.session_state:
                st.session_state[f"cf_{f}"] = ai_val if ai_val in codes else "not_said"
            picks[f] = st.radio(q, codes, format_func=dict(opts).get, key=f"cf_{f}")
        clash = core.conflict(picks)
        if clash:
            st.warning(clash["msg"])
            for n, (label, upd) in enumerate(clash["fixes"]):
                st.button(label, key=f"cx_{n}", use_container_width=True,
                          on_click=lambda u=upd: st.session_state.update({f"cf_{k}": v for k, v in u.items()}))
        go = st.button("Looks right, continue", type="primary", use_container_width=True, key="cf_go", disabled=bool(clash))
        if clash:
            st.caption("Pick one of the options above to continue.")
        if go:
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
    st.markdown(f"<div class='card fb'><div class='lab'>Your details</div>{facts_html(r['facts'], r['evidence'], answers)}</div>", unsafe_allow_html=True)
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
        st.button("\u2190 Back", key="q_back", on_click=go_back)
    elif kind == "reason":
        if st.session_state.get("fx_guide") is not None:
            guide(val)
            st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)
            return
        st.button("Guide me step by step", key="g_start", type="primary", use_container_width=True, on_click=lambda: st.session_state.update(fx_guide=0))
        res = {"kind": "answer", "reason": val, "label": core.LABELS.get(val, val), "evidence": "",
               "confidence": "medium", "mode": r.get("mode"),
               "checks": r["checks"] + [("You checked what I understood", True), ("Reason picked by fixed rules from the facts above", True), ("Fix steps from checked sources", True), ("Output guardrails passed", True)]}
        show_result(text, res, echo=False, how="Based on what you told me.")
        st.markdown(f"<div class='blk' style='margin-top:10px'><h4>Good to know</h4>{help_lines_html(GOOD_TO_KNOW)}</div>", unsafe_allow_html=True)
    else:
        show_result(text, {"kind": "fallback", "checks": r["checks"] + [("Not enough facts to name a reason, so no guess", True)], "mode": r.get("mode")}, echo=False)
    if kind != "ask":
        exit_row("exit_result")
    if r.get("advice_note"):
        st.caption("You also asked for an opinion on funds or returns. I can't advise on that; this covers the payment only.")
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
                    "<p class='src'>Based only on the numbers you entered. Check your current limit in the app.</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='risk'>{RISK}</div>", unsafe_allow_html=True)

def page_start():
    header()
    st.title("Start a SIP")
    st.write("Groww's steps to start a SIP, plus a set-up checklist so your installments go through from the first month. "
             "Which fund to choose is your decision; this page never suggests one.")
    st.markdown(f"""<div class='card'><div class='lab'>Steps in the Groww app</div><div class='blk'><ol>
<li>From Home, open Mutual Funds and tap Explore. <a href='{HELP.H["S15"][1]}' target='_blank'>Learn more</a></li>
<li>Find the fund you've chosen and tap Start SIP. <a href='{HELP.H["S15"][1]}' target='_blank'>Learn more</a></li>
<li>Enter the amount and choose the monthly date. <a href='{HELP.H["S15"][1]}' target='_blank'>Learn more</a></li>
<li>Pay the first installment with UPI or net banking. <a href='{HELP.H["S15"][1]}' target='_blank'>Learn more</a></li>
<li>Complete AutoPay (OTP or form) so later installments are debited automatically. <a href='{HELP.H["S15"][1]}' target='_blank'>Learn more</a></li>
</ol></div></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class='card'><div class='lab'>Set it up so it doesn't fail</div><div class='blk'><ul>
<li>Pick a date when your linked account usually has the money, for example a few days after your salary arrives.</li>
<li>Keep the balance ready 4 days before the installment date. <a href='{SOURCES["S1"][1]}' target='_blank'>Learn more</a></li>
<li>Set an AutoPay limit above your planned amount, with room if you plan to increase it later.</li>
<li>Check AutoPay shows as approved; bank approval takes 2 to 7 working days. <a href='{HELP.H["S9"][1]}' target='_blank'>Learn more</a></li>
<li>Expect the second installment about two months after the first: there's a 30-day minimum gap. <a href='{HELP.H["S16"][1]}' target='_blank'>Learn more</a></li>
</ul></div></div>""", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    amt = c1.number_input("Planned monthly amount (\u20b9)", min_value=0, step=500, value=0, key="st_amt")
    lim = c2.number_input("AutoPay limit you'll set (\u20b9), if you know it", min_value=0, step=1000, value=0, key="st_lim")
    if st.button("Check my set-up", type="primary", key="st_go"):
        kind, msg = core.change_check(amt, lim or None)
        label = {"ok": "\u2713 Looks fine", "close": "\u25cf Fine, but close to the limit", "exceeds": "\u25b2 Above your AutoPay limit", "unsure": "? Not sure"}[kind]
        st.markdown(f"<div class='card{' fb' if kind == 'unsure' else ''}'><div class='reason'>{esc(label)}</div><div class='why'>{esc(msg)}</div>"
                    "<p class='src'>Based only on the numbers you entered.</p></div>", unsafe_allow_html=True)
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
