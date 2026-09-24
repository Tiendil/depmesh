from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from depmesh.core import warnings
from depmesh.discovery import errors
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.sources.files import FilesSource, FilesSourceConfig
from depmesh.domain.entities import ArtifactId, ProjectRootPath, RelationId


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestFilesSource:
    def test_evaluate__filesystem_failure_returns_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        original = PermissionError("permission denied")

        def fail_glob(_path: Path, _pattern: str) -> Iterator[Path]:
            raise original

        monkeypatch.setattr(Path, "rglob", fail_glob)
        source = FilesSource(FilesSourceConfig(type="files"))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("all"), captures={})

        failure = source.evaluate(context).unwrap_err()[0]

        assert isinstance(failure, errors.FilesUnreadable)
        assert failure.cause is original

    def test_variables__extracts_template_variables(self) -> None:
        source = FilesSourceConfig.model_validate({"type": "files", "pattern": "@/tests/test_{module}.py"})

        assert source.variables() == {CaptureName("module")}

    def test_evaluate__returns_all_files_without_pattern(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "docs/a.md")
        source = FilesSource(FilesSourceConfig(type="files"))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("all"), captures={})

        assert source.evaluate(context).unwrap() == [ArtifactId("@/docs/a.md"), ArtifactId("@/src/a.py")]

    def test_evaluate__returns_matching_files(self, tmp_path: Path) -> None:
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "tests/test_b.py")
        source = FilesSource(
            FilesSourceConfig.model_validate({"type": "files", "pattern": "@/tests/test_{module}.py"})
        )
        context = EvaluationContext(
            root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={"module": "a"}
        )

        assert source.evaluate(context).unwrap() == [ArtifactId("@/tests/test_a.py")]

    def test_evaluate__invalid_pattern_adds_warning(self, tmp_path: Path) -> None:
        warnings.clear()
        source = FilesSource(FilesSourceConfig.model_validate({"type": "files", "pattern": "../tests/*.py"}))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={})

        assert source.evaluate(context).unwrap() == []
        assert warnings.read() == ["relation `tests`: skipped invalid files source pattern `../tests/*.py`"]
        warnings.clear()
