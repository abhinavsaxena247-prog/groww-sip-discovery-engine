import pandas as pd
import streamlit as st

from engine import data as D
from engine import guard as G
from engine import ui

ui.page("Evidence explorer", "🗂️")
C = D.corpus()
ci, d = C["ci"], C["dict"]

st.title("Read the evidence behind every number")
st.write("Filter the 21,445 tagged comments and read the short verbatim span the AI picked to justify its tags. Usernames were never collected. "
         "Spans containing abuse, personal data or fund names are hidden.")

AREAS = {"Any": {}, "SIP lapses without deciding": {"driver_any": ["payment_mandate_failure"]},
         "No way to pause, skip or change": {"driver_any": ["missing_control_pause_skip_modify"]},
         "Cash-flow or income change": {"driver_any": ["cashflow_or_income_change", "emergency_or_goal_need_for_money"]},
         "Returns and expectations": {"driver_any": ["returns_below_expectation", "negative_or_volatile_returns", "confusing_numbers_or_terms", "goal_clarity_or_tracking"]},
         "Trust and support": {"driver_any": ["trust_or_support_failure"]}, "App bugs and friction": {"driver_any": ["app_friction_or_bug"]},
         "Fees and charges": {"driver_any": ["fees_or_hidden_charges"]}}
c1, c2, c3, c4 = st.columns(4)
area = c1.selectbox("Area", list(AREAS), index=1)
src = c2.multiselect("Source", [D.SRC[s] for s in D.SRC_ORDER])
drop = c3.selectbox("Drop-off type", ["Any", "Voluntary", "Involuntary", "Passive drift", "None described"])
ft = c4.selectbox("Investor", ["Anyone", "Self-described first-time"])
c5, c6 = st.columns([1, 2])
app = c5.selectbox("App (store reviews)", ["Any"] + sorted(a for a in d["app"] if a and a not in ("forum", "youtube") and not a.startswith("r/")))
kw = c6.text_input("Keyword in the quote or need (use | for alternatives)", "")

f = dict(AREAS[area])
if src:
    f["source"] = [k for k, v in D.SRC.items() if v in src]
if drop != "Any":
    f["drop"] = [{"Voluntary": "voluntary", "Involuntary": "involuntary", "Passive drift": "passive_drift", "None described": "none"}[drop]]
if ft != "Anyone":
    f["first_time"] = True
if app != "Any":
    f["app"] = [app]
if kw.strip():
    chk = G.check_input(kw)
    if chk["verdict"] in ("abuse", "pii", "injection"):
        st.warning("That keyword can't be used here (" + chk["reason"].lower() + ").")
    else:
        f["keyword"] = kw.strip().lower()

m = D._matcher(f)
rows = [r for r in C["rows"] if m(r)]
st.markdown(f"**{len(rows):,}** matching comments ({100*len(rows)/len(C['rows']):.1f}% of all relevant comments).")


def safe(e):
    return e and not G.FUNDS.search(e) and G.check_input(e)["verdict"] not in ("abuse", "pii")


show = [r for r in sorted(rows, key=lambda r: -r[ci["sev"]]) if safe(r[ci["evidence"]])][:200]
table = pd.DataFrame([{"Quote": r[ci["evidence"]], "Source": D.SRC[d["source"][r[ci["source"]]]],
                       "App": "" if d["app"][r[ci["app"]]] in ("forum", "youtube") else d["app"][r[ci["app"]]],
                       "Drop-off": D.lab(d["drop"][r[ci["drop"]]]) if r[ci["drop"]] >= 0 else "", "Severity": r[ci["sev"]],
                       "Year": r[ci["year"]] or None, "Need recorded": r[ci["need"]], "Link": r[ci["url"]] or None} for r in show])
if table.empty:
    st.info("No comments match these filters. Try removing one.")
else:
    st.dataframe(table, hide_index=True, use_container_width=True, height=520,
                 column_config={"Link": st.column_config.LinkColumn("Link", display_text="Open"), "Quote": st.column_config.TextColumn(width="large")})
    st.caption(f"Showing the {len(show)} most severe of {len(rows):,}. Severity: 1 mention, 2 changed SIP behaviour, 3 stopped, lapsed or left.")
