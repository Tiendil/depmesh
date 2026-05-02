from __future__ import annotations

import importlib.resources

from depmesh.skills.entities import SkillDocument

_FIXTURES: dict[SkillDocument, str] = {
    SkillDocument.usage: "usage.md",
    SkillDocument.configuration: "configuration.md",
    SkillDocument.initialization: "initialization.md",
}


def load_skill_text(document: SkillDocument = SkillDocument.usage) -> str:
    return (
        importlib.resources.files(__package__)
        .joinpath("fixtures", _FIXTURES[document])
        .read_text(encoding="utf-8")
    )
