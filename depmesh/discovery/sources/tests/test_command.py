from __future__ import annotations

from pathlib import Path

from depmesh.core import warnings
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.sources.command import CommandSource
from depmesh.domain.entities import ArtifactId, RelationId


class TestCommandSource:
    def test_variables__extracts_template_variables(self) -> None:
        source = CommandSource(type="command", command="printf './tests/test_{module}.py\\n'")

        assert source.variables() == {CaptureName("module")}

    def test_evaluate__returns_stdout_artifacts(self, tmp_path: Path) -> None:
        source = CommandSource(type="command", command="printf './tests/test_{module}.py\\n'")
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert source.evaluate(context) == [ArtifactId("./tests/test_a.py")]

    def test_evaluate__records_warnings(self, tmp_path: Path) -> None:
        warnings.clear()
        source = CommandSource(
            type="command",
            command="printf './tests/test_a.py\\n'; printf 'diagnostic\\n' >&2; exit 7",
        )
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={})

        assert source.evaluate(context) == [ArtifactId("./tests/test_a.py")]
        assert warnings.read() == [
            "relation `tests`: command stderr: diagnostic",
            "relation `tests`: command exited with status 7: "
            "printf './tests/test_a.py\\n'; printf 'diagnostic\\n' >&2; exit 7",
        ]
        warnings.clear()
