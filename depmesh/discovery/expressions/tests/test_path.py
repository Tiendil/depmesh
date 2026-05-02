from __future__ import annotations

from pathlib import Path

from depmesh.core import warnings
from depmesh.discovery.expressions.path import PathExpression
from depmesh.discovery.expressions.entities import EvaluationContext
from depmesh.discovery.matchers import CaptureName
from depmesh.domain.entities import ArtifactId, RelationId


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestPathExpression:
    def test_variables__extracts_template_variables(self) -> None:
        expression = PathExpression(type="path", path="./tests/test_{module}.py")

        assert expression.variables() == {CaptureName("module")}

    def test_evaluate__returns_existing_file(self, tmp_path: Path) -> None:
        touch(tmp_path / "tests/test_a.py")
        expression = PathExpression(type="path", path="./tests/test_{module}.py")
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert expression.evaluate(context) == [ArtifactId("./tests/test_a.py")]

    def test_evaluate__normalizes_complex_template_path(self, tmp_path: Path) -> None:
        touch(tmp_path / "packages/core/tests/test_api.py")
        expression = PathExpression(
            type="path",
            path="./packages/{package}/../{package}/tests/./test_{module}.py",
        )
        context = EvaluationContext(
            root=tmp_path,
            relation_id=RelationId("tests"),
            captures={"package": "core", "module": "api"},
        )

        assert expression.evaluate(context) == [ArtifactId("./packages/core/tests/test_api.py")]

    def test_evaluate__missing_file_adds_warning(self, tmp_path: Path) -> None:
        warnings.clear()
        expression = PathExpression(type="path", path="./tests/test_{module}.py")
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert expression.evaluate(context) == []
        assert warnings.read() == ["relation `tests`: skipped missing dependency `./tests/test_a.py`"]
        warnings.clear()

    def test_evaluate__invalid_path_adds_warning(self, tmp_path: Path) -> None:
        warnings.clear()
        expression = PathExpression(type="path", path="../tests/test_{module}.py")
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert expression.evaluate(context) == []
        assert warnings.read() == ["relation `tests`: skipped invalid dependency path `../tests/test_a.py`"]
        warnings.clear()
