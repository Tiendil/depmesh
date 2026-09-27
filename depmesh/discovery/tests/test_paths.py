from __future__ import annotations

from pathlib import Path

import pytest
from llm_tool_cli.paths.errors import PathResolutionFailed

from depmesh.discovery.paths import (
    normalize_path_pattern,
    resolve_project_path,
)
from depmesh.domain.entities import UntrustedPath


class TestResolveProjectPath:
    def test_root_resolution_failure_is_not_recovered(self, tmp_path: Path) -> None:
        root = tmp_path / "loop"
        root.symlink_to(root)

        failure = resolve_project_path("@/src/a.py", UntrustedPath(root)).unwrap_err()[0]

        assert isinstance(failure, PathResolutionFailed)
        assert failure.path == str(root)
        assert isinstance(failure.cause, (OSError, RuntimeError))

    def test_root_anchored_path(self, tmp_path: Path) -> None:
        assert (
            resolve_project_path("@/src/a.py", UntrustedPath(tmp_path)).unwrap()
            == (tmp_path / "src" / "a.py").resolve()
        )

    def test_classical_relative_path(self, tmp_path: Path) -> None:
        assert (
            resolve_project_path("./src/a.py", UntrustedPath(tmp_path)).unwrap()
            == (tmp_path / "src" / "a.py").resolve()
        )

    def test_absolute_path(self, tmp_path: Path) -> None:
        path = tmp_path / "src" / "a.py"

        assert resolve_project_path(str(path), UntrustedPath(tmp_path)).unwrap() == path.resolve()

    def test_relative_path_escaping_root(self, tmp_path: Path) -> None:
        assert resolve_project_path("../outside.py", UntrustedPath(tmp_path)).unwrap() is None

    def test_absolute_path_is_not_allowed(self, tmp_path: Path) -> None:
        path = tmp_path / "src" / "a.py"

        assert resolve_project_path(str(path), UntrustedPath(tmp_path), allow_absolute=False).unwrap() is None

    def test_project_root_is_not_a_project_file_path(self, tmp_path: Path) -> None:
        assert resolve_project_path(str(tmp_path), UntrustedPath(tmp_path)).unwrap() is None
        assert resolve_project_path(".", UntrustedPath(tmp_path)).unwrap() is None

    @pytest.mark.parametrize("value", ["@/../outside.py", "@/.", "@file", "@/a//b", "@/a/"])
    def test_invalid_root_anchored_path_is_not_resolved(self, tmp_path: Path, value: str) -> None:
        assert resolve_project_path(value, UntrustedPath(tmp_path)).unwrap() is None

    def test_root_anchored_symlink_outside_project_is_not_resolved(self, tmp_path: Path) -> None:
        (tmp_path / "outside").symlink_to(tmp_path.parent, target_is_directory=True)

        assert resolve_project_path("@/outside/a.py", UntrustedPath(tmp_path)).unwrap() is None

    @pytest.mark.parametrize("value", ["@/src/a.py", "src/a.py"])
    def test_resolution_failure_is_not_recovered(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        original = PermissionError("permission denied")
        resolve = Path.resolve

        def fail_resolution(path: Path) -> Path:
            if path == tmp_path / "src" / "a.py":
                raise original
            return resolve(path)

        monkeypatch.setattr(Path, "resolve", fail_resolution)

        failure = resolve_project_path(value, UntrustedPath(tmp_path)).unwrap_err()[0]

        assert isinstance(failure, PathResolutionFailed)
        assert failure.path == str(tmp_path / "src" / "a.py")
        assert failure.cause is original


class TestNormalizePathPattern:
    def test_root_anchored_pattern_preserves_glob_captures(self, tmp_path: Path) -> None:
        assert normalize_path_pattern("@/./src/{**package}/{*module}.py", UntrustedPath(tmp_path)).unwrap() == (
            "@/src/{**package}/{*module}.py"
        )

    def test_invalid_root_anchored_pattern_does_not_match(self, tmp_path: Path) -> None:
        assert normalize_path_pattern("@/../*.py", UntrustedPath(tmp_path)).unwrap() is None

    def test_resolution_failure_is_not_recovered(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        original = PermissionError("permission denied")
        resolve = Path.resolve

        def fail_resolution(path: Path) -> Path:
            if path == tmp_path / "src" / "*.py":
                raise original
            return resolve(path)

        monkeypatch.setattr(Path, "resolve", fail_resolution)

        failure = normalize_path_pattern("src/*.py", UntrustedPath(tmp_path)).unwrap_err()[0]

        assert isinstance(failure, PathResolutionFailed)
        assert failure.path == str(tmp_path / "src" / "*.py")
        assert failure.cause is original
