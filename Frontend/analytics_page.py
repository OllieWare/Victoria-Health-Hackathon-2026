import pandas as pd
import requests
import streamlit as st

BACKEND_BASE_URL = "http://localhost:8000"
TRIAGE_LABELS = {
    1: "Resuscitation",
    2: "Emergent",
    3: "Urgent",
    4: "Less Urgent",
    5: "Non-Urgent",
}


def triage_display(level: int) -> str:
    return f"CTAS {level} - {TRIAGE_LABELS.get(level, 'Unknown')}"


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
            triage_display(predicted_level),
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
