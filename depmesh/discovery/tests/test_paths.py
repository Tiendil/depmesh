from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.discovery import errors
from depmesh.discovery.paths import (
    normalize_existing_path,
    normalize_path,
    resolve_project_path,
    resolve_project_root,
)
from depmesh.domain.entities import UntrustedPath


class TestResolveProjectRoot:
    def test_resolves_root_path(self, tmp_path: Path) -> None:
        assert resolve_project_root(UntrustedPath(tmp_path / ".")).unwrap() == tmp_path.resolve()

    def test_resolution_failure_preserves_cause(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        original = PermissionError("permission denied")

        def fail_resolution(_path: Path) -> Path:
            raise original

        monkeypatch.setattr(Path, "resolve", fail_resolution)

        failure = resolve_project_root(UntrustedPath(tmp_path)).unwrap_err()[0]

        assert isinstance(failure, errors.PathResolutionFailed)
        assert failure.path == str(tmp_path)
        assert failure.cause is original


class TestResolveProjectPath:
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


class TestNormalizePath:
    def test_root_anchored_path_inside_root(self, tmp_path: Path) -> None:
        assert normalize_path("@/src/a.py", UntrustedPath(tmp_path)).unwrap() == "@/src/a.py"

    def test_classical_relative_path_inside_root(self, tmp_path: Path) -> None:
        assert normalize_path("./src/a.py", UntrustedPath(tmp_path)).unwrap() == "@/src/a.py"

    def test_root_anchored_path_with_dotdot(self, tmp_path: Path) -> None:
        assert normalize_path("@/src/../README.md", UntrustedPath(tmp_path)).unwrap() == "@/README.md"

    def test_path_relative_to_cwd(self, tmp_path: Path) -> None:
        cwd = tmp_path / "src"
        cwd.mkdir()

        assert normalize_path("a.py", UntrustedPath(tmp_path), cwd=UntrustedPath(cwd)).unwrap() == "@/src/a.py"

    def test_path_outside_root(self, tmp_path: Path) -> None:
        path = tmp_path.parent / "outside.py"

        failures = normalize_path(str(path), UntrustedPath(tmp_path)).unwrap_err()
        assert failures == [errors.InvalidProjectPath(path=str(path))]


class TestNormalizeExistingPath:
    def test_path_inside_root(self, tmp_path: Path) -> None:
        path = tmp_path / "src" / "a.py"
        path.parent.mkdir()
        path.write_text("", encoding="utf-8")

        assert normalize_existing_path(UntrustedPath(path), UntrustedPath(tmp_path)).unwrap() == "@/src/a.py"

    def test_path_outside_root(self, tmp_path: Path) -> None:
        path = tmp_path.parent / "outside.py"

        failures = normalize_existing_path(UntrustedPath(path), UntrustedPath(tmp_path)).unwrap_err()
        assert failures == [errors.InvalidProjectPath(path=str(path))]
