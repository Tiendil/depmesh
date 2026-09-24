from __future__ import annotations

import importlib.resources

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result

from depmesh.skills.entities import SkillDocument
from depmesh.skills.errors import SkillUnreadable

_FIXTURES: dict[SkillDocument, str] = {
    SkillDocument.usage: "usage.md",
    SkillDocument.configuration: "configuration.md",
    SkillDocument.initialization: "initialization.md",
}


def load_skill_text(document: SkillDocument = SkillDocument.usage) -> Result[str, EnvironmentErrors]:
    try:
        return Ok(
            importlib.resources.files(__package__)
            .joinpath("fixtures", _FIXTURES[document])
            .read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError) as error:
        return Err([SkillUnreadable(document=document, reason=str(error)).with_cause(error)])
