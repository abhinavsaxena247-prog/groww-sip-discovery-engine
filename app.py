"""Entry point: NL-Groww Discovery Engine (Streamlit)."""
import streamlit as st

st.set_page_config(page_title="NL-Groww Discovery Engine", page_icon="🔎", layout="wide")
pg = st.navigation([
    st.Page("views/0_Ask.py", title="Ask the engine", icon="🔎", default=True),
    st.Page("views/1_Findings.py", title="Findings", icon="📊"),
    st.Page("views/2_Opportunities.py", title="Opportunities", icon="🎯"),
    st.Page("views/3_Evidence_explorer.py", title="Evidence explorer", icon="🗂️"),
    st.Page("views/4_Quality_and_evals.py", title="Quality and evals", icon="✅"),
    st.Page("views/5_How_it_works.py", title="How it works", icon="⚙️"),
    st.Page("views/6_Tag_a_comment.py", title="Tag a comment", icon="🏷️"),
])
pg.run()
