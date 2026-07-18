from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from fulfilltwin.config import ARTIFACT_DIR, KNOWLEDGE_DIR, settings
from fulfilltwin.backend.services.council import AgentCouncil
from fulfilltwin.backend.services.expert_system import ExpertSystem
from fulfilltwin.backend.services.llm import LLMProvider
from fulfilltwin.backend.services.memory import JsonMemoryStore
from fulfilltwin.backend.services.ml_engine import OperationalMLEngine
from fulfilltwin.backend.services.optimizer import RecoveryOptimizer
from fulfilltwin.backend.services.rag import LocalRagEngine

REQUIRED_FIELDS: dict[str, tuple[float, float]] = {
    "order_volume_pct": (-30, 100),
    "absenteeism_pct": (0, 45),
    "conveyor_capacity_pct": (20, 110),
    "dock_congestion_pct": (0, 100),
    "energy_price_pct": (-30, 160),
    "inventory_availability_pct": (40, 100),
    "current_backlog": (0, 15000),
    "workers": (20, 500),
    "base_throughput": (200, 5000),
    "horizon_hours": (1, 24),
}


def _validate_scenario(payload: dict[str, Any]) -> dict[str, float]:
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Missing scenario fields: {', '.join(missing)}")

    result: dict[str, float] = {}
    for field, (low, high) in REQUIRED_FIELDS.items():
        value = float(payload[field])
        if not low <= value <= high:
            raise ValueError(f"{field} must be between {low:g} and {high:g}")
        result[field] = value
    return result


class LocalFulfillTwinClient:
    """In-process FulfillTwin service used by the merged Streamlit suite.

    The standalone FulfillTwin project used HTTP between Streamlit and Flask.
    Inside Workforce AI Suite, this adapter invokes the same service classes
    directly, so Railway only needs one Streamlit process and one public port.
    """

    def __init__(self) -> None:
        self.memory_store = JsonMemoryStore(settings.memory_file, settings.max_memory_records)
        self.rag_engine = LocalRagEngine(KNOWLEDGE_DIR)
        self.ml_engine = OperationalMLEngine(ARTIFACT_DIR, settings.model_seed, settings.training_rows)
        self.llm_provider = LLMProvider(settings)
        self.council = AgentCouncil(
            self.ml_engine,
            ExpertSystem(),
            self.rag_engine,
            RecoveryOptimizer(),
            self.llm_provider,
            self.memory_store,
        )

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "FulfillTwin AI embedded service",
            "transport": "in-process",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "models_ready": bool(self.ml_engine.metrics),
            "knowledge_chunks": len(self.rag_engine.chunks),
        }

    def models(self) -> dict[str, Any]:
        return self.llm_provider.available_models()

    def run_scenario(self, scenario: dict[str, Any], provider: str, model: str) -> dict[str, Any]:
        validated = _validate_scenario(scenario)
        return self.council.run(validated, provider=provider, model=model)

    def approve_scenario(self, run_id: str) -> dict[str, Any]:
        updated = self.memory_store.approve_run(run_id)
        if not updated:
            raise RuntimeError("Run not found")
        return {"status": "approved", "run": updated}

    def search_rag(self, query: str, top_k: int = 5) -> dict[str, Any]:
        count = max(1, min(int(top_k), 10))
        return {"query": query, "results": self.rag_engine.search(str(query), count)}

    def refresh_rag(self) -> dict[str, Any]:
        self.rag_engine.refresh()
        return {"status": "refreshed", "knowledge_chunks": len(self.rag_engine.chunks)}

    def memory(self, limit: int = 25) -> dict[str, Any]:
        return {"runs": self.memory_store.list(max(1, min(int(limit), 100)))}

    def clear_memory(self) -> dict[str, Any]:
        self.memory_store.clear()
        return {"status": "cleared"}

    def model_card(self) -> dict[str, Any]:
        return self.ml_engine.model_card()

    def retrain(self) -> dict[str, Any]:
        return {"status": "retrained", "metrics": self.ml_engine.train()}

    def events(self, count: int = 12) -> dict[str, Any]:
        count = max(5, min(int(count), 50))
        rng = random.Random(int(datetime.now(timezone.utc).timestamp() // 60))
        event_types = [
            "ORDER_SURGE",
            "CONVEYOR_ALERT",
            "LABOR_UPDATE",
            "TRAILER_ARRIVAL",
            "REPLENISHMENT_DELAY",
            "ENERGY_SIGNAL",
        ]
        rows = []
        for idx in range(count):
            event = rng.choice(event_types)
            severity = rng.choices(
                ["INFO", "WATCH", "HIGH", "CRITICAL"],
                weights=[45, 30, 20, 5],
            )[0]
            rows.append(
                {
                    "event_id": f"EVT-{rng.randint(10000, 99999)}-{idx}",
                    "type": event,
                    "severity": severity,
                    "zone": rng.choice(["Inbound", "Receive", "Pick", "Pack", "Sort", "Outbound", "Yard"]),
                    "value": round(rng.uniform(0.2, 1.0), 2),
                    "minutes_ago": idx * rng.randint(1, 4),
                }
            )
        return {"events": rows}
