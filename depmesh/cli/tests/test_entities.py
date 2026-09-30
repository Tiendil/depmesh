from __future__ import annotations

import pytest
import typer

from depmesh.cli.entities import (
    _exit_with_invalid_arguments,
    _parse_artifact,
    _parse_relation,
    _validate_artifacts,
)
from depmesh.domain.entities import ArtifactId, RelationId


class TestParseArtifact:
    def test_success(self) -> None:
        assert _parse_artifact("./src/a.py") == ArtifactId("./src/a.py")


class TestExitWithInvalidArguments:
    def test_shared_human_cell_uses_stderr_and_exit_one(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(typer.Exit) as caught:
            _exit_with_invalid_arguments("Invalid café 日本語")

        assert caught.value.exit_code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err.startswith("----- DEPMESH CELL ")
        assert "kind = error\n" in captured.err
        assert "code = invalid_arguments\n" in captured.err
        assert "reason = Invalid café 日本語\n" in captured.err
        assert "type = error\n" in captured.err
        assert "Invalid café 日本語" in captured.err


class TestValidateArtifacts:
    def test_success(self) -> None:
        artifacts = [ArtifactId("./src/a.py")]

        assert _validate_artifacts(artifacts) == artifacts

    def test_empty(self) -> None:
        with pytest.raises(typer.Exit):
            _validate_artifacts([])

    def test_none(self) -> None:
        with pytest.raises(typer.Exit):
            _validate_artifacts(None)


class TestParseRelation:
    def test_success(self) -> None:
        assert _parse_relation("tests") == RelationId("tests")
