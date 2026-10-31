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
@media (min-width: 1200px) {{ [data-testid="stSidebarCollapseButton"] {{ display: none !important; }} }}
@media (min-width: 768px) and (max-width: 1199px) {{ [data-testid="stSidebar"][aria-expanded="true"] {{ min-width: 230px !important; max-width: 230px !important; }}
  .stButton button p {{ font-size: 0.88rem; }} }}
.block-container {{ padding-top: 4.2rem; max-width: 1100px; }}
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
/* Groww-style accents: green brand bar, green outline buttons, green active nav, green focus */
.nl-bar {{ display:flex; align-items:center; justify-content:space-between; background:#fff; border:1px solid {LINE}; border-top:4px solid {GREEN};
          border-radius:10px; padding:10px 16px; margin-bottom:10px; }}
.nl-bar .logo {{ display:flex; align-items:center; gap:10px; font-weight:600; font-size:1.05rem; color:{INK}; }}
.nl-bar .logo b {{ width:28px; height:28px; border-radius:50%; background:{GREEN}; display:inline-block; }}
.nl-bar .tag {{ font-size:0.76rem; color:{GREEN_DARK}; background:#E5F7F1; border-radius:99px; padding:3px 10px; font-weight:500; }}
.nl-sublabel {{ font-size:0.8rem; color:{MUTED}; font-weight:600; margin:10px 0 4px; text-transform:uppercase; letter-spacing:.05em; }}
.nl-notice {{ background:#F0FAF6 !important; border-left:3px solid {GREEN}; color:{INK} !important; }}
.stButton button {{ border:1px solid {GREEN} !important; color:{GREEN_DARK} !important; background:#fff !important; }}
.stButton button:hover {{ background:#E5F7F1 !important; }}
.stButton button[kind="primary"] {{ background:{GREEN} !important; color:#fff !important; }}
[data-testid="stSidebarNav"] a[aria-current="page"], [data-testid="stSidebarNavLink"][aria-current="page"] {{ background:#E5F7F1 !important; }}
[data-testid="stSidebarNav"] a[aria-current="page"] span {{ color:{GREEN_DARK} !important; font-weight:600; }}
[data-testid="stChatInput"] > div {{ border:1px solid {GREEN} !important; border-radius:10px; }}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ color:{GREEN_DARK} !important; }}
[data-testid="stMetricValue"] {{ color:{GREEN_DARK}; }}
.stTabs [aria-selected="true"] {{ color:{GREEN_DARK} !important; }}
</style>
"""


def page(title, icon="🔎"):
    try:
        st.set_page_config(page_title=f"{title} · NL-Groww Discovery Engine", page_icon=icon, layout="wide")
    except Exception:
        pass   # already set by the app entry point
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"<div class='nl-bar'><div class='logo'><b></b>NL-Groww Discovery Engine</div><span class='tag'>Independent concept · Not investment advice</span></div>"
                f"<div class='nl-notice'>{NOTICE}</div>", unsafe_allow_html=True)


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


def bars(rows, label_col="label", value_col="n", title=None, color=GREEN, height=None, sort=True):
    import altair as alt
    import pandas as pd
    df = pd.DataFrame(rows)
    if df.empty:
        return
    if title:   # title as text above the chart, so it never eats into the plot's height
        st.markdown(f"<div style='font-weight:600;font-size:0.9rem;margin:4px 0 -6px'>{title}</div>", unsafe_allow_html=True)
    ch = (alt.Chart(df).mark_bar(color=color, cornerRadiusEnd=3)
          .encode(x=alt.X(f"{value_col}:Q", title=None, scale=alt.Scale(domain=[0, float(df[value_col].max()) * 1.18 or 1])), y=alt.Y(f"{label_col}:N", sort="-x" if sort else list(df[label_col]), title=None, axis=alt.Axis(labelLimit=320, labelOverlap=False)),
                  tooltip=[label_col, value_col] + (["pct_of_base"] if "pct_of_base" in df else []))
          .properties(height=height or max(110, 36 * len(df) + 30)))
    text = ch.mark_text(align="left", dx=4, color=INK).encode(text=alt.Text(f"{value_col}:Q", format=","))
    st.altair_chart(ch + text, use_container_width=True)
