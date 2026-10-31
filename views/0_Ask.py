"""NL-Groww Discovery Engine: ask questions of 21,445 tagged public comments about SIP continuation."""
import streamlit as st

from engine import data as D
from engine import guard as G
from engine import llm
from engine import pipeline as P
from engine import suggest as S
from engine import ui

ui.page("Ask the engine")
E = D.engine_data()
F = E["funnel"]

st.title("Why first-time investors keep, pause or stop their SIPs")
st.write(f"Ask anything about SIP behaviour. The engine answers only from **{F['relevant']:,} AI-tagged public comments** "
         f"(from {F['collected']:,} collected across Play Store, App Store, Reddit, YouTube, TradingQnA, Zerodha Varsity and Team-BHP), "
         "counts before it speaks, and shows the checks it ran on every reply.")

MAX_Q = 25
if "msgs" not in st.session_state:
    st.session_state.msgs = []
    st.session_state.history = []
    st.session_state.asked = 0
    import random as _r
    st.session_state.seed = _r.randint(0, 10**9)

ai_on = llm.ai_available()
with st.sidebar:
    st.subheader("How every reply is checked")
    st.markdown("**What you can ask:** SIP basics (minimum amount, lumpsum or monthly, pausing, missed installments, tax, NAV...), "
                "the research findings and how they were produced, or any question about what investors wrote, by app, source, segment or year.")
    st.markdown("1. **Rule check** on your question: abuse (English, Hinglish, Hindi), personal data, attempts to override the rules, advice and off-topic requests. Blocked messages never reach the AI and are not stored.\n"
                "2. **AI intent check**: research question, advice, own-account help, off-topic or greeting.\n"
                "3. **Grounded answer**: the AI must call counting tools over the tagged comments.\n"
                "4. **Output check**: every number must trace to the counts; no fund names, advice wording, urgency or personal data.")
    st.caption(("Mode: AI (Gemini with counting tools)." if ai_on else "Mode: basic (direct counts).") +
               " If the free AI quota runs out, the engine switches to basic mode with the same checks.")


def render(m):
    with st.chat_message(m["role"], avatar=":material/person:" if m["role"] == "user" else ":material/query_stats:"):
        if m.get("masked"):
            st.caption(m["text"])
            return
        st.write(m["text"])
        o = m.get("out")
        if not o:
            return
        if o.get("breakdown") and o["breakdown"].get("values"):
            b = o["breakdown"]
            if b.get("plain"):
                ui.bars([{"label": v["label"], "n": v["n"]} for v in b["values"][:8]], title=o.get("title") or "From the computed results")
            else:
                ui.bars([{"label": f"{v['label']} ({v['pct_of_base']}%)", "n": v["n"]} for v in b["values"][:8]],
                        title=f"{o.get('title') or 'Counted breakdown'} · base {b['base_comments']:,} comments" + (" (small sample)" if b["base_comments"] < 30 else ""))
        for q in (o.get("quotes") or [])[:3]:
            ui.quote(q)
        ui.chips(o["checks"])
        if o.get("reframe"):
            st.caption("You can ask this instead: " + o["reframe"])


for m in st.session_state.msgs:
    render(m)

starters_box = st.empty()
clicked = None


def button_row(items, key, label=None, cols=2):
    global clicked
    if not items:
        return
    if label:
        st.markdown(f"<div class='nl-sublabel'>{label}</div>", unsafe_allow_html=True)
    cs = st.columns(cols)
    for i, s_ in enumerate(items):
        if cs[i % cols].button(s_, key=f"{key}{i}", use_container_width=True):
            clicked = s_


asked_qs = [m["text"] for m in st.session_state.msgs if m["role"] == "user" and not m.get("masked")]
if not st.session_state.msgs:
    with starters_box.container():
        with st.chat_message("assistant", avatar=":material/query_stats:"):
            st.write(P.greeting())
        button_row(S.starters(st.session_state.seed), "s", "Try one of these")
        button_row(S.popular([], 3), "p", "Asked recently by other visitors")
else:
    last_q = asked_qs[-1] if asked_qs else ""
    last_out = st.session_state.msgs[-1].get("out")
    o_reframe = (last_out or {}).get("reframe")
    nexts = S.follow_ups(last_q, last_out, asked_qs) if last_q else []
    if o_reframe and o_reframe not in nexts:
        nexts = [o_reframe] + nexts[:2]
    button_row(nexts, f"f{len(st.session_state.msgs)}_", "Suggested next questions, based on what you just asked")
    button_row(S.popular(asked_qs, 3), f"p{len(st.session_state.msgs)}_", "Asked recently by other visitors")

q = st.chat_input("Ask anything about SIPs", max_chars=800) or clicked
if q:
    if st.session_state.asked >= MAX_Q:
        st.warning("You've reached the limit of 25 questions for this session. Reload the page to start a new session.")
    else:
        st.session_state.asked += 1
        starters_box.empty()
        pre = G.check_input(q)
        shown = {"abuse": "Message hidden: abusive language", "pii": "Message hidden: it contained personal data"}.get(pre["verdict"])
        user_msg = {"role": "user", "text": shown or q, "masked": bool(shown)}
        render(user_msg)                                   # show the question straight away
        with st.chat_message("assistant", avatar=":material/query_stats:"):
            with st.spinner("Checking your question and counting the comments…"):
                out = P.answer(q, st.session_state.history, use_ai=ai_on and not clicked)   # example buttons use the direct count: instant and identical every time
        st.session_state.msgs += [user_msg, {"role": "assistant", "text": out["text"], "out": out}]
        if out["route"] in ("answer", "basics", "research"):
            st.session_state.history.append({"q": q, "a": out["text"]})
        if not clicked:
            S.record(q, out["route"])              # typed questions only, and only if they passed every check
        st.rerun()

c_left, c_right = st.columns([3, 1], vertical_alignment="center")
c_left.caption("Mutual fund investments are subject to market risks, read all scheme related documents carefully. "
               "Numbers are AI tags on public comments and are directional; see Quality and evals for how they were checked.")
if c_right.button("Clear chat", key="clear", type="primary", icon=":material/delete_sweep:", use_container_width=True, disabled=not st.session_state.msgs,
                  help="Remove this conversation and start again"):
    st.session_state.msgs, st.session_state.history = [], []
    st.rerun()
