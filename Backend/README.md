# Backend

These commands are written for PowerShell on Windows. Copy and paste them one line at a time.

## 1. Go to the backend folder

```powershell
cd Backend
```

## 2. Create a virtual environment

```powershell
python -m venv .venv
```

## 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Install backend dependencies

```powershell
pip install -r requirements.txt
```

## 5. Start the backend server

```powershell
uvicorn app.main:app --reload
```

The triage endpoint expects the hackathon CSVs to exist at:

```text
..\Data Sources for Hackathon\hackathon-data\track-1-clinical-ai\synthea-patients
```

## 6. Open the backend in your browser

Health check:

```text
http://127.0.0.1:8000/health
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

## 7. Test the generate-data endpoint in Swagger

Open this page:

```text
http://127.0.0.1:8000/docs
```

Then:

1. Find `POST /api/generate_data`
2. Click `Try it out`
3. Use this sample request body:

```json
{
  "n_rows": 5,
  "seed": 42
}
```

4. Click `Execute`

## 8. Test the triage prediction endpoint

Open this page:

```text
http://127.0.0.1:8000/docs
```

Then call `POST /api/triage/predict` with a body like:

```json
{
  "query": "52 year old with chest pain and shortness of breath, troponin 0.42, sodium 133, taking metoprolol",
  "labs": {
    "Troponin I": 0.42
  },
  "medications": ["metoprolol"]
}
```

## 9. Stop the backend

In the same PowerShell window:

```powershell
Ctrl+C
```
