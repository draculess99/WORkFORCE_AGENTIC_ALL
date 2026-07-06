# Antigravity / AI Coding Agent Instructions

This project is a merged one-service Streamlit app called **Workforce AI Suite**.

## Goal
Keep this project deployable as **one Railway service**, not four separate services.

The intended architecture is:

```text
Railway Service
└── Streamlit multipage app
    ├── pages/01_Basic_Warehouse_Forecast.py
    ├── pages/02_CrewAI_Multi_Agent_Planner.py
    ├── pages/03_LangGraph_Labor_Optimizer.py
    ├── pages/04_Autonomous_VET_VTO_Supervisor.py
    └── backend/forecast_engine.py
```

## Run locally
Prefer this command:

```bash
python app.py
```

The launcher creates `.venv`, installs `requirements.txt`, starts Streamlit, and opens the browser.

Manual fallback:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Railway deployment
Use `railway.toml` as-is unless there is a strong reason to change it.

Do not restore Docker Compose as the main deployment path. Docker Compose can create multiple Railway services, which defeats the cost-saving purpose of this merge.

## Backend rule
Do **not** reintroduce a separate public Flask backend unless explicitly requested.

The old `/forecast` HTTP calls are redirected locally through:

```python
backend/forecast_engine.py
local_requests_patch.py
```

If a page needs forecast results, prefer importing the shared Python backend directly or keep using the existing local request patch.

## Environment variables
Optional LLM keys may be placed in `.env`, copied from `.env.example`.
Do not commit `.env`.

## Safe refactor guidance
- Preserve the four existing Streamlit pages unless replacing them with a cleaner multipage implementation.
- Keep model/data paths relative to the project root.
- Keep generated files, `.venv`, caches, and secrets out of git.
- When changing dependencies, update `requirements.txt` and test with `python app.py --reinstall`.
- Keep the app runnable without paid API keys where possible; agent/LLM features should fail gracefully or use local/demo mode.
