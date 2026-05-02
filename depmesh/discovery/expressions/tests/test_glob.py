from __future__ import annotations

from pathlib import Path

from depmesh.core import warnings
from depmesh.discovery.expressions.glob import GlobExpression
from depmesh.discovery.expressions.entities import EvaluationContext
from depmesh.discovery.matchers import CaptureName
from depmesh.domain.entities import ArtifactId, RelationId


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestGlobExpression:
    def test_variables__extracts_template_variables(self) -> None:
        expression = GlobExpression(type="glob", pattern="./tests/test_{module}_*.py")

        assert expression.variables() == {CaptureName("module")}

    def test_evaluate__returns_matching_files_in_order(self, tmp_path: Path) -> None:
        touch(tmp_path / "tests/test_a_b.py")
        touch(tmp_path / "tests/test_a_a.py")
        touch(tmp_path / "tests/test_b_a.py")
        expression = GlobExpression(type="glob", pattern="./tests/test_{module}_*.py")
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert expression.evaluate(context) == [ArtifactId("./tests/test_a_a.py"), ArtifactId("./tests/test_a_b.py")]

    def test_evaluate__supports_recursive_template_patterns(self, tmp_path: Path) -> None:
        touch(tmp_path / "packages/core/tests/unit/test_api_a.py")
        touch(tmp_path / "packages/core/tests/unit/test_api_b.py")
        touch(tmp_path / "packages/core/tests/integration/test_cli_a.py")
        touch(tmp_path / "packages/ui/tests/unit/test_api_a.py")
        (tmp_path / "packages/core/tests/unit/test_api_dir.py").mkdir(parents=True)
        expression = GlobExpression(type="glob", pattern="./packages/{package}/**/test_{module}_*.py")
        context = EvaluationContext(
            root=tmp_path,
            relation_id=RelationId("tests"),
            captures={"package": "core", "module": "api"},
        )

        assert expression.evaluate(context) == [
            ArtifactId("./packages/core/tests/unit/test_api_a.py"),
            ArtifactId("./packages/core/tests/unit/test_api_b.py"),
        ]

    def test_evaluate__invalid_pattern_adds_warning(self, tmp_path: Path) -> None:
        warnings.clear()
        expression = GlobExpression(type="glob", pattern="../tests/test_{module}_*.py")
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert expression.evaluate(context) == []
        assert warnings.read() == ["relation `tests`: skipped invalid dependency glob `../tests/test_a_*.py`"]
        warnings.clear()
