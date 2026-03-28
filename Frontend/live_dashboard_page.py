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

st.set_page_config(page_title="Live Dashboard", page_icon=":material/monitoring:")
st.title("Live Dashboard")
st.caption("Auto-refreshes every 10 seconds.")


@st.fragment(run_every="10s")
def dashboard() -> None:
    st.subheader("Current Metrics")
    try:
        response = requests.get(f"{BACKEND_BASE_URL}/api/dashboard", timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        st.warning(
            f"Using placeholder values because the backend is unavailable: {exc}"
        )
        data = {"active_patients": 24, "alerts": 3, "avg_wait_minutes": 18}

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Patients", data.get("active_patients", "N/A"))
    col2.metric("Alerts", data.get("alerts", "N/A"))
    col3.metric("Avg Wait (min)", data.get("avg_wait_minutes", "N/A"))
    st.caption("Backend endpoint: GET /api/dashboard")


dashboard()
