from __future__ import annotations

from pathlib import Path

from depmesh.discovery.expressions.regex import RegexExpression
from depmesh.discovery.expressions.entities import EvaluationContext
from depmesh.discovery.matchers import CaptureName
from depmesh.domain.entities import ArtifactId, RelationId


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestRegexExpression:
    def test_variables__extracts_template_variables(self) -> None:
        expression = RegexExpression(type="regex", pattern=r"^\./specs/{module}\.md$")

        assert expression.variables() == {CaptureName("module")}

    def test_evaluate__returns_matching_files_in_order(self, tmp_path: Path) -> None:
        touch(tmp_path / "specs/a.md")
        touch(tmp_path / "specs/b.md")
        expression = RegexExpression(type="regex", pattern=r"^\./specs/{module}\.md$")
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("specs"), captures={"module": "a"})

        assert expression.evaluate(context) == [ArtifactId("./specs/a.md")]

    def test_evaluate__supports_complex_template_pattern(self, tmp_path: Path) -> None:
        touch(tmp_path / "packages/core/tests/unit/test_api_a.py")
        touch(tmp_path / "packages/core/tests/unit/test_api_b.py")
        touch(tmp_path / "packages/core/tests/integration/test_cli_a.py")
        touch(tmp_path / "packages/ui/tests/unit/test_api_a.py")
        expression = RegexExpression(
            type="regex",
            pattern=r"^\./packages/{package}/tests/.+/test_{module}_[a-z]\.py$",
        )
        context = EvaluationContext(
            root=tmp_path,
            relation_id=RelationId("tests"),
            captures={"package": "core", "module": "api"},
        )

        assert expression.evaluate(context) == [
            ArtifactId("./packages/core/tests/unit/test_api_a.py"),
            ArtifactId("./packages/core/tests/unit/test_api_b.py"),
        ]
