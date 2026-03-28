import os

import pandas as pd
import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def get_backend_base_url() -> str:
    env_value = os.getenv("BACKEND_BASE_URL")
    if env_value:
        return env_value

    try:
        return st.secrets["BACKEND_BASE_URL"]
    except (KeyError, StreamlitSecretNotFoundError):
        return "https://victoria-health-hackathon-2026.onrender.com"


BACKEND_BASE_URL = get_backend_base_url()
TRIAGE_LABELS = {
    1: "Resuscitation",
    2: "Emergent",
    3: "Urgent",
    4: "Less Urgent",
    5: "Non-Urgent",
}
TRIAGE_GUIDANCE = {
    1: {
        "where_to_go": "Emergency Department immediately",
        "meaning": "Life-threatening conditions requiring instant intervention. Seconds matter.",
        "examples": [
            "Cardiac arrest",
            "Severe trauma with shock",
            "Airway obstruction",
            "Unresponsive patient",
        ],
        "why": "Only a hospital emergency department has the equipment and staff to stabilize and resuscitate.",
    },
    2: {
        "where_to_go": "Emergency Department (high priority)",
        "meaning": "Very serious conditions that are not yet crashing but could deteriorate quickly.",
        "examples": [
            "Chest pain suspicious for heart attack",
            "Stroke symptoms",
            "Severe shortness of breath",
            "Major fractures",
            "High-risk abdominal pain",
        ],
        "why": "These require rapid diagnostics, imaging, and interventions that only an ER can provide.",
    },
    3: {
        "where_to_go": "Urgent Care, or Emergency Department if symptoms worsen or urgent care is unavailable",
        "meaning": "Moderate severity. Needs medical attention within hours, not days, but not immediately life-threatening.",
        "examples": [
            "Moderate asthma flare",
            "Dehydration needing IV fluids",
            "Simple fractures",
            "High fever with concerning symptoms",
            "Wounds needing stitches",
        ],
        "why": "Most Level 3 issues can be managed with on-site diagnostics and treatments available at urgent care centers.",
    },
    4: {
        "where_to_go": "General Practitioner, Walk-in Clinic, or over-the-counter care for minor issues",
        "meaning": "Mild conditions that require medical evaluation but are not time-sensitive.",
        "examples": [
            "Mild infections like ear, throat, or urinary infections",
            "Minor sprains",
            "Rashes",
            "Medication refills",
            "Mild cold or flu symptoms",
        ],
        "why": "These conditions can usually be managed safely outside the hospital with simple treatments or routine follow-up.",
    },
    5: {
        "where_to_go": "General Practitioner, Walk-in Clinic, virtual care, or self-care",
        "meaning": "Non-urgent concerns that are stable and appropriate for routine outpatient care.",
        "examples": [
            "Minor symptom checks",
            "Routine prescription questions",
            "Chronic issue follow-up",
            "Very mild cold symptoms",
            "Self-limited minor complaints",
        ],
        "why": "Level 5 cases generally do not need hospital resources and are better managed through primary care or self-care.",
    },
}


def triage_display(level: int) -> str:
    return f"CTAS {level} - {TRIAGE_LABELS.get(level, 'Unknown')}"


def triage_metric_display(level: int) -> str:
    return f"CTAS {level}\n{TRIAGE_LABELS.get(level, 'Unknown')}"


st.set_page_config(page_title="Analytics", page_icon=":material/insights:")
st.title("Analytics")
st.caption(
    "Use the backend triage model to estimate likely CTAS level from a patient summary."
)

default_query = (
    "52 year old with chest pain and shortness of breath, troponin 0.42, "
    "sodium 133, taking metoprolol"
)

with st.form("triage_prediction_form"):
    query = st.text_area(
        "Patient summary",
        value=default_query,
        height=160,
        help="Include the presenting complaint and any medication or lab details that might matter.",
    )
    submitted = st.form_submit_button("Predict triage level", use_container_width=True)

if submitted:
    try:
        response = requests.post(
            f"{BACKEND_BASE_URL}/api/triage/predict",
            json={"query": query},
            timeout=15,
        )
        response.raise_for_status()
        prediction = response.json()
    except requests.RequestException as exc:
        st.error(f"Could not reach the backend triage endpoint: {exc}")
    else:
        predicted_level = prediction["predicted_triage_level"]
        baseline_level = prediction["chief_complaint_baseline_triage"]

        metric_col, complaint_col = st.columns([1, 1.4])
        metric_col.metric(
            "Likely triage level",
            triage_metric_display(predicted_level),
            delta=f"Baseline {triage_display(baseline_level)}",
        )
        complaint_col.write("**Identified chief complaint**")
        complaint_col.write(
            f"{prediction['chief_complaint'].title()} "
            f"({int(prediction['chief_complaint_confidence'] * 100)}% confidence)"
        )

        probability_df = pd.DataFrame(prediction["probabilities"])
        probability_df["label"] = probability_df["triage_level"].apply(triage_display)
        probability_df["probability_pct"] = probability_df["probability"] * 100
        chart_df = probability_df.set_index("label")[["probability_pct"]]

        st.subheader("Probability breakdown")
        st.bar_chart(chart_df)
        st.dataframe(
            probability_df[["label", "probability_pct"]].rename(
                columns={"label": "Triage level", "probability_pct": "Probability (%)"}
            ),
            use_container_width=True,
            hide_index=True,
        )

        guidance = TRIAGE_GUIDANCE[predicted_level]
        st.subheader("Recommended where to go")
        st.info(guidance["where_to_go"])

        guidance_col, examples_col = st.columns([1.3, 1])
        guidance_col.write("**What this level means**")
        guidance_col.write(guidance["meaning"])
        guidance_col.write("**Why this destination fits**")
        guidance_col.write(guidance["why"])

        examples_col.write("**Common examples**")
        for example in guidance["examples"]:
            examples_col.write(f"- {example}")

        details_col, meds_col = st.columns(2)
        details_col.write("**Extracted labs**")
        if prediction["extracted_labs"]:
            details_col.json(prediction["extracted_labs"])
        else:
            details_col.caption("No supported lab values detected in the text.")

        meds_col.write("**Extracted medications**")
        if prediction["extracted_medications"]:
            meds_col.write(", ".join(prediction["extracted_medications"]))
        else:
            meds_col.caption("No supported medications detected in the text.")

st.divider()
st.caption("Backend endpoint: POST /api/triage/predict")
