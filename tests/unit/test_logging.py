"""Tests for structlog logging configuration."""

from __future__ import annotations

import logging

import pytest
import structlog
import structlog.dev
import structlog.processors

from fittrack.utils.logging import configure_logging


@pytest.fixture(autouse=True)
def reset_logging_config() -> object:
    yield
    structlog.reset_defaults()
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    for h in root.handlers[:]:
        root.removeHandler(h)


@pytest.mark.unit
def test_dev_mode_uses_console_renderer() -> None:
    configure_logging("INFO", dev=True)
    processors = structlog.get_config()["processors"]
    assert any(isinstance(p, structlog.dev.ConsoleRenderer) for p in processors)


@pytest.mark.unit
def test_prod_mode_uses_json_renderer() -> None:
    configure_logging("INFO", dev=False)
    processors = structlog.get_config()["processors"]
    assert any(isinstance(p, structlog.processors.JSONRenderer) for p in processors)


@pytest.mark.unit
def test_prod_mode_no_console_renderer() -> None:
    configure_logging("INFO", dev=False)
    processors = structlog.get_config()["processors"]
    assert not any(isinstance(p, structlog.dev.ConsoleRenderer) for p in processors)


@pytest.mark.unit
def test_dev_mode_no_json_renderer() -> None:
    configure_logging("INFO", dev=True)
    processors = structlog.get_config()["processors"]
    assert not any(isinstance(p, structlog.processors.JSONRenderer) for p in processors)


@pytest.mark.unit
def test_stdlib_level_info() -> None:
    configure_logging("INFO", dev=True)
    assert logging.root.level == logging.INFO


@pytest.mark.unit
def test_stdlib_level_debug() -> None:
    configure_logging("DEBUG", dev=True)
    assert logging.root.level == logging.DEBUG


@pytest.mark.unit
def test_stdlib_level_warning() -> None:
    configure_logging("WARNING", dev=False)
    assert logging.root.level == logging.WARNING


@pytest.mark.unit
def test_stdlib_level_error() -> None:
    configure_logging("ERROR", dev=False)
    assert logging.root.level == logging.ERROR


@pytest.mark.unit
def test_calling_twice_does_not_raise() -> None:
    configure_logging("INFO", dev=True)
    configure_logging("DEBUG", dev=False)


@pytest.mark.unit
def test_shared_processors_always_present() -> None:
    configure_logging("INFO", dev=True)
    processors = structlog.get_config()["processors"]
    assert structlog.contextvars.merge_contextvars in processors
    assert structlog.stdlib.add_log_level in processors
    assert any(isinstance(p, structlog.processors.TimeStamper) for p in processors)
    assert any(isinstance(p, structlog.processors.StackInfoRenderer) for p in processors)


@pytest.mark.unit
def test_shared_processors_present_in_prod_mode() -> None:
    configure_logging("INFO", dev=False)
    processors = structlog.get_config()["processors"]
    assert structlog.contextvars.merge_contextvars in processors
    assert structlog.stdlib.add_log_level in processors
    assert any(isinstance(p, structlog.processors.TimeStamper) for p in processors)


@pytest.mark.unit
def test_dev_mode_disables_logger_caching() -> None:
    configure_logging("INFO", dev=True)
    assert structlog.get_config()["cache_logger_on_first_use"] is False


@pytest.mark.unit
def test_prod_mode_enables_logger_caching() -> None:
    configure_logging("INFO", dev=False)
    assert structlog.get_config()["cache_logger_on_first_use"] is True


@pytest.mark.unit
def test_unknown_log_level_falls_back_to_info() -> None:
    configure_logging("NOTAREAL", dev=True)
    assert logging.root.level == logging.INFO


@pytest.mark.unit
def test_prod_mode_includes_exception_renderer() -> None:
    configure_logging("INFO", dev=False)
    processors = structlog.get_config()["processors"]
    assert any(isinstance(p, structlog.processors.ExceptionRenderer) for p in processors)
