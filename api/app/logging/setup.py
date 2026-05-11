from __future__ import annotations

import logging
import queue
import sys
import threading
import urllib.error
import urllib.request
from typing import Any

import structlog
from structlog.stdlib import ProcessorFormatter

from app.core.config import Settings


class LogstashHttpHandler(logging.Handler):
    """Ship JSON log lines to Logstash HTTP input without blocking the logging thread."""

    def __init__(self, endpoint: str) -> None:
        super().__init__()
        self._endpoint = endpoint.rstrip("/") + "/"
        self._queue: queue.Queue[str | None] = queue.Queue(maxsize=8192)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._consume, name="logstash-shipper", daemon=True)
        self._thread.start()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._queue.put_nowait(record.getMessage())
        except queue.Full:
            return

    def _consume(self) -> None:
        while not self._stop.is_set():
            try:
                message = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if message is None:
                break
            request = urllib.request.Request(
                self._endpoint,
                data=message.encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=2.0) as response:  # nosec B310
                    if response.status >= 400:
                        continue
            except (urllib.error.URLError, TimeoutError, OSError):
                continue

    def close(self) -> None:
        self._stop.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)
        super().close()


def configure_logging(settings: Settings) -> None:
    logging.captureWarnings(True)

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.structlog_caller_info:
        shared_processors.insert(4, structlog.processors.CallsiteParameterAdder())

    renderer: structlog.types.Processor
    if settings.log_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [stream_handler]
    if settings.log_ship_logstash:
        handlers.append(LogstashHttpHandler(settings.logstash_http_endpoint))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, settings.log_level))
    for handler in handlers:
        root_logger.addHandler(handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
