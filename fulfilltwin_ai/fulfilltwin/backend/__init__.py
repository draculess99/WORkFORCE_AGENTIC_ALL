"""FulfillTwin backend package.

Service modules are intentionally importable without Flask so the merged
Workforce AI Suite can run FulfillTwin in-process. Standalone callers may still
import ``create_app`` lazily from this package.
"""

from __future__ import annotations

from typing import Any


def create_app(*args: Any, **kwargs: Any):
    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)


__all__ = ["create_app"]
