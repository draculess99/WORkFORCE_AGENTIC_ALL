import streamlit as st

st.set_page_config(
    page_title="Workforce AI Suite",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Workforce AI Suite")
st.caption("One Railway service • one Streamlit multipage app • shared local forecast engine")

st.markdown("""
This merged prototype combines your four workforce apps into a single Streamlit project.

### What changed
- Each former app is now a separate page in the sidebar.
- The old external Flask `/forecast` network calls are intercepted locally.
- The shared forecast logic lives in `backend/forecast_engine.py`.
- Railway only needs to run one command: `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`.

### Pages included
1. Basic Warehouse Forecast Dashboard
2. CrewAI Multi-Agent Workforce Planner
3. LangGraph Labor Optimization
4. Autonomous VET/VTO Supervisor

### Local run
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Railway run
Use the included `railway.toml`. Deploy this whole folder as one service.
""")

st.info("Open the sidebar and choose one of the app pages to test the merged version.")

st.subheader("Single-service architecture")
st.code("""
Railway Service
└── Streamlit multipage app
    ├── Page 1: Basic forecast dashboard
    ├── Page 2: CrewAI planner
    ├── Page 3: LangGraph optimizer
    ├── Page 4: Autonomous supervisor
    └── Shared backend/forecast_engine.py
""", language="text")
