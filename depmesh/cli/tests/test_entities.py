from __future__ import annotations

from depmesh.cli.entities import _parse_artifact, _parse_relation
from depmesh.domain.entities import ArtifactId, RelationId


class TestParseArtifact:
    def test_success(self) -> None:
        assert _parse_artifact("./src/a.py") == ArtifactId("./src/a.py")


class TestParseRelation:
    def test_success(self) -> None:
        assert _parse_relation("tests") == RelationId("tests")
