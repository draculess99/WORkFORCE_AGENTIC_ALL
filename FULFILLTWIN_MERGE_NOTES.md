# FulfillTwin AI Merge Notes

FulfillTwin AI is integrated as page 6 of the Workforce AI Suite.

## Entry point

- Suite page: `pages/06_FulfillTwin_AI.py`
- Isolated source directory: `fulfilltwin_ai/`
- Core package: `fulfilltwin_ai/fulfilltwin/`
- Internal UI sections: `fulfilltwin_ai/ui_pages/`

## Internal sections

1. Control Tower
2. Scenario Lab
3. Agent Council
4. Knowledge Center
5. Model Ops

## Single-service design

The original FulfillTwin project used a Streamlit frontend that called a separate Flask API. The merged suite defaults to `LocalFulfillTwinClient`, which invokes the same ML, RAG, expert-system, optimizer, memory, and agent-council classes directly inside the Streamlit process.

This keeps Railway deployment to one command and one public port:

```bash
streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

The optional standalone HTTP mode remains available by setting:

```env
FULFILLTWIN_USE_HTTP_API=true
FULFILLTWIN_API_URL=http://127.0.0.1:5000
```

Do not enable HTTP mode on the one-process Railway deployment unless a separate API process is also configured.

## Models preserved

- XGBoost regressor for backlog forecasting
- XGBoost classifier for SLA-breach risk
- Isolation Forest for anomaly detection
- K-means for operating-regime clustering
- TF-IDF local RAG
- Deterministic expert-system guardrails
- Optional Groq and Gemini executive narrative
- JSON decision memory and approval audit trail
