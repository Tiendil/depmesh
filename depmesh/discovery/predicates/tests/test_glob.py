from __future__ import annotations

from pathlib import Path

from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates.glob import GlobPredicate
from depmesh.domain.entities import ArtifactId


class TestGlobPredicate:
    def test_variables__extracts_template_variables(self) -> None:
        predicate = GlobPredicate(type="glob", pattern="./src/{package}/{*module}.py")

        assert predicate.variables() == {CaptureName("package")}

    def test_captures__extracts_capture_names(self) -> None:
        predicate = GlobPredicate(type="glob", pattern="./src/{**package}/{*module}.py")

        assert predicate.captures() == {CaptureName("package"), CaptureName("module")}

    def test_match__supports_templates_and_captures(self, tmp_path: Path) -> None:
        predicate = GlobPredicate(type="glob", pattern="./src/{package}/{*module}.py")

        assert predicate.match(ArtifactId("./src/core/api.py"), tmp_path, {"package": "core"}) == {"module": "api"}

    def test_match__returns_none_for_missing_artifact(self, tmp_path: Path) -> None:
        predicate = GlobPredicate(type="glob", pattern="./src/{*module}.py")

        assert predicate.match(ArtifactId("./docs/a.md"), tmp_path) is None
