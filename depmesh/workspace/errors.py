from __future__ import annotations

from depmesh.core import errors as core_errors


class Error(core_errors.Error):
    code = "workspace_error"


class ConfigTemplateUnreadable(Error):
    code = "config_template_unreadable"

    def __init__(self, template: str, reason: str) -> None:
        super().__init__(
            f"could not read configuration template `{template}`: {reason}",
            details={"template": template, "reason": reason},
        )
