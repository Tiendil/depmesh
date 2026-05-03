from __future__ import annotations

_warnings: list[str] = []


def add(message: str) -> None:
    _warnings.append(message)


def read() -> list[str]:
    return list(_warnings)


def clear() -> None:
    _warnings.clear()
