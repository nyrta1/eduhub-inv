from __future__ import annotations

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator


def configure_metrics(app: FastAPI, *, metrics_path: str, enabled: bool) -> None:
    if not enabled:
        return

    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
    ).instrument(app).expose(
        app,
        endpoint=metrics_path,
        include_in_schema=False,
    )
