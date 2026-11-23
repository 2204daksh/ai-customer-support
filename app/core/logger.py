"""Centralized colored logger for the AI customer support agent.

Structure mirrors the reference layout:
- ``app/logger.py``  (this file)

Provides:
- ``LoggerManager``: builds a logger with a colored console handler.
- ``ColoredFormatter``: ANSI-colored log output by level.
- ``logging_llm_call``: decorator that logs LLM inputs/outputs (secrets redacted).
- ``logging_db_call``: decorator that logs DB inputs/outputs (secrets redacted).
- ``log_call(kind)``: generic decorator for any function.
- ``setup_logging()``: convenience to initialize the root logger once.

Secret values (API keys, tokens, passwords, DB URLs, bearer tokens) are
replaced with ``***`` on both input and output sides.
"""

from __future__ import annotations

import functools
import json
import logging
import re
import sys
import time
from typing import Any, Callable, Optional, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

# ---------------------------------------------------------------------------
# ANSI color constants (matching the reference layout)
# ---------------------------------------------------------------------------


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


LEVEL_COLORS = {
    "DEBUG": Colors.BLUE,
    "INFO": Colors.GREEN,
    "WARNING": Colors.YELLOW,
    "ERROR": Colors.RED,
    "CRITICAL": Colors.BRIGHT_RED,
}

# ---------------------------------------------------------------------------
# Secret redaction
# ---------------------------------------------------------------------------

_SECRET_KV = re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*\S+")
_DATABASE_URL = re.compile(r"://[^:]+:[^@]+@")
_BEARER = re.compile(r"(?i)bearer\s+\S+")


def _redact_string(value: str) -> str:
    value = _DATABASE_URL.sub("://***:***@", value)
    value = _BEARER.sub("bearer ***", value)
    value = _SECRET_KV.sub(lambda m: m.group(1) + "=***", value)
    return value


def sanitize(value: Any) -> Any:
    """Recursively redact secrets from strings, dicts, lists, tuples, sets."""
    if isinstance(value, str):
        return _redact_string(value)

    if hasattr(value, "model_dump"):  # pydantic v2
        return sanitize(value.model_dump())
    if hasattr(value, "dict"):  # pydantic v1
        return sanitize(value.dict())

    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return type(value)(sanitize(v) for v in value)
    return value


# ---------------------------------------------------------------------------
# Colored formatter
# ---------------------------------------------------------------------------


class ColoredFormatter(logging.Formatter):
    """Log formatter that colors the level name based on severity."""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, use_colors: bool = True):
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors and record.levelname in LEVEL_COLORS:
            color = LEVEL_COLORS[record.levelname]
            record.levelname = f"{color}{record.levelname}{Colors.RESET}"
        return super().format(record)


# ---------------------------------------------------------------------------
# Logger manager (matches reference layout)
# ---------------------------------------------------------------------------


class LoggerManager:
    """Builds and manages a logger with a colored console handler."""

    def __init__(self, name: str, level: str | int = "INFO", use_colors: bool = True):
        self.name = name
        if isinstance(level, int):
            level = logging.getLevelName(level)
        self.level = getattr(logging, level.upper(), logging.INFO)
        self.use_colors = use_colors
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        logger.propagate = False  # prevent double-logging to root

        if not logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level)

            fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
            formatter = ColoredFormatter(fmt=fmt, datefmt=datefmt, use_colors=self.use_colors)
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        return logger

    # --- convenience methods ------------------------------------------------

    def debug(self, message: str, **kwargs: Any) -> None:
        self.logger.debug(self._format_message(message, **kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        self.logger.error(self._format_message(message, **kwargs))

    def critical(self, message: str, **kwargs: Any) -> None:
        self.logger.critical(self._format_message(message, **kwargs))

    def exception(self, message: str, **kwargs: Any) -> None:
        self.logger.exception(self._format_message(message, **kwargs))

    # --- helpers ------------------------------------------------------------

    @staticmethod
    def _format_message(message: str, **kwargs: Any) -> str:
        if not kwargs:
            return message
        context = json.dumps(kwargs, default=str, ensure_ascii=False)
        return f"{message} | Context: {context}"


# Global default logger instance
logger = LoggerManager(name="ai.support", level="INFO", use_colors=True).logger

# Backward-compatible module-level logger for `logging.getLogger(__name__)` users.
_module_logger = logging.getLogger("ai.support")


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def _log_call(
    kind: str,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    result: Any | None = None,
    error: BaseException | None = None,
    duration_ms: float | None = None,
) -> None:
    name = f"{func.__module__}.{func.__qualname__}"
    parts: list[str] = [f"[{kind}]", name]

    if args or kwargs:
        parts.append(f"args={sanitize(args)}")
        parts.append(f"kwargs={sanitize(kwargs)}")
    if result is not None:
        parts.append(f"result={sanitize(result)}")
    if error is not None:
        parts.append(f"error={type(error).__name__}: {error}")
    if duration_ms is not None:
        parts.append(f"duration_ms={round(duration_ms, 1)}")

    _module_logger.info(" ".join(parts))


def logging_llm_call(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator that logs an LLM call with sanitized inputs/outputs and timing."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as error:  # noqa: BLE001
            duration_ms = (time.perf_counter() - start) * 1000
            _log_call("llm", func, args, kwargs, error=error, duration_ms=duration_ms)
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        _log_call("llm", func, args, kwargs, result=result, duration_ms=duration_ms)
        return result

    return wrapper


def logging_db_call(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator that logs a database call with sanitized inputs/outputs and timing."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as error:  # noqa: BLE001
            duration_ms = (time.perf_counter() - start) * 1000
            _log_call("db", func, args, kwargs, error=error, duration_ms=duration_ms)
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        _log_call("db", func, args, kwargs, result=result, duration_ms=duration_ms)
        return result

    return wrapper


def log_call(kind: str = "call") -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Generic decorator factory for logging any function's inputs/outputs."""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            except Exception as error:  # noqa: BLE001
                duration_ms = (time.perf_counter() - start) * 1000
                _log_call(kind, func, args, kwargs, error=error, duration_ms=duration_ms)
                raise
            duration_ms = (time.perf_counter() - start) * 1000
            _log_call(kind, func, args, kwargs, result=result, duration_ms=duration_ms)
            return result

        return wrapper

    return decorator


def setup_logging(level: str | int = "INFO") -> None:
    """Initialize the default logger once at process startup."""
    global logger
    if isinstance(level, int):
        level = logging.getLevelName(level)
    manager = LoggerManager(name="ai.support", level=level, use_colors=True)
    logger = manager.logger
