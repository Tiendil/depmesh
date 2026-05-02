from __future__ import annotations

from depmesh.skills import load_skill_text


class TestLoadSkillText:
    def test_returns_markdown_skill_text(self) -> None:
        assert load_skill_text().startswith("# depmesh usage\n")
