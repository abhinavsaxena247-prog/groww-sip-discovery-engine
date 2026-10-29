import streamlit as st

from engine import data as D
from engine import guard as G
from engine import llm
from engine import pipeline as P
from engine import ui

ui.page("Tag a comment", "🏷️")
E = D.engine_data()
st.title("Tag any investor comment with the engine's codebook")
st.write("Paste a comment (English, Hinglish or Hindi). The engine applies the same codebook and prompt used on the corpus and runs the same guardrail checks. "
         "The examples show the tags the corpus model actually gave those comments.")

SCHEMA = {"type": "OBJECT", "properties": {
    "relevant": {"type": "BOOLEAN"}, "first_time_signal": {"type": "STRING", "enum": ["yes", "no", "unclear"]},
    "lifecycle_stage": {"type": "STRING", "enum": P.CODE["lifecycle_stage"]},
    "event": {"type": "ARRAY", "items": {"type": "STRING", "enum": P.CODE["event"]}}, "dropoff_type": {"type": "STRING", "enum": P.CODE["dropoff_type"]},
    "drivers": {"type": "ARRAY", "items": {"type": "STRING", "enum": P.CODE["drivers"]}},
    "what_they_check": {"type": "ARRAY", "items": {"type": "STRING", "enum": P.CODE["what_they_check"]}},
    "outside_app_behaviour": {"type": "ARRAY", "items": {"type": "STRING", "enum": P.CODE["outside_app_behaviour"]}},
    "unmet_need": {"type": "STRING"}, "evidence_span": {"type": "STRING"}, "severity": {"type": "INTEGER"}},
    "required": ["relevant", "first_time_signal", "lifecycle_stage", "event", "dropoff_type", "drivers", "what_they_check", "outside_app_behaviour", "unmet_need", "evidence_span", "severity"]}
RULES = ("You tag Indian retail-investor feedback for a research study about SIP continuation. Tag ONLY what the text states or clearly implies; if unsure use "
         "'unclear', 'none', [] or ''. relevant=true only if the writer describes their OWN experience, behaviour, question, worry or need about SIPs or mutual funds. "
         "dropoff_type is 'none' unless a SIP was skipped, paused, reduced, stopped, cancelled or lapsed; voluntary = they chose it; involuntary = it failed or lapsed "
         "without their decision (mandate, autopay, bank debit, OTP, app error); passive_drift = forgot or lost track. severity: 1 mention, 2 changed SIP behaviour, "
         "3 stopped, lapsed, withdrew everything or left the platform. unmet_need: a neutral phrase only if the writer states a want, else ''. evidence_span: up to 20 "
         "words copied verbatim. Never give investment opinions or name funds in your own words.")

ex = E["examples"]
cols = st.columns(len(ex))
for i, x in enumerate(ex):
    if cols[i].button("Example: " + x["label"], use_container_width=True):
        st.session_state.tag_text = x["text"]
        st.session_state.tag_out = (x["tags"], f"Corpus tags for this {x['label'].lower()} ({x['model']})")
text = st.text_area("Comment to tag", st.session_state.get("tag_text", ex[0]["text"]), height=140, max_chars=800)
if st.button("Tag with AI", type="primary"):
    chk = G.check_input(text)
    if chk["verdict"] in ("abuse", "pii", "injection", "too_long", "empty"):
        st.warning({"abuse": "This text contains abusive language, so the engine will not process it.",
                    "pii": f"This text looks like it contains personal data ({chk.get('kind')}). Remove it first; nothing was sent.",
                    "injection": "This text tries to change the engine's rules, so it was not processed.",
                    "too_long": "Keep the comment under 800 characters.", "empty": "Paste a comment first."}[chk["verdict"]])
    else:
        try:
            with st.spinner("Tagging…"):
                tags, model = llm.json_call(RULES + "\n\nTEXT:\n" + text, SCHEMA)
            st.session_state.tag_out = (tags, f"Live tags ({model})")
        except llm.QuotaExhausted:
            st.info("The free AI quota is used up for today, so live tagging is paused. The examples still show real corpus tags.")
tags, src = st.session_state.get("tag_out", (ex[0]["tags"], f"Corpus tags for this {ex[0]['label'].lower()} ({ex[0]['model']})"))
st.subheader(src)
lst = lambda v: ", ".join(D.lab(x) for x in v) if v else "None"
st.table({"Field": ["Relevant", "First-time investor", "Stage", "What happened", "Drop-off type", "Reasons", "Checks", "Outside the app", "Unmet need", "Evidence", "Severity"],
          "Tag": ["Yes" if tags.get("relevant") else "No", D.lab(tags.get("first_time_signal", "unclear")), D.lab(tags.get("lifecycle_stage", "unclear")),
                  lst(tags.get("event")), D.lab(tags.get("dropoff_type", "none")), lst(tags.get("drivers")), lst(tags.get("what_they_check")),
                  lst(tags.get("outside_app_behaviour")), tags.get("unmet_need") or "None stated", tags.get("evidence_span") or "None", f"{tags.get('severity', 1)} of 3"]})
oc = G.check_output(" ".join([tags.get("unmet_need", ""), tags.get("evidence_span", "")]))
ui.chips([("Guardrail check passed: no fund named, no advice, no urgency" if oc["pass"] else "Guardrail flag: " + oc["issues"][0], oc["pass"])])
