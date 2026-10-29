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
st.dataframe(df, hide_index=True, use_container_width=True,
             column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f")})

st.header("Each channel shows a different side of the problem")
st.write("Share of each source's relevant comments that fall in each area. App reviews describe failures; communities describe expectations and money pressure. Raw counts alone would favour the loudest channel.")
hm = [{"Area": r["Area"], "Source": D.SRC[s], "Share (%)": o["per_source_pct"].get(s, 0)} for o, r in zip(OPP, rows) for s in D.SRC_ORDER]
h = pd.DataFrame(hm)
base = alt.Chart(h).encode(x=alt.X("Source:N", sort=[D.SRC[s] for s in D.SRC_ORDER], title=None), y=alt.Y("Area:N", sort=list(df["Area"]), title=None, axis=alt.Axis(labelLimit=300)))
heat = base.mark_rect().encode(color=alt.Color("Share (%):Q", scale=alt.Scale(range=["#F2F5F7", ui.GREEN_DARK]), legend=None), tooltip=["Area", "Source", "Share (%)"])
txt = base.mark_text(fontSize=12).encode(text=alt.Text("Share (%):Q", format=".1f"), color=alt.condition("datum['Share (%)'] > 25", alt.value("white"), alt.value(ui.INK)))
st.altair_chart((heat + txt).properties(height=320), use_container_width=True)
st.caption("Opportunity scores and shares come from AI tags; the golden-set check measures how far the tags can be trusted.")
