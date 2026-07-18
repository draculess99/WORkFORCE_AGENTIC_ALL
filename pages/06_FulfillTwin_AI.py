# FulfillTwin AI embedded multipage entry.
# The original project remains isolated under fulfilltwin_ai/ while this page
# runs its service layer in-process so the suite needs only one Railway service.

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import streamlit as st

SUITE_ROOT = Path(__file__).resolve().parents[1]
FULFILL_ROOT = SUITE_ROOT / "fulfilltwin_ai"
if str(FULFILL_ROOT) not in sys.path:
    sys.path.insert(0, str(FULFILL_ROOT))

from fulfilltwin.ui_helpers import get_client  # noqa: E402

st.set_page_config(
    page_title="FulfillTwin AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .ft-header {
        border: 1px solid rgba(128,128,128,.24);
        border-radius: 16px;
        padding: 1rem 1.15rem;
        margin-bottom: 1rem;
        background: rgba(128,128,128,.04);
    }
    .ft-title {font-size: 2rem; font-weight: 760; letter-spacing: -.03em;}
    .ft-subtitle {opacity: .78; margin-top: .15rem;}
    </style>
    <div class="ft-header">
      <div class="ft-title">🏭 FulfillTwin AI</div>
      <div class="ft-subtitle">Human–robot workforce digital twin, incident command, traditional ML, RAG, and multi-agent recovery planning.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

client = get_client()

st.sidebar.markdown("### FulfillTwin Controls")
try:
    health = client.health()
    st.sidebar.success(
        f"Embedded engine online · {health['knowledge_chunks']} RAG chunks"
    )
except Exception as exc:
    st.sidebar.error(f"FulfillTwin initialization failed: {exc}")
    st.error(f"FulfillTwin could not initialize: {exc}")
    st.stop()

try:
    model_config = client.models()
except Exception:
    model_config = {
        "LOCAL": ["expert-system-v1"],
        "GROQ": [],
        "GEMINI": [],
        "keys_configured": {},
    }

provider_options = ["LOCAL", "GROQ", "GEMINI"]
if st.session_state.get("fulfilltwin_provider") not in provider_options:
    st.session_state["fulfilltwin_provider"] = "LOCAL"
provider = st.sidebar.selectbox(
    "Decision narrative",
    provider_options,
    key="fulfilltwin_provider",
)
models = model_config.get(provider, ["expert-system-v1"]) or ["expert-system-v1"]
if st.session_state.get("fulfilltwin_model") not in models:
    st.session_state["fulfilltwin_model"] = models[0]
model = st.sidebar.selectbox(
    "Model",
    models,
    key="fulfilltwin_model",
)
if provider != "LOCAL" and not model_config.get("keys_configured", {}).get(provider, False):
    st.sidebar.warning(
        f"{provider} API key is not configured. FulfillTwin will use its deterministic local expert-system brief."
    )

if "fulfilltwin_total_tokens" not in st.session_state:
    st.session_state["fulfilltwin_total_tokens"] = 0

token_col, reset_col = st.sidebar.columns([2, 1])
token_placeholder = token_col.empty()
token_placeholder.metric("Tokens", f"{st.session_state['fulfilltwin_total_tokens']:,}")
if reset_col.button("Reset", key="fulfilltwin_reset_tokens"):
    st.session_state["fulfilltwin_total_tokens"] = 0
    st.rerun()

sections = [
    "Control Tower",
    "Scenario Lab",
    "Agent Council",
    "Knowledge Center",
    "Model Ops",
]

# A Control Tower incident can request the Scenario Lab on the next clean rerun.
next_section = st.session_state.pop("fulfilltwin_next_section", None)
if next_section in sections:
    st.session_state["fulfilltwin_section"] = next_section

section = st.sidebar.radio(
    "FulfillTwin section",
    sections,
    key="fulfilltwin_section",
)

page_map = {
    "Control Tower": FULFILL_ROOT / "ui_pages" / "control_tower.py",
    "Scenario Lab": FULFILL_ROOT / "ui_pages" / "scenario_lab.py",
    "Agent Council": FULFILL_ROOT / "ui_pages" / "agent_council.py",
    "Knowledge Center": FULFILL_ROOT / "ui_pages" / "knowledge_center.py",
    "Model Ops": FULFILL_ROOT / "ui_pages" / "model_ops.py",
}

page_path = page_map[section]
if not page_path.exists():
    st.error(f"Missing FulfillTwin section: {page_path.name}")
    st.stop()

# Execute the selected original UI module inside this one suite page.
runpy.run_path(str(page_path), run_name=f"__fulfilltwin_{section.lower().replace(' ', '_')}__")
# Refresh the sidebar metric after the selected section may have added LLM tokens.
token_placeholder.metric("Tokens", f"{st.session_state['fulfilltwin_total_tokens']:,}")
