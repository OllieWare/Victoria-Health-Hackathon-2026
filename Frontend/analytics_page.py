import pandas as pd
import requests
import streamlit as st

BACKEND_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="Analytics", page_icon=":material/insights:")
st.title("Analytics")

try:
    response = requests.get(f"{BACKEND_BASE_URL}/api/analytics/visits", timeout=5)
    response.raise_for_status()
    rows = response.json()
except requests.RequestException as exc:
    st.warning(f"Using placeholder data because the backend is unavailable: {exc}")
    rows = [
        {"day": "Mon", "visits": 18},
        {"day": "Tue", "visits": 25},
        {"day": "Wed", "visits": 22},
        {"day": "Thu", "visits": 29},
        {"day": "Fri", "visits": 31},
    ]

df = pd.DataFrame(rows)
st.line_chart(df.set_index("day"))
st.dataframe(df, use_container_width=True)
st.caption("Backend endpoint: GET /api/analytics/visits")
