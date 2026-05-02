from __future__ import annotations

from pathlib import Path

import pytest
import typer

from depmesh.cli.entities import (
    GlobalOptions,
    _parse_artifact,
    _parse_config,
    _parse_protocol,
    _parse_relation,
    _validate_artifacts,
)
from depmesh.domain.entities import ArtifactId, RelationId
from depmesh.protocol import OutputProtocol


class TestGlobalOptions:
    def test_defaults(self) -> None:
        options = GlobalOptions()

        assert options.protocol is None
        assert options.config is None

    def test_values(self) -> None:
        options = GlobalOptions(protocol=OutputProtocol.automation, config=Path("./depmesh.toml"))

        assert options.protocol is OutputProtocol.automation
        assert options.config == Path("./depmesh.toml")


class TestParseArtifact:
    def test_success(self) -> None:
        assert _parse_artifact("./src/a.py") == ArtifactId("./src/a.py")


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


class TestParseConfig:
    def test_success(self) -> None:
        assert _parse_config("./depmesh.toml") == Path("./depmesh.toml")


class TestParseProtocol:
    def test_success(self) -> None:
        assert _parse_protocol("automation") is OutputProtocol.automation

    def test_unsupported_value(self) -> None:
        with pytest.raises(typer.Exit):
            _parse_protocol("unknown")


class TestParseRelation:
    def test_success(self) -> None:
        assert _parse_relation("tests") == RelationId("tests")
