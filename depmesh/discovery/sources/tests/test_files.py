from __future__ import annotations

from pathlib import Path

from depmesh.core import warnings
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.sources.files import FilesSource, FilesSourceConfig
from depmesh.domain.entities import ArtifactId, RelationId


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestFilesSource:
    def test_variables__extracts_template_variables(self) -> None:
        source = FilesSourceConfig(type="files", pattern="@/tests/test_{module}.py")

        assert source.variables() == {CaptureName("module")}

    def test_evaluate__returns_all_files_without_pattern(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "docs/a.md")
        source = FilesSource(FilesSourceConfig(type="files"))
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("all"), captures={})

        assert source.evaluate(context) == [ArtifactId("@/docs/a.md"), ArtifactId("@/src/a.py")]

    def test_evaluate__returns_matching_files(self, tmp_path: Path) -> None:
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "tests/test_b.py")
        source = FilesSource(FilesSourceConfig(type="files", pattern="@/tests/test_{module}.py"))
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert source.evaluate(context) == [ArtifactId("@/tests/test_a.py")]

    def test_evaluate__invalid_pattern_adds_warning(self, tmp_path: Path) -> None:
        warnings.clear()
        source = FilesSource(FilesSourceConfig(type="files", pattern="../tests/*.py"))
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={})

        assert source.evaluate(context) == []
        assert warnings.read() == ["relation `tests`: skipped invalid files source pattern `../tests/*.py`"]
        warnings.clear()
