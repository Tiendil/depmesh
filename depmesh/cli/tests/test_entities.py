from __future__ import annotations

import pytest
import typer

from depmesh.cli.entities import (
    _parse_artifact,
    _parse_relation,
    _validate_artifacts,
)
from depmesh.domain.entities import ArtifactId, RelationId


class TestParseArtifact:
    def test_success(self) -> None:
        assert _parse_artifact("./src/a.py") == ArtifactId("./src/a.py")


class TestValidateArtifacts:
    def test_success(self) -> None:
        artifacts = [ArtifactId("./src/a.py")]

        assert _validate_artifacts(artifacts) == artifacts

    @pytest.mark.parametrize("values", [None, []])
    def test_missing_artifacts_use_shared_diagnostic(
        self, capsys: pytest.CaptureFixture[str], values: list[ArtifactId] | None
    ) -> None:
        with pytest.raises(typer.Exit) as caught:
            _validate_artifacts(values)

        assert caught.value.exit_code == 1
        captured = capsys.readouterr()
        assert not captured.out
        assert captured.err.startswith("----- DEPMESH CELL ")
        assert "code = invalid_arguments\n" in captured.err
        assert "at least one artifact is required" in captured.err


class TestParseRelation:
    def test_success(self) -> None:
        assert _parse_relation("tests") == RelationId("tests")
