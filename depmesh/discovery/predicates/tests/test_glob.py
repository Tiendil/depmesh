from __future__ import annotations

from pathlib import Path

import pytest
from llm_tool_cli.core.result import UnwrapError
from llm_tool_cli.paths import ProjectRootPath
from llm_tool_cli.paths.errors import PathResolutionFailed

from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates.glob import GlobPredicate, GlobPredicateConfig
from depmesh.domain.entities import ArtifactId


class TestGlobPredicate:
    def test_match__normalizes_root_anchored_pattern_and_preserves_captures(self, tmp_path: Path) -> None:
        predicate = GlobPredicate(GlobPredicateConfig(type="glob", pattern="@/./src/{**package}/{*module}.py"))

        assert predicate.match(ArtifactId("@/src/core/api.py"), ProjectRootPath(tmp_path)) == {
            "package": "core",
            "module": "api",
        }

    def test_match__invalid_root_anchored_pattern_does_not_match(self, tmp_path: Path) -> None:
        predicate = GlobPredicate(GlobPredicateConfig(type="glob", pattern="@/../*.py"))

        assert predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path)) is None

    def test_match__empty_substituted_pattern_does_not_match(self, tmp_path: Path) -> None:
        predicate = GlobPredicate(GlobPredicateConfig(type="glob", pattern="{pattern}"))

        assert predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path), {"pattern": ""}) is None

    def test_match__resolution_failure_is_not_recovered(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        predicate = GlobPredicate(GlobPredicateConfig(type="glob", pattern="src/*.py"))
        original = PermissionError("permission denied")
        resolve = Path.resolve

        def fail_resolution(path: Path) -> Path:
            if path == tmp_path / "src" / "*.py":
                raise original
            return resolve(path)

        monkeypatch.setattr(Path, "resolve", fail_resolution)

        with pytest.raises(UnwrapError) as caught:
            predicate.match(ArtifactId("@/src/a.py"), ProjectRootPath(tmp_path))

        failures = caught.value.details["error"]
        assert isinstance(failures, list)
        assert len(failures) == 1
        failure = failures[0]
        assert isinstance(failure, PathResolutionFailed)
        assert failure.path == str(tmp_path / "src" / "*.py")
        assert failure.cause is original

    def test_match__invalid_substituted_capture_raises(self, tmp_path: Path) -> None:
        predicate = GlobPredicate(GlobPredicateConfig(type="glob", pattern="@/{pattern}"))

        with pytest.raises(ValueError):
            predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path), {"pattern": "{*invalid-name}"})

    def test_variables__extracts_template_variables(self) -> None:
        predicate = GlobPredicateConfig(type="glob", pattern="@/src/{package}/{*module}.py")

        assert predicate.variables() == {CaptureName("package")}

    def test_captures__extracts_capture_names(self) -> None:
        predicate = GlobPredicateConfig(type="glob", pattern="@/src/{**package}/{*module}.py")

        assert predicate.captures() == {CaptureName("package"), CaptureName("module")}

    def test_match__supports_templates_and_captures(self, tmp_path: Path) -> None:
        predicate = GlobPredicate(GlobPredicateConfig(type="glob", pattern="@/src/{package}/{*module}.py"))

        assert predicate.match(ArtifactId("@/src/core/api.py"), ProjectRootPath(tmp_path), {"package": "core"}) == {
            "module": "api"
        }

    def test_match__returns_none_for_missing_artifact(self, tmp_path: Path) -> None:
        predicate = GlobPredicate(GlobPredicateConfig(type="glob", pattern="@/src/{*module}.py"))

        assert predicate.match(ArtifactId("@/docs/a.md"), ProjectRootPath(tmp_path)) is None
