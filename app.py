"""Entry point: NL-Groww Discovery Engine (Streamlit)."""
import hashlib
import importlib
import pathlib
import sys

import streamlit as st

st.set_page_config(page_title="NL-Groww Discovery Engine", page_icon=":material/search:", layout="wide")

# Load new engine code after a deploy without a full rebuild: if the engine files changed since they were imported, reload them once.
_ROOT = pathlib.Path(__file__).parent
_code = hashlib.md5(b"".join(p.read_bytes() for p in sorted((_ROOT / "engine").glob("*.py")))).hexdigest()
import engine  # noqa: E402
if getattr(engine, "LOADED_HASH", None) != _code:
    for _m in ("engine.guard", "engine.data", "engine.glossary", "engine.kb", "engine.llm", "engine.pipeline", "engine.suggest", "engine.ui"):
        if _m in sys.modules:
            importlib.reload(sys.modules[_m])
    engine.LOADED_HASH = _code

pg = st.navigation([
    st.Page("views/0_Ask.py", title="Ask the engine", icon=":material/search:", default=True),
    st.Page("views/1_Findings.py", title="Findings", icon=":material/bar_chart:"),
    st.Page("views/2_Opportunities.py", title="Opportunities", icon=":material/target:"),
    st.Page("views/3_Evidence_explorer.py", title="Evidence explorer", icon=":material/format_quote:"),
    st.Page("views/4_Quality_and_evals.py", title="Quality and evals", icon=":material/verified:"),
    st.Page("views/5_How_it_works.py", title="How it works", icon=":material/account_tree:"),
    st.Page("views/6_Tag_a_comment.py", title="Tag a comment", icon=":material/sell:"),
])
pg.run()
