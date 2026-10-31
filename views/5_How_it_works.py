import pandas as pd
import streamlit as st

from engine import data as D
from engine import ui

ui.page("How it works", "⚙️")
E = D.engine_data()
F = E["funnel"]
R = F["reddit"]

st.title("How the engine turns 344,872 public comments into counted answers")
steps = [
    ("1", "Collect", f"{F['collected']:,} public items from Play Store and App Store reviews (Groww and 9 other apps), Reddit, YouTube, TradingQnA, Zerodha Varsity and Team-BHP"),
    ("2", "Clean", f"Remove duplicates, very short, promotional and off-topic items; keep Hinglish and Hindi. {F['cleaned']:,} left"),
    ("3", "Tag with AI", f"Gemini Flash-Lite applies a fixed codebook with a strict JSON schema at temperature 0 (prompt {E['prompt_version']}). {F['tagged']:,} tagged, {F['relevant']:,} relevant"),
    ("4", "Count and compare", f"Themes counted, {F['dropoffs']:,} drop-offs split by type, sources normalised, 7 opportunity areas scored"),
    ("5", "Validate", "Hand-labelled golden set, guardrail scan of every AI output, Reddit sample-vs-full robustness check, chat eval suites"),
    ("6", "Answer", "Chat: rule check, AI intent check, counting tools, output check; plus the Findings, Opportunities and Evidence pages"),
]
st.markdown("""<style>
.flow{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:6px 0 4px}@media(max-width:700px){.flow{grid-template-columns:1fr}}
.flow div{border:1px solid #E7E8EC;border-top:3px solid #04B488;border-radius:8px;padding:10px 12px;background:#fff}
.flow b{display:block;color:#44475B;font-size:.95rem;margin-bottom:4px}
.flow span{font-size:.82rem;color:#6B6E80;line-height:1.45}
</style>""", unsafe_allow_html=True)
st.markdown("<div class='flow'>" + "".join(f"<div><b>{n}. {t}</b><span>{d}</span></div>" for n, t, d in steps) + "</div>", unsafe_allow_html=True)

st.header("Where each brief requirement is shown")
st.markdown("""
| Brief requirement | Where to see it |
|---|---|
| Analyse feedback from multiple sources (app stores, Reddit, YouTube, forums) | This page: sources and volume |
| Answer the 9 discovery questions | Findings (one card per question); Ask the engine answers any wording |
| Go beyond sentiment: identify, quantify and compare opportunity areas | Opportunities (7 areas, scored, per-source view) |
| Show how data is gathered, themes found and insights generated | This page; Tag a comment runs the same tagging live |
| Validate insight quality (golden set, agreement, failure cases) | Quality and evals: golden set |
| Cases where AI output was rejected or corrected | Quality and evals: AI outputs we rejected or corrected |
| Traceable evidence behind every number | Evidence explorer; quotes and checks under every chat answer |
| No fund recommendations, no fear or urgency, not investment advice | Rule and output checks (Quality and evals); notice on every page |
""")

st.header("Sources and volume")
col = F["collected_by_source"]
st.dataframe(pd.DataFrame([{"Source": D.SRC[s], "Collected": col.get(s, 0), "After cleaning": F["cleaned_by_source"].get(s, 0),
                            "Tagged": F["tagged_by_source"].get(s, 0), "Relevant": F["relevant_by_source"].get(s, 0)} for s in D.SRC_ORDER]),
             hide_index=True, use_container_width=True)
st.markdown(f"""
- **How each source was collected:** Play Store and App Store with public review endpoints (India, newest and most relevant, plus per-star pulls for Groww back to 2018); YouTube with the official YouTube Data API (20 English and Hindi searches); Reddit through the Arctic Shift archive (reddit.com blocks automated reads), every post from Jan 2024 to Oct 2026 in three subreddits, filtered to first-person SIP experiences ({R['personal_sip']:,}), of which {R['tagged']:,} were tagged; TradingQnA through its public Discourse API; Zerodha Varsity reader comments; Team-BHP's mutual funds thread.
- **Removed in cleaning:** {F['removed']['duplicates_removed']:,} duplicates, {F['removed']['too_short_removed']:,} comments under six words, {F['removed']['promotional_removed']} promotional posts, {F['removed']['not_relevant_removed']:,} items with no SIP or mutual-fund content (mostly stock trading).
- **Not collected:** Trustpilot, Value Research and MouthShut showed bot checks, which were not bypassed; Team-BHP stopped at 87 posts for the same reason.
- **Privacy:** no usernames, account details or screenshots are stored. The chat blocks personal data before any AI call.
- **Codebook (what each comment is tagged with):** lifecycle stage, events (started, skipped, paused, stopped, payment lapsed and more), drop-off type (voluntary, involuntary, passive drift), reasons, what they check, where they go when unsure, segment hints (income, age, influencer), unmet need, severity (1 to 3), and a verbatim evidence span.
""")
st.header("Known limits")
st.markdown(f"""
- Public comments over-represent complaints and confident investors; quietly forgetting a SIP is barely visible (20 of 3,336 drop-off comments), so interviews cover it.\n- The AI is too generous about which forum comments count as relevant (golden set: 59% first-pass agreement); headline findings hold without forum sources.\n- How often people check, what they expected at the start and where the money comes from are rarely stated, so interviews cover them.
- Most comments do not state whether the writer is a first-time investor, their income or their age, so segment cuts rest on a few thousand items.
- Groww-specific items ({F['groww']:,}) come only from app reviews; community posts rarely name the app.
- {R['cleaned'] - R['tagged']:,} cleaned Reddit items are untagged because the free AI quota ran out; a sample-versus-full check showed near-identical shares.
- Opportunity scores depend on two analyst judgements (fixability and fit with the brief's rules), shown per row.
""")
st.caption("Code for every stage is in the project repository: pipeline/ (collection and analysis), engine/ (guardrails, counting tools, AI calls), evals/ (eval runner).")
