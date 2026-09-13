# KisanSetu operator dashboard

This is a **development-only** Streamlit dashboard for mandi operators. It
does not provide production authentication and must not be deployed publicly.
The FastAPI backend rejects operator requests outside `ENVIRONMENT=development`
and requires the local access value (default `local-operator`).

## Run locally

In one terminal, start the backend from the repository root:

```bash
source backend/.venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

In another terminal:

```bash
pip install -r apps/operator/requirements.txt
streamlit run apps/operator/app.py
```

The sidebar can point at another local API with `API URL`; it defaults to
`http://localhost:8000`. Set `OPERATOR_ACCESS_TOKEN` in the backend `.env` if
you change the local access value. No credentials are stored by the dashboard.
