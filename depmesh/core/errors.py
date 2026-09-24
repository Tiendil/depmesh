from llm_tool_cli.core import errors as shared_errors


class InternalError(shared_errors.InternalError):
    """Root for internal project exceptions."""


class EnvironmentError(shared_errors.EnvironmentError):
    """Root for expected project failures returned as values."""

    code: str = "project_error"
    message: str = "The request could not be completed."
