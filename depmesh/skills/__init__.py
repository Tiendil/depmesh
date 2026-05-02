from __future__ import annotations

import importlib.resources


def load_skill_text() -> str:
    return importlib.resources.files(__name__).joinpath("fixtures", "skill.md").read_text(encoding="utf-8")
