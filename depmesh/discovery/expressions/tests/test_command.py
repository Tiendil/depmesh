from __future__ import annotations

from pathlib import Path

from depmesh.core import warnings
from depmesh.discovery.expressions.command import CommandExpression
from depmesh.discovery.expressions.entities import EvaluationContext
from depmesh.discovery.matchers import CaptureName
from depmesh.domain.entities import ArtifactId, RelationId


class TestCommandExpression:
    def test_variables__extracts_template_variables(self) -> None:
        expression = CommandExpression(type="command", command="printf './tests/test_{module}.py\\n'")

        assert expression.variables() == {CaptureName("module")}

    def test_evaluate__returns_stdout_paths(self, tmp_path: Path) -> None:
        expression = CommandExpression(type="command", command="printf './tests/test_{module}.py\\n'")
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert expression.evaluate(context) == [ArtifactId("./tests/test_a.py")]

    def test_evaluate__normalizes_complex_stdout_paths(self, tmp_path: Path) -> None:
        expression = CommandExpression(
            type="command",
            command="printf ' tests/./test_{module}.py \\n\\n./specs/{module}.md\\n'",
        )
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert expression.evaluate(context) == [ArtifactId("./tests/test_a.py"), ArtifactId("./specs/a.md")]

    def test_evaluate__returns_stdout_paths_with_warnings(self, tmp_path: Path) -> None:
        warnings.clear()
        expression = CommandExpression(
            type="command",
            command="printf './tests/test_{module}.py\\n'; printf 'problem\\n' >&2; exit 3",
        )
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert expression.evaluate(context) == [ArtifactId("./tests/test_a.py")]
        assert warnings.read() == [
            "relation `tests`: command stderr: problem",
            "relation `tests`: command exited with status 3: printf './tests/test_a.py\\n'; printf 'problem\\n' >&2; exit 3",
        ]
        warnings.clear()

    def test_evaluate__stderr_and_nonzero_add_warnings(self, tmp_path: Path) -> None:
        warnings.clear()
        expression = CommandExpression(type="command", command="printf 'problem\\n' >&2; exit 3")
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={})

        assert expression.evaluate(context) == []
        assert warnings.read() == [
            "relation `tests`: command stderr: problem",
            "relation `tests`: command exited with status 3: printf 'problem\\n' >&2; exit 3",
        ]
        warnings.clear()
