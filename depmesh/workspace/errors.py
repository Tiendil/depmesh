from __future__ import annotations

from depmesh.core import errors as core_errors


class EnvironmentError(core_errors.EnvironmentError):
    code: str = "workspace_error"


class ConfigTemplateUnreadable(EnvironmentError):
    code: str = "config_template_unreadable"
    message: str = "could not read configuration template `{error.template}`: {error.reason}"
    template: str
    reason: str
