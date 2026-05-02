from __future__ import annotations

from depmesh.skills.entities import SkillDocument


class TestSkillDocument:
    def test_values(self) -> None:
        assert SkillDocument.usage.value == "usage"
        assert SkillDocument.configuration.value == "configuration"
        assert SkillDocument.initialization.value == "initialization"
