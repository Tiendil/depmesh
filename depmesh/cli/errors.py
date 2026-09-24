from __future__ import annotations

from depmesh.core import errors as core_errors


class EnvironmentError(core_errors.EnvironmentError):
    code: str = "cli_error"


class InvalidArguments(EnvironmentError):
    code: str = "invalid_arguments"
    message: str = "{error.reason}"
    reason: str
