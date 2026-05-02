from __future__ import annotations

from pathlib import Path
from typing import Any

from depmesh.core import errors as core_errors


class Error(core_errors.Error):
    code = "workspace_error"


class ConfigNotFound(Error):
    code = "config_not_found"

    def __init__(self, start: Path) -> None:
        super().__init__("depmesh.toml was not found", details={"path": str(start)})


class ConfigUnreadable(Error):
    code = "config_unreadable"

    def __init__(self, path: Path, original: Exception | None = None) -> None:
        super().__init__(f"could not read configuration file `{path}`", details={"path": str(path)})
        if original is not None:
            self.__cause__ = original


class ConfigInvalid(Error):
    code = "config_invalid"

    def __init__(self, message: str, *, path: Path | None = None, details: dict[str, Any] | None = None) -> None:
        merged_details = details or {}
        if path is not None:
            merged_details = {"path": str(path), **merged_details}
        super().__init__(message, details=merged_details)

