# Workforce AI Suite — Merge Notes

This is a consolidated prototype made from four workforce apps plus the embedded GridGuard AI app.

## Included pages

- `pages/01_Basic_Warehouse_Forecast.py` — original/basic Streamlit app.
- `pages/02_CrewAI_Multi_Agent_Planner.py` — CrewAI multi-agent version.
- `pages/03_LangGraph_Labor_Optimizer.py` — LangGraph/RAG/labor optimization version.
- `pages/04_Autonomous_VET_VTO_Supervisor.py` — autonomous supervisor version.
- `pages/05_GridGuard_AI.py` — energy-demand forecasting, grid-risk simulation, RAG, persistence, and decision intelligence.

## Key consolidation change

The original apps called external Flask URLs such as:

```python
requests.post("https://.../forecast", json=payload)
```

Those calls are now intercepted by `local_requests_patch.py` and routed to:

```python
backend.forecast_engine.run_forecast(payload)
```

So Railway only needs one public service running Streamlit.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy to Railway

Deploy this folder as one Railway service. The included `railway.toml` uses:

```bash
streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

## Notes

- `flask_api.py` is kept for reference/compatibility, but it is not needed for the one-service version.
- The trained model is expected at `models/warehouse_system.pkl`.
- If the model cannot load, the backend uses a deterministic fallback forecast so the demo page still works.

## GridGuard directory isolation

GridGuard remains available as its own directory at `gridguard_ai/`. Its original `backend/` package was renamed to `gridguard_ai/gridguard_backend/` and imports were namespaced to prevent collision with the workforce suite's `backend/` package. GridGuard data, RAG documents, and JSON runtime files remain under `gridguard_ai/`.

The original GridGuard `.env` and nested `.git` directory were intentionally not copied. Put shared API keys in the suite root `.env` using `.env.example` as guidance.
