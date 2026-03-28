# Frontend

These commands are written for PowerShell on Windows. Copy and paste them one line at a time.

## 1. Go to the frontend folder

```powershell
cd Frontend
```

## 2. Create a virtual environment

```powershell
python -m venv .venv
```

## 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Install frontend dependencies

```powershell
pip install -r requirements.txt
```

## 5. Run the live dashboard page

```powershell
streamlit run .\live_dashboard_page.py
```

Open this page in your browser:

```text
http://localhost:8501
```

## 6. Stop Streamlit

In the same PowerShell window:

```powershell
Ctrl+C
```

## 7. Run the patient detail page

```powershell
streamlit run .\patient_detail_page.py
```

Open this page in your browser:

```text
http://localhost:8501
```

## 8. Stop Streamlit

In the same PowerShell window:

```powershell
Ctrl+C
```

## 9. Run the analytics page

```powershell
streamlit run .\analytics_page.py
```

Open this page in your browser:

```text
http://localhost:8501
```

## 10. What to expect right now

The frontend pages currently call backend placeholder endpoints at `http://localhost:8000`.

The current backend does not yet provide these frontend endpoints:

- `GET /api/dashboard`
- `GET /api/patients/{patient_id}`
- `GET /api/analytics/visits`

So the pages should still load, but they will show warning messages and fallback demo data until those endpoints are added.

## 11. Stop Streamlit

In the same PowerShell window:

```powershell
Ctrl+C
```
