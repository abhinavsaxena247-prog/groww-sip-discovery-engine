import pandas as pd
import streamlit as st

from engine import data as D
from engine import ui

ui.page("How it works", "⚙️")
E = D.engine_data()
F = E["funnel"]
R = F["reddit"]

st.title("How the engine turns 344,872 public comments into counted answers")
st.graphviz_chart(f"""
digraph G {{
  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#F2F5F7", color="#DDE3E8", fontname="Helvetica", fontsize=11];
  edge [color="#027F5F"];
  subgraph cluster_src {{ label="1. Collect"; color="#DDE3E8"; fontname="Helvetica";
    ps [label="Play Store\\n168,082 (Groww + 7 apps)"]; as [label="App Store\\n9,000 (9 apps)"]; rd [label="Reddit\\n132,264 (3 subreddits)"];
    yt [label="YouTube\\n24,740 (131 videos)"]; fo [label="Forums\\nTradingQnA 6,389\\nVarsity 4,310 · Team-BHP 87"]; }}
  clean [label="2. Clean\\ndedupe · spam · length · SIP relevance\\nHinglish and Hindi kept\\n{F['cleaned']:,} items"];
  tag [label="3. AI tagging (Gemini Flash-Lite)\\nfixed codebook · strict JSON schema\\ntemperature 0 · prompt {E['prompt_version']}\\n{F['tagged']:,} tagged"];
  ana [label="4. Count and compare\\n{F['relevant']:,} relevant · {F['dropoffs']:,} drop-offs\\nper-source normalisation\\nopportunity scoring"];
  val [label="5. Validate\\ngolden set (human labels)\\nguardrail scan · robustness check"];
  chat [label="6. Ask the engine\\nrule check → AI intent check\\n→ counting tools → output check", fillcolor="#E3F6F0"];
  ps -> clean; as -> clean; rd -> clean; yt -> clean; fo -> clean; clean -> tag -> ana -> chat; tag -> val; val -> chat [style=dashed];
}}""", use_container_width=True)

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
- Public comments over-represent complaints and confident investors; quiet drop-offs and passive drift are barely visible, so interviews cover them.
- Most comments do not state whether the writer is a first-time investor, their income or their age, so segment cuts rest on a few thousand items.
- Groww-specific items ({F['groww']:,}) come only from app reviews; community posts rarely name the app.
- {R['cleaned'] - R['tagged']:,} cleaned Reddit items are untagged because the free AI quota ran out; a sample-versus-full check showed near-identical shares.
- Opportunity scores depend on two analyst judgements (fixability and fit with the brief's rules), shown per row.
""")
st.caption("Code for every stage is in the project repository: pipeline/ (collection and analysis), engine/ (guardrails, counting tools, AI calls), evals/ (eval runner).")
