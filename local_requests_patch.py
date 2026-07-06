"""Patch requests.post('/forecast') to use the local shared backend engine."""
from __future__ import annotations

import json as _json
import traceback
import requests as _requests
from backend.forecast_engine import run_forecast

_ORIGINAL_POST = _requests.post

class LocalForecastResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = _json.dumps(payload, indent=2, default=str)
        self.content = self.text.encode("utf-8")

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.text)


def _patched_post(url, *args, **kwargs):
    if isinstance(url, str) and url.rstrip("/").endswith("/forecast"):
        try:
            payload = kwargs.get("json") or {}
            return LocalForecastResponse(run_forecast(payload), 200)
        except Exception as exc:
            return LocalForecastResponse({
                "status": "error",
                "error": str(exc),
                "traceback": traceback.format_exc(limit=5),
            }, 500)
    return _ORIGINAL_POST(url, *args, **kwargs)


def patch_requests():
    if getattr(_requests.post, "_workforce_suite_patch", False):
        return
    _patched_post._workforce_suite_patch = True
    _requests.post = _patched_post
