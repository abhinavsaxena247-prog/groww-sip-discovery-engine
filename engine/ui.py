"""Shared look for every page: Groww-inspired palette (independent concept, not a Groww product)."""
import streamlit as st

GREEN, GREEN_DARK, BLUE, INK, MUTED, SURFACE, LINE, DRIFT = "#04B488", "#00875F", "#5367FF", "#44475B", "#6B6E80", "#F6F7F9", "#E7E8EC", "#A3A8B4"
NOTICE = ("Independent student research for a NextLeap course. Not affiliated with Groww. Not investment advice: this engine describes what "
          "investors wrote in public comments and never recommends a fund, stock or action.")

CSS = f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
html, body, p, li, h1, h2, h3, h4, label, input, textarea, button, .stMarkdown, [data-testid="stSidebarNav"] span:not([data-testid="stIconMaterial"]), [data-testid="stMetricValue"], [data-testid="stCaptionContainer"] {{ font-family: "Inter", "GrowwSans", system-ui, sans-serif; }}
[data-testid="stIconMaterial"] {{ font-family: "Material Symbols Rounded" !important; }}
[data-testid="stDecoration"] {{ display: none; }}
.block-container {{ padding-top: 1.6rem; max-width: 1100px; }}
h1, h2, h3 {{ color: {INK} !important; letter-spacing: -0.015em; }}
h1 {{ font-weight: 600 !important; font-size: 2.1rem !important; line-height: 1.2 !important; }}
h2 {{ font-weight: 600 !important; font-size: 1.45rem !important; }}
h3 {{ font-weight: 600 !important; }}
p, li {{ color: {INK}; }}
.stButton button {{ border-radius: 8px; border: 1px solid {LINE}; color: {INK}; font-weight: 500; background: #fff; }}
.stButton button:hover {{ border-color: {GREEN}; color: {GREEN_DARK}; }}
[data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {LINE}; }}
[data-testid="stSidebarNav"] a span {{ color: {INK}; font-weight: 500; }}
[data-testid="stChatMessage"] {{ border-radius: 12px; }}
.nl-brand {{ display: flex; align-items: center; gap: 10px; font-weight: 600; color: {INK}; margin-bottom: 6px; }}
.nl-brand i {{ width: 12px; height: 12px; border-radius: 50%; background: {GREEN}; display: inline-block; }}
.nl-notice {{ background: {SURFACE}; border-radius: 8px; padding: 8px 12px; font-size: 0.82rem; color: {MUTED}; }}
.nl-chip {{ display: inline-block; font-size: 0.76rem; padding: 2px 10px; margin: 2px 4px 2px 0; border-radius: 99px; background: #EEF0F3; color: {INK}; }}
.nl-chip.ok {{ background: #E5F7F1; color: {GREEN_DARK}; }}
.nl-chip.no {{ background: #EEF0FF; color: #3F4FD9; }}
.nl-quote {{ border-left: 3px solid {GREEN}; background: {SURFACE}; padding: 8px 12px; border-radius: 0 8px 8px 0; margin: 6px 0; color: {INK}; }}
.nl-quote .meta {{ font-size: 0.78rem; color: {MUTED}; }}
.nl-quote a {{ color: {GREEN_DARK}; }}
</style>
"""


def page(title, icon="🔎"):
    try:
        st.set_page_config(page_title=f"{title} · NL-Groww Discovery Engine", page_icon=icon, layout="wide")
    except Exception:
        pass   # already set by the app entry point
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"<div class='nl-brand'><i></i>NL-Groww Discovery Engine</div><div class='nl-notice'>{NOTICE}</div>", unsafe_allow_html=True)


def chips(checks):
    html = ""
    for text, ok in checks:
        cls = "ok" if ok is True else "no" if ok is False else ""
        html += f"<span class='nl-chip {cls}'>{text}</span>"
    st.markdown(html, unsafe_allow_html=True)


def quote(q):
    import html as h
    src = q["source"] + (": " + q["app"] if q.get("app") else "")
    meta = f"{h.escape(src)}{' · ' + str(q['year']) if q.get('year') else ''}"
    link = f" · <a href='{h.escape(q['url'])}' target='_blank'>Open source</a>" if q.get("url") else ""
    st.markdown(f"<div class='nl-quote'>“{h.escape(q['quote'])}”<div class='meta'>{meta}{link}</div></div>", unsafe_allow_html=True)


def bars(rows, label_col="label", value_col="n", title=None, color=GREEN, height=None):
    import altair as alt
    import pandas as pd
    df = pd.DataFrame(rows)
    if df.empty:
        return
    ch = (alt.Chart(df).mark_bar(color=color, cornerRadiusEnd=3)
          .encode(x=alt.X(f"{value_col}:Q", title=None, scale=alt.Scale(domain=[0, float(df[value_col].max()) * 1.18 or 1])), y=alt.Y(f"{label_col}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=320, labelOverlap=False)),
                  tooltip=[label_col, value_col] + (["pct_of_base"] if "pct_of_base" in df else []))
          .properties(height=height or max(100, 34 * len(df) + 20), title=title or ""))
    text = ch.mark_text(align="left", dx=4, color=INK).encode(text=alt.Text(f"{value_col}:Q", format=","))
    st.altair_chart(ch + text, use_container_width=True)
