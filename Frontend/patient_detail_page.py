import os

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

st.set_page_config(page_title="Patient Detail", page_icon=":material/person:")
st.title("Patient Detail")

patient_id = st.text_input("Patient ID", value="patient-123")

if st.button("Load record"):
    try:
        response = requests.get(
            f"{BACKEND_BASE_URL}/api/patients/{patient_id}",
            timeout=5,
        )
        response.raise_for_status()
        patient = response.json()
    except requests.RequestException as exc:
        st.warning(
            f"Using placeholder record because the backend is unavailable: {exc}"
        )
        patient = {
            "id": patient_id,
            "name": "Jane Doe",
            "age": 47,
            "status": "Stable",
            "last_updated": "2026-03-28T09:30:00Z",
        }

    st.json(patient)
    st.caption("Backend endpoint: GET /api/patients/{patient_id}")
