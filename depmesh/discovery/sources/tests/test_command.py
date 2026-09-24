from __future__ import annotations

from pathlib import Path

from depmesh.core import warnings
from depmesh.discovery import errors
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.sources.command import CommandSource, CommandSourceConfig
from depmesh.domain.entities import ArtifactId, ProjectRootPath, RelationId


class TestCommandSource:
    def test_evaluate__startup_failure_is_returned(self, tmp_path: Path) -> None:
        source = CommandSource(CommandSourceConfig(type="command", command="printf '@/a.py'"))
        context = EvaluationContext(
            root=ProjectRootPath(tmp_path / "missing"), relation_id=RelationId("tests"), captures={}
        )

        failure = source.evaluate(context).unwrap_err()[0]

        assert isinstance(failure, errors.CommandFailed)
        assert failure.relation == "tests"
        assert isinstance(failure.cause, FileNotFoundError)

    def test_evaluate__invalid_output_path_is_returned(self, tmp_path: Path) -> None:
        source = CommandSource(CommandSourceConfig(type="command", command="printf '../outside.py'"))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={})

        assert source.evaluate(context).unwrap_err() == [errors.InvalidProjectPath(path="../outside.py")]

    def test_variables__extracts_template_variables(self) -> None:
        source = CommandSourceConfig(type="command", command="printf '@/tests/test_{module}.py\\n'")

        assert source.variables() == {CaptureName("module")}

    def test_evaluate__returns_stdout_artifacts(self, tmp_path: Path) -> None:
        source = CommandSource(CommandSourceConfig(type="command", command="printf '@/tests/test_{module}.py\\n'"))
        context = EvaluationContext(
            root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={"module": "a"}
        )

        assert source.evaluate(context).unwrap() == [ArtifactId("@/tests/test_a.py")]

    def test_evaluate__records_warnings(self, tmp_path: Path) -> None:
        warnings.clear()
        source = CommandSource(
            CommandSourceConfig(
                type="command",
                command="printf '@/tests/test_a.py\\n'; printf 'diagnostic\\n' >&2; exit 7",
            )
        )
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={})

        assert source.evaluate(context).unwrap() == [ArtifactId("@/tests/test_a.py")]
        assert warnings.read() == [
            "relation `tests`: command stderr: diagnostic",
            "relation `tests`: command exited with status 7: "
            "printf '@/tests/test_a.py\\n'; printf 'diagnostic\\n' >&2; exit 7",
        ]
        warnings.clear()
