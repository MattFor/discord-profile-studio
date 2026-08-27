from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, overload

R = TypeVar("R")
P = ParamSpec("P")


class _ElapsedFormatter(logging.Formatter):
    def __init__(self, started: float) -> None:
        super().__init__()
        self._started = started

    def format(self, record: logging.LogRecord) -> str:
        elapsed = time.perf_counter() - self._started
        message = record.getMessage()
        return f"[{elapsed:8.3f}s] {record.levelname:<7} {record.name}: {message}"


class _LoggerManager:
    def __init__(self) -> None:
        self.started = time.perf_counter()
        self.verbose = False
        self.initialized = False
        self._handler: logging.Handler | None = None

    def setup(self, *, verbose: bool = False) -> None:
        self.verbose = verbose

        root = logging.getLogger()
        root.setLevel(logging.DEBUG if verbose else logging.INFO)

        if self._handler is None:
            handler = logging.StreamHandler()
            handler.setFormatter(_ElapsedFormatter(self.started))
            self._handler = handler

        if self._handler not in root.handlers:
            root.addHandler(self._handler)

        self.initialized = True

    def get(self, name: str) -> logging.Logger:
        if not self.initialized:
            self.setup()

        return logging.getLogger(name)


_manager = _LoggerManager()


def setup(*, verbose: bool = False) -> None:
    _manager.setup(verbose=verbose)


def get(name: str) -> logging.Logger:
    return _manager.get(name)


@overload
def logged(func: Callable[P, R]) -> Callable[P, R]: ...


@overload
def logged(
    *,
    logger: logging.Logger | None = None,
    level: int = logging.INFO,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def logged(
    func: Callable[P, R] | None = None,
    *,
    logger: logging.Logger | None = None,
    level: int = logging.INFO,
) -> Callable[..., Any]:
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        log = logger or get(fn.__module__)

        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            log.log(level, "-> %s()", fn.__qualname__)

            try:
                result = fn(*args, **kwargs)
            except Exception:
                log.exception("X %s()", fn.__qualname__)
                raise

            log.log(level, "<- %s()", fn.__qualname__)
            return result

        return wrapper

    if func is None:
        return decorator

    return decorator(func)
