from __future__ import annotations

from depmesh.skills.entities import SkillDocument
from depmesh.skills.fixtures import load_skill_text


class TestLoadSkillText:
    def test_returns_usage_document_by_default(self) -> None:
        assert load_skill_text().startswith("# `depmesh` Usage\n")

    def test_returns_configuration_document(self) -> None:
        assert load_skill_text(SkillDocument.configuration).startswith("# `depmesh` Configuration\n")

    def test_returns_initialization_document(self) -> None:
        assert load_skill_text(SkillDocument.initialization).startswith("# `depmesh` Initialization\n")
