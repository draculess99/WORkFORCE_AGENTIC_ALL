from backend.forecast_engine import run_forecast

payload = {
    "request_id": "smoke_test",
    "scenario_name": "Local Smoke Test",
    "weeks": 4,
    "inputs": {
        "temperature": [42, 44, 46, 48],
        "fuel_price": [3.2, 3.2, 3.3, 3.4],
        "cpi": [225, 225, 226, 226],
        "unemployment": [6.5, 6.4, 6.4, 6.3],
        "isholiday": [0, 0, 1, 0],
    },
    "settings": {"workers_per_unit": 5000},
}

result = run_forecast(payload)
print(result["status"])
print(result["summary"])
print(result["forecast"][0])
