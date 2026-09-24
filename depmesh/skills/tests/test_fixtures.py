from __future__ import annotations

import importlib.resources
from pathlib import Path

import pytest

from depmesh.skills.entities import SkillDocument
from depmesh.skills.errors import SkillUnreadable
from depmesh.skills.fixtures import load_skill_text


class TestLoadSkillText:
    @pytest.mark.parametrize("content", [None, b"\xff"])
    def test_read_failure_is_returned(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: bytes | None
    ) -> None:
        fixtures = tmp_path / "fixtures"
        fixtures.mkdir()
        if content is not None:
            (fixtures / "usage.md").write_bytes(content)
        monkeypatch.setattr(importlib.resources, "files", lambda _package: tmp_path)

        failure = load_skill_text().unwrap_err()[0]

        assert isinstance(failure, SkillUnreadable)
        assert failure.document is SkillDocument.usage
        assert isinstance(failure.cause, FileNotFoundError if content is None else UnicodeDecodeError)

    def test_returns_usage_document_by_default(self) -> None:
        assert load_skill_text().unwrap().startswith("# `depmesh` Usage\n")

    def test_returns_configuration_document(self) -> None:
        assert load_skill_text(SkillDocument.configuration).unwrap().startswith("# `depmesh` Configuration\n")

    def test_returns_initialization_document(self) -> None:
        assert load_skill_text(SkillDocument.initialization).unwrap().startswith("# `depmesh` Initialization\n")
