import altair as alt
import pandas as pd
import streamlit as st

from engine import data as D
from engine import ui

ui.page("Opportunities", "🎯")
E = D.engine_data()
OPP = E["opportunities"]

st.title("SIPs that lapse without the investor choosing are the largest opportunity")
st.write("Each comment can sit in more than one area. The score multiplies four things: how many drop-offs the area touches, how severe they are, "
         "how much a product change can fix it, and how well a fix fits the brief's rules (no advice, no fear or urgency nudges). "
         "The last two are analyst judgements and are written out per row so they can be challenged.")

rows = []
for o in OPP:
    rows.append({"Area": o["area"].split(". ", 1)[1].split(" (")[0], "Score": o["opportunity_score"], "Comments": o["n"],
                 "Share of all drop-offs (%)": o["share_of_all_dropoffs_pct"], "Avg severity (1-3)": o["avg_severity"],
                 "First-time investors": o["first_time_n"], "Groww reviews": o["groww_n"],
                 "Fixable (1-3)": o["addressability_1to3"], "Fits rules (1-3)": o["constraint_fit_1to3"], "Why": o["why"]})
df = pd.DataFrame(rows)
import html as _h
st.markdown("""<style>
.op{border:1px solid #E7E8EC;border-radius:10px;padding:12px 14px;margin:8px 0;background:#fff}
.op.top{border-color:#04B488;box-shadow:0 0 0 1px #04B488 inset}
.op h4{margin:0 0 6px;font-size:1rem;color:#44475B;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.op .tag{font-size:.72rem;background:#E5F7F1;color:#00785A;border-radius:99px;padding:2px 8px;font-weight:600}
.op .bar{height:8px;background:#EEF0F3;border-radius:99px;overflow:hidden;margin:4px 0 8px}
.op .bar i{display:block;height:100%;background:#04B488}
.op .nums{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:.85rem;color:#44475B}
.op .nums b{font-variant-numeric:tabular-nums}
.op .why{font-size:.85rem;color:#6B6E80;margin-top:6px}
</style>""", unsafe_allow_html=True)
for i, (o, r) in enumerate(zip(OPP, rows), start=1):
    chosen = o["area"].startswith("A.")
    st.markdown(
        f"<div class='op{' top' if chosen else ''}'><h4>{i}. {_h.escape(r['Area'])} <span style='font-weight:500;color:#6B6E80'>score {r['Score']}</span>"
        + ("<span class='tag'>Chosen for interviews</span>" if chosen else "") + "</h4>"
        f"<div class='bar'><i style='width:{min(100, r['Score'])}%'></i></div>"
        f"<div class='nums'><span><b>{r['Comments']:,}</b> comments</span><span><b>{r['Share of all drop-offs (%)']}%</b> of all drop-offs</span>"
        f"<span>severity <b>{r['Avg severity (1-3)']}</b> of 3</span><span><b>{r['First-time investors']:,}</b> first-time investors</span>"
        f"<span><b>{r['Groww reviews']:,}</b> Groww reviews</span><span>fixable by product <b>{r['Fixable (1-3)']}</b>/3</span>"
        f"<span>fits the brief's rules <b>{r['Fits rules (1-3)']}</b>/3</span></div>"
        f"<div class='why'>Why: {_h.escape(r['Why'])}</div></div>", unsafe_allow_html=True)
st.caption("Score = (share of all drop-offs ÷ largest share) × (severity ÷ 3) × (fixable ÷ 3) × (fits rules ÷ 3) × 100. "
           "Read the comments behind any area on the Evidence explorer page.")

st.header("Each channel shows a different side of the problem")
st.write("Share of each source's relevant comments that fall in each area. App reviews describe failures; communities describe expectations and money pressure. Raw counts alone would favour the loudest channel.")
hm = [{"Area": r["Area"], "Source": D.SRC[s], "Share (%)": o["per_source_pct"].get(s, 0)} for o, r in zip(OPP, rows) for s in D.SRC_ORDER]
h = pd.DataFrame(hm)
base = alt.Chart(h).encode(x=alt.X("Source:N", sort=[D.SRC[s] for s in D.SRC_ORDER], title=None, axis=alt.Axis(labelAngle=0, orient="top", labelLimit=90)), y=alt.Y("Area:N", sort=list(df["Area"]), title=None, axis=alt.Axis(labelLimit=300)))
heat = base.mark_rect().encode(color=alt.Color("Share (%):Q", scale=alt.Scale(range=["#F2F5F7", ui.GREEN_DARK]), legend=None), tooltip=["Area", "Source", "Share (%)"])
txt = base.mark_text(fontSize=12).encode(text=alt.Text("Share (%):Q", format=".1f"), color=alt.condition("datum['Share (%)'] > 25", alt.value("white"), alt.value(ui.INK)))
st.altair_chart((heat + txt).properties(height=320), use_container_width=True)
st.caption("Opportunity scores and shares come from AI tags. The hand-labelled golden set found 59% first-pass agreement; the AI over-counts forum comments, "
           "but area A's share of drop-offs barely moves without them: 29.6% with all sources, 29.5% with app stores and Reddit only (see Quality and evals).")
