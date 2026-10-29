"""NL-Groww Discovery Engine: ask questions of 21,445 tagged public comments about SIP continuation."""
import streamlit as st

from engine import data as D
from engine import guard as G
from engine import llm
from engine import pipeline as P
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

ai_on = llm.ai_available()
with st.sidebar:
    st.subheader("How every reply is checked")
    st.markdown("1. **Rule check** on your question: abuse (English, Hinglish, Hindi), personal data, attempts to override the rules, advice and off-topic requests. Blocked messages never reach the AI and are not stored.\n"
                "2. **AI intent check**: research question, advice, own-account help, off-topic or greeting.\n"
                "3. **Grounded answer**: the AI must call counting tools over the tagged comments.\n"
                "4. **Output check**: every number must trace to the counts; no fund names, advice wording, urgency or personal data.")
    st.caption(("Mode: AI (Gemini with counting tools)." if ai_on else "Mode: basic (direct counts).") +
               " If the free AI quota runs out, the engine switches to basic mode with the same checks.")
    if st.button("Clear conversation"):
        st.session_state.msgs, st.session_state.history = [], []
        st.rerun()

STARTERS = ["Why do first-time investors stop their SIPs?", "What goes wrong when Groww SIP payments fail?",
            "What do new investors check after starting?", "Do people ask to pause instead of cancel?",
            "How do Reddit and Play Store differ on why people stop?", "log SIP kyun band karte hain?"]


def render(m):
    with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🔎"):
        if m.get("masked"):
            st.caption(m["text"])
            return
        st.write(m["text"])
        o = m.get("out")
        if not o:
            return
        if o.get("breakdown") and o["breakdown"].get("values"):
            b = o["breakdown"]
            ui.bars([{"label": f"{v['label']} ({v['pct_of_base']}%)", "n": v["n"]} for v in b["values"][:6]],
                    title=f"{o.get('title') or 'Counted breakdown'} · base {b['base_comments']:,} comments" + (" (small sample)" if b["base_comments"] < 30 else ""))
        for q in (o.get("quotes") or [])[:3]:
            ui.quote(q)
        ui.chips(o["checks"])
        if o.get("reframe"):
            st.caption("You can ask this instead: " + o["reframe"])


for m in st.session_state.msgs:
    render(m)

if not st.session_state.msgs:
    with st.chat_message("assistant", avatar="🔎"):
        st.write(P.greeting())

cols = st.columns(3)
clicked = None
for i, s in enumerate(STARTERS):
    if cols[i % 3].button(s, key=f"s{i}", use_container_width=True):
        clicked = s

q = st.chat_input("Ask about SIP behaviour, for example: what do first-time investors on Groww check after starting?", max_chars=800) or clicked
if q:
    if st.session_state.asked >= MAX_Q:
        st.warning("You've reached the limit of 25 questions for this session. Reload the page to start a new session.")
    else:
        st.session_state.asked += 1
        pre = G.check_input(q)
        shown = {"abuse": "Message hidden: abusive language", "pii": "Message hidden: it contained personal data"}.get(pre["verdict"])
        st.session_state.msgs.append({"role": "user", "text": shown or q, "masked": bool(shown)})
        with st.spinner("Checking and counting…"):
            out = P.answer(q, st.session_state.history, use_ai=ai_on)
        st.session_state.msgs.append({"role": "assistant", "text": out["text"], "out": out})
        if out["route"] == "answer":
            st.session_state.history.append({"q": q, "a": out["text"]})
        st.rerun()

st.caption("Mutual fund investments are subject to market risks, read all scheme related documents carefully. "
           "Numbers are AI tags on public comments and are directional; see Quality and evals for how they were checked.")
