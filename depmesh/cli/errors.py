from __future__ import annotations

from depmesh.core import errors as core_errors


class Error(core_errors.Error):
    code = "cli_error"


class InvalidArguments(Error):
    code = "invalid_arguments"

    def __init__(self, message: str) -> None:
        super().__init__(message)
