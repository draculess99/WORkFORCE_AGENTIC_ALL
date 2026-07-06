"""
Shared local forecast engine for Workforce AI Suite.

This replaces the old Flask /forecast network call so all Streamlit pages can run
inside one Railway service. If the saved XGBoost/skforecast model is available,
it is used. If the model cannot load, a deterministic fallback forecast keeps the
app usable for local testing and demos.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List
import math

import numpy as np
import pandas as pd

try:
    import joblib
except Exception:  # pragma: no cover
    joblib = None

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATHS = [
    ROOT / "models" / "warehouse_system.pkl",
    ROOT / "warehouse_system.pkl",
]

DEFAULT_WORKERS_PER_UNIT = 5000
DEFAULT_OVERTIME_LABOR_COST_PER_WORKER = 30
DEFAULT_HOURLY_LABOR_COST_PER_WORKER = 20

_MODEL_BUNDLE = None
_MODEL_ERROR = None


def _load_model_bundle():
    global _MODEL_BUNDLE, _MODEL_ERROR
    if _MODEL_BUNDLE is not None or _MODEL_ERROR is not None:
        return _MODEL_BUNDLE
    if joblib is None:
        _MODEL_ERROR = "joblib is not installed"
        return None
    for path in MODEL_PATHS:
        if path.exists():
            try:
                _MODEL_BUNDLE = joblib.load(path)
                return _MODEL_BUNDLE
            except Exception as exc:
                _MODEL_ERROR = f"Could not load model from {path.name}: {exc}"
                return None
    _MODEL_ERROR = "warehouse_system.pkl was not found"
    return None


def _as_list(value: Any, weeks: int, default: float) -> List[float]:
    if isinstance(value, (list, tuple, np.ndarray, pd.Series)):
        arr = list(value)
    else:
        arr = [value] * weeks
    if len(arr) < weeks:
        arr += [default] * (weeks - len(arr))
    arr = arr[:weeks]
    cleaned = []
    for item in arr:
        try:
            cleaned.append(float(item))
        except Exception:
            cleaned.append(float(default))
    return cleaned


def _input_summary(values: Iterable[float], field_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    vals = list(values)
    return {
        "default_used": field_name not in inputs,
        "length": len(vals),
        "min": min(vals) if vals else None,
        "max": max(vals) if vals else None,
        "avg": round(sum(vals) / len(vals), 2) if vals else None,
        "values": ", ".join(str(int(v)) if float(v).is_integer() else str(round(v, 2)) for v in vals),
    }


def _fallback_prediction(weeks: int, temperature, fuel_price, cpi, unemployment, isholiday,
                         velocity_pct, shipping_delay_pct, congestion_pct, logistics_stress_pct):
    """Deterministic backup if the trained model cannot load."""
    base = 46_500_000.0
    preds = []
    for i in range(weeks):
        seasonal = 1 + 0.035 * math.sin((i / max(weeks, 1)) * math.pi * 2)
        holiday = 1.08 if int(isholiday[i]) else 1.0
        temp_effect = 1 + (temperature[i] - 45) * 0.0015
        fuel_effect = 1 - (fuel_price[i] - 3.2) * 0.015
        unemployment_effect = 1 - (unemployment[i] - 6.5) * 0.008
        macro = 1 + (cpi[i] - 225) * 0.0005
        ops = (1 + velocity_pct[i] / 100) * (1 - shipping_delay_pct[i] / 100) * (1 - congestion_pct[i] / 100) * (1 - logistics_stress_pct[i] / 100)
        preds.append(base * seasonal * holiday * temp_effect * fuel_effect * unemployment_effect * macro * ops)
    return np.array(preds, dtype=float), 47_500_000.0, 45_500_000.0, "fallback"


def run_forecast(data: Dict[str, Any] | None) -> Dict[str, Any]:
    data = data or {}
    request_id = data.get("request_id", "forecast_default")
    scenario_name = data.get("scenario_name", "Standard Forecast")
    weeks = int(data.get("weeks", 43) or 43)
    weeks = max(1, min(104, weeks))
    mode = data.get("mode", "simple")

    inputs = data.get("inputs", {}) or {}
    settings = data.get("settings", {}) or {}

    temperature = _as_list(inputs.get("temperature", 45), weeks, 45)
    fuel_price = _as_list(inputs.get("fuel_price", 3.2), weeks, 3.2)
    cpi = _as_list(inputs.get("cpi", 225), weeks, 225)
    unemployment = _as_list(inputs.get("unemployment", 6.5), weeks, 6.5)
    isholiday = _as_list(inputs.get("isholiday", 0), weeks, 0)

    workers_per_unit = float(settings.get("workers_per_unit", DEFAULT_WORKERS_PER_UNIT) or DEFAULT_WORKERS_PER_UNIT)
    overtime_cost = float(settings.get("overtime_labor_cost_per_worker", DEFAULT_OVERTIME_LABOR_COST_PER_WORKER) or DEFAULT_OVERTIME_LABOR_COST_PER_WORKER)
    hourly_cost = float(settings.get("hourly_labor_cost_per_worker", DEFAULT_HOURLY_LABOR_COST_PER_WORKER) or DEFAULT_HOURLY_LABOR_COST_PER_WORKER)

    velocity_pct = _as_list(settings.get("velocity_pct", 0), weeks, 0)
    shipping_delay_pct = _as_list(settings.get("shipping_delay_pct", 0), weeks, 0)
    congestion_pct = _as_list(settings.get("congestion_pct", 0), weeks, 0)
    logistics_stress_pct = _as_list(settings.get("logistics_stress_pct", 0), weeks, 0)

    model_mode = "model"
    bundle = _load_model_bundle()
    if bundle is not None:
        try:
            forecaster = bundle["forecaster"]
            vet_threshold = float(bundle["vet_threshold"])
            vto_threshold = float(bundle["vto_threshold"])
            temp_series = pd.Series(temperature)
            high_temp = temp_series.quantile(0.90)
            low_temp = temp_series.quantile(0.10)
            future_exog = pd.DataFrame({
                "IsHoliday": isholiday,
                "Temperature": temperature,
                "Fuel_Price": fuel_price,
                "CPI": cpi,
                "Unemployment": unemployment,
            })
            future_exog["sales_velocity"] = np.array(velocity_pct) / 100
            future_exog["backlog_proxy"] = np.array(shipping_delay_pct) / 100
            future_exog["warehouse_congestion"] = np.array(congestion_pct) / 100
            future_exog["logistics_stress"] = np.array(logistics_stress_pct) / 100
            future_exog["extreme_temp"] = ((future_exog["Temperature"] > high_temp) | (future_exog["Temperature"] < low_temp)).astype(int)
            try:
                last_idx = forecaster.last_window_.index[-1]
                start = last_idx + pd.Timedelta(weeks=1)
            except Exception:
                start = pd.Timestamp("2012-11-02")
            future_exog.index = pd.date_range(start=start, periods=weeks, freq="W-FRI")
            pred = forecaster.predict(steps=weeks, exog=future_exog)
            pred = np.asarray(pred, dtype=float)
            pred = pred * (1 + np.array(velocity_pct) / 100)
            pred = pred * (1 - np.array(shipping_delay_pct) / 100)
            pred = pred * (1 - np.array(congestion_pct) / 100)
            pred = pred * (1 - np.array(logistics_stress_pct) / 100)
        except Exception as exc:
            pred, vet_threshold, vto_threshold, model_mode = _fallback_prediction(
                weeks, temperature, fuel_price, cpi, unemployment, isholiday,
                velocity_pct, shipping_delay_pct, congestion_pct, logistics_stress_pct
            )
            globals()["_MODEL_ERROR"] = f"Model execution failed, using fallback: {exc}"
    else:
        pred, vet_threshold, vto_threshold, model_mode = _fallback_prediction(
            weeks, temperature, fuel_price, cpi, unemployment, isholiday,
            velocity_pct, shipping_delay_pct, congestion_pct, logistics_stress_pct
        )

    output = []
    cumulative_cost = 0.0
    vet_weeks = vto_weeks = normal_weeks = 0
    total_extra_workers = total_workers_reduced = 0
    peak_demand = float("-inf")
    peak_week = 0

    workers_per_unit = max(workers_per_unit, 1.0)
    for i, value in enumerate(pred):
        value = float(value)
        if value >= vet_threshold:
            decision = "VET"
            extra_workers = int(max(0, (value - vet_threshold) / workers_per_unit))
            reduce_workers = 0
            est_cost = extra_workers * overtime_cost
            vet_weeks += 1
        elif value <= vto_threshold:
            decision = "VTO"
            extra_workers = 0
            reduce_workers = int(max(0, (vto_threshold - value) / workers_per_unit))
            est_cost = reduce_workers * hourly_cost
            vto_weeks += 1
        else:
            decision = "NORMAL"
            extra_workers = 0
            reduce_workers = 0
            est_cost = 0.0
            normal_weeks += 1
        cumulative_cost += est_cost
        total_extra_workers += extra_workers
        total_workers_reduced += reduce_workers
        if value > peak_demand:
            peak_demand = value
            peak_week = i + 1
        output.append({
            "week": i + 1,
            "predicted_demand": round(value, 2),
            "decision": decision,
            "extra_workers_needed": int(extra_workers),
            "workers_to_reduce": int(reduce_workers),
            "estimated_cost": round(float(est_cost), 2),
            "cumulative_future_cost": round(float(cumulative_cost), 2),
        })

    summary = {
        "weeks_forecasted": weeks,
        "vet_weeks": vet_weeks,
        "vto_weeks": vto_weeks,
        "normal_weeks": normal_weeks,
        "total_extra_workers": int(total_extra_workers),
        "total_workers_reduced": int(total_workers_reduced),
        "total_cost": round(float(cumulative_cost), 2),
        "peak_demand_week": peak_week,
        "peak_demand_value": round(float(peak_demand), 2),
    }

    inputs_used = {
        "weeks": weeks,
        "temperature": _input_summary(temperature, "temperature", inputs),
        "fuel_price": _input_summary(fuel_price, "fuel_price", inputs),
        "cpi": _input_summary(cpi, "cpi", inputs),
        "unemployment": _input_summary(unemployment, "unemployment", inputs),
        "isholiday": _input_summary(isholiday, "isholiday", inputs),
    }

    simulation_controls = {
        "mode": mode,
        "workers_per_unit": workers_per_unit,
        "overtime_labor_cost_per_worker": overtime_cost,
        "hourly_labor_cost_per_worker": hourly_cost,
        "demand_velocity_pct": ", ".join(map(str, velocity_pct)),
        "shipping_delay_pct": ", ".join(map(str, shipping_delay_pct)),
        "warehouse_congestion_pct": ", ".join(map(str, congestion_pct)),
        "logistics_stress_pct": ", ".join(map(str, logistics_stress_pct)),
        "forecast_engine": model_mode,
    }

    recommendations = []
    if vet_weeks > 0:
        recommendations.append(f"Increase staffing during {vet_weeks} week(s) of forecasted high demand.")
    if vto_weeks > 0:
        recommendations.append(f"Offer VTO during {vto_weeks} low-demand week(s) to reduce labor cost.")
    if peak_week > 0:
        recommendations.append(f"Highest demand expected in Week {peak_week}. Prepare staffing early.")
    if total_extra_workers > 50:
        recommendations.append("Large labor requirement detected. Consider temporary staffing support.")
    if cumulative_cost > 0:
        recommendations.append(f"Projected added labor cost is ${round(cumulative_cost, 2)}.")
    if not recommendations:
        recommendations.append("Demand stable. Maintain standard staffing plan.")
    if model_mode == "fallback":
        recommendations.append("Prototype note: the saved model could not be loaded, so a deterministic fallback forecast was used. Install requirements.txt to use the trained model.")

    return {
        "status": "success",
        "inputs_used": inputs_used,
        "simulation_controls": simulation_controls,
        "request_id": request_id,
        "scenario_name": scenario_name,
        "summary": summary,
        "forecast": output,
        "recommendations": recommendations,
    }
