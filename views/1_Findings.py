import altair as alt
import pandas as pd
import streamlit as st

from engine import data as D
from engine import ui

ui.page("Findings", "📊")
E = D.engine_data()
F, A, Q = E["funnel"], E["anatomy"], E["questions"]
lab = D.lab

drops = F["dropoffs"]
inv, vol, dr = A["type"].get("involuntary", 0), A["type"].get("voluntary", 0), A["type"].get("passive_drift", 0)
fti = A["first_time_type"].get("involuntary", 0)
ftn = sum(A["first_time_type"].values())

st.title("Almost a third of SIP drop-offs happen without the investor choosing to stop")
st.write(f"Of **{drops:,}** comments describing a SIP being skipped, paused, reduced, stopped or lapsing, **{inv:,} ({100*inv/drops:.1f}%)** "
         f"describe a lapse the investor did not choose: a failed debit, a broken mandate or autopay, or an app error. Among self-described "
         f"first-time investors it is **{fti} of {ftn} ({100*fti/ftn:.1f}%)**.")
st.caption("AI tags on public comments: directional until the hand-labelled golden set confirms them. Interviews test these patterns next.")

df = pd.DataFrame([{"type": "Voluntary: chose to stop, skip, pause or reduce", "n": vol},
                   {"type": "Involuntary: lapsed without deciding", "n": inv},
                   {"type": "Passive drift: forgot or lost track", "n": dr}])
df["pct"] = (100 * df["n"] / drops).round(1)
df["label"] = df["pct"].map(lambda x: f"{x:.1f}%")
ch = alt.Chart(df).mark_bar(cornerRadiusEnd=3).encode(
    x=alt.X("n:Q", title="Drop-off comments", scale=alt.Scale(domain=[0, vol * 1.12])), y=alt.Y("type:N", sort=None, title=None, axis=alt.Axis(labelLimit=360)),
    color=alt.Color("type:N", scale=alt.Scale(domain=list(df["type"]), range=[ui.BLUE, ui.GREEN_DARK, ui.DRIFT]), legend=None),
    tooltip=["type", "n", "pct"]).properties(height=150)
st.altair_chart(ch + ch.mark_text(align="left", dx=4, color=ui.INK).encode(text=alt.Text("label:N"), color=alt.value(ui.INK)), use_container_width=True)
st.caption("Passive drift is rarely written about, so public text under-counts it; it is a focus of the interviews.")

st.header("Answers to the brief's discovery questions")
st.write("Counts are comments whose AI tags match. A comment can carry several tags, so bars in one card do not add up to the total. "
         "These nine are the brief's starting questions; the **Ask the engine** page answers any other question about the same data.")


def card(ask, ans, rows, foot=None):
    st.markdown(f"<span style='font-size:0.85rem;font-weight:600;color:{ui.MUTED}'>{ask}</span>", unsafe_allow_html=True)
    st.markdown(f"**{ans}**")
    ui.bars([{"label": lab(k) if not isinstance(k, str) or k in D.L or k in D.SRC else k, "n": n} for k, n in rows])
    if foot:
        st.caption(foot)


q2, q7, q8 = Q["q2"], Q["q7"], Q["q8"]
c1, c2 = st.columns(2)
with c1:
    card("1. Why first-time investors start, and what they expect",
         f"{Q['q1']['started_n']:,} comments describe starting a SIP. Most say they decided themselves; friends, family and social media are the visible outside triggers.",
         [r for r in Q["q1"]["influencer"] if r[0] != "self"], "Expectations about returns show up mainly in community posts (see question 3).")
with c2:
    card("2. How behaviour changes after starting",
         f"Drop-off talk roughly doubles after the first quarter: {q2['first_instalments_1_3m']['drop_pct']}% of month 1 to 3 comments describe a drop-off versus {q2['months_4_12']['drop_pct']}% in months 4 to 12.",
         [(f"{lab(s)}: share describing a drop-off (%)", q2[s]["drop_pct"]) for s in ["first_instalments_1_3m", "months_4_12", "beyond_12m"]],
         "Only comments where the stage is clear.")
c1, c2 = st.columns(2)
with c1:
    card("3. What leads to pausing, reducing or stopping",
         "Platform problems lead even among deliberate stops (985 of 2,343 voluntary drop-offs). Return and expectation gaps come next (683), then money pressure (230).",
         Q["q3"]["drivers"][:7], f"Across {Q['q3']['n']:,} drop-off comments. First-time investors (n={Q['q3']['ft_n']}) put payment and mandate failure second.")
with c2:
    card("4. What first-time investors check",
         "Returns first, and whether the instalment went through second; XIRR and NAV matter far less to them than to experienced investors.",
         Q["q4"]["first_time"], "First-time investors only. How often they check is rarely stated in text; interviews cover it.")
c1, c2 = st.columns(2)
with c1:
    card("5. What confuses or worries them inside the app",
         "Friction and unanswered support worry people most, then missing controls and payment failures. Confusing figures are a smaller but steady theme.", Q["q5"])
with c2:
    card("6. What they do outside the app when unsure",
         "First-time investors turn to YouTube and Reddit before customer support; experienced investors go to support, AMC records and other trackers.",
         Q["q6"]["first_time"], f"First-time investors only ({F['first_time']:,} comments).")
c1, c2 = st.columns(2)
with c1:
    card("7. How continuers differ from those who drop off",
         "Continuers credit automation and habit; drop-offs cite failures and support. Both mention weak returns, so returns alone do not decide who stays.",
         [(f"Still investing: {lab(k)}", n) for k, n in q7["continuer"][:3]] + [(f"Dropped off: {lab(k)}", n) for k, n in q7["dropoff"][:3]],
         f"Still investing n={q7['continuers_n']:,}; dropped off n={q7['dropoffs_n']:,}.")
with c2:
    seg = [(f"{lab(k)} (n={v['n']:,}): % describing a drop-off", v["pct_dropoff"]) for f in ("income", "age_hint") for k, v in q8[f].items()]
    card("8. Differences across segments",
         "Younger investors and students describe fewer drop-offs; salaried and variable-income writers name cash-flow changes as their top reason.", seg,
         "Few comments state income or age, so segment cuts are thin; interviews and the survey fill this gap.")
card("9. Unmet needs that appear consistently",
     "Clear explanation of returns, support that resolves, and instalments that reliably go through are the most repeated asks.",
     [(n["need"], n["n"]) for n in Q["q9"]["needs"]],
     f"From {Q['q9']['need_items']:,} comments where the AI recorded a need, grouped by transparent keyword rules. About {Q['q9']['advice_seekers']:,} comments ask which fund to pick; the engine records that as a need but never answers it.")
