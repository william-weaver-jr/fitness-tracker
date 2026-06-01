"""Structlog configuration for FitTrack."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
import structlog.dev
import structlog.processors
import structlog.stdlib


def configure_logging(log_level: str = "INFO", *, dev: bool = True) -> None:
    """Configure structlog and stdlib logging.

    Call once at startup. Dev mode uses ConsoleRenderer; production uses JSONRenderer.
    """
    numeric_level: int = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if dev:
        processors: list[Any] = [*shared_processors, structlog.dev.ConsoleRenderer()]
    else:
        processors = [
            *shared_processors,
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=not dev,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
        force=True,
    )
