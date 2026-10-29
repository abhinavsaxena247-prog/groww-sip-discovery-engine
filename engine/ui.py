"""Shared look for every page: Groww-inspired palette (independent concept, not a Groww product)."""
import streamlit as st

GREEN, GREEN_DARK, BLUE, INK, MUTED, SURFACE, LINE, DRIFT = "#04B488", "#027F5F", "#5669FF", "#2C2E3A", "#5F6373", "#F2F5F7", "#DDE3E8", "#A3A8B4"
NOTICE = ("Independent student research for a NextLeap course. Not affiliated with Groww. Not investment advice: this engine describes what "
          "investors wrote in public comments and never recommends a fund, stock or action.")

CSS = f"""
<style>
.block-container {{ padding-top: 2rem; max-width: 1100px; }}
h1, h2, h3 {{ color: {INK}; letter-spacing: -0.01em; }}
.nl-notice {{ background: {SURFACE}; border-radius: 10px; padding: 8px 12px; font-size: 0.85rem; color: {MUTED}; }}
.nl-chip {{ display: inline-block; font-size: 0.78rem; padding: 2px 9px; margin: 2px 4px 2px 0; border-radius: 99px; background: #E9EEF1; color: {INK}; }}
.nl-chip.ok {{ background: #E3F6F0; color: {GREEN_DARK}; }}
.nl-chip.no {{ background: #ECEEFF; color: #3D4FD6; }}
.nl-quote {{ border-left: 3px solid {GREEN}; background: {SURFACE}; padding: 8px 12px; border-radius: 0 8px 8px 0; margin: 6px 0; }}
.nl-quote .meta {{ font-size: 0.8rem; color: {MUTED}; }}
.nl-big {{ font-size: 2rem; font-weight: 800; color: {INK}; line-height: 1.1; }}
.nl-card {{ border: 1px solid {LINE}; border-radius: 12px; padding: 14px 16px; height: 100%; }}
.nl-card .ask {{ font-size: 0.85rem; color: {MUTED}; font-weight: 600; }}
</style>
"""


def page(title, icon="🔎"):
    try:
        st.set_page_config(page_title=f"{title} · NL-Groww Discovery Engine", page_icon=icon, layout="wide")
    except Exception:
        pass   # already set by the app entry point
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"<div class='nl-notice'>{NOTICE}</div>", unsafe_allow_html=True)


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
