from __future__ import annotations

from typing import Any


class Error(Exception):
    code = "error"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.__class__.__name__
        self.details = details or {}
        if code is not None:
            self.code = code
        super().__init__(self.message)

    def as_record(self) -> dict[str, Any]:
        return {"type": "error", "code": self.code, "message": self.message, **self.details}

