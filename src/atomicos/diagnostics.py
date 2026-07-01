"""Safe technical diagnostics for atomicOS."""

from __future__ import annotations

import logging
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4


LOGGER_NAME = "atomicos"
DEFAULT_TRUNCATE_LIMIT = 500
CONTENT_PLACEHOLDER = "<omitted>"


@dataclass(frozen=True)
class Timer:
    """Small elapsed-time helper for diagnostic logs."""

    started_at: float

    @classmethod
    def start(cls) -> "Timer":
        return cls(perf_counter())

    def elapsed_ms(self) -> int:
        return round((perf_counter() - self.started_at) * 1000)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure the application logger namespace once and return it."""

    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def new_run_id() -> str:
    return uuid4().hex[:12]


def truncate_value(value: str | None, limit: int = DEFAULT_TRUNCATE_LIMIT) -> str:
    """Return a bounded representation of uncontrolled external output."""

    if value is None:
        return ""
    if len(value) <= limit:
        return value
    omitted = len(value) - limit
    return f"{value[:limit]}... <truncated {omitted} chars>"


def sanitize_command(command: Sequence[str]) -> list[str]:
    """Return a CLI command shape without logging sensitive content values."""

    sanitized: list[str] = []
    skip_next = False
    for part in command:
        if skip_next:
            sanitized.append(CONTENT_PLACEHOLDER)
            skip_next = False
            continue
        sanitized.append(part)
        if part == "--content":
            skip_next = True
    return sanitized
