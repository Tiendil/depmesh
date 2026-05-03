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
        assert resolve_project_root(UntrustedPath(tmp_path / ".")) == tmp_path.resolve()


class TestResolveProjectPath:
    def test_root_anchored_path(self, tmp_path: Path) -> None:
        assert resolve_project_path("@/src/a.py", UntrustedPath(tmp_path)) == (tmp_path / "src" / "a.py").resolve()

    def test_classical_relative_path(self, tmp_path: Path) -> None:
        assert resolve_project_path("./src/a.py", UntrustedPath(tmp_path)) == (tmp_path / "src" / "a.py").resolve()

    def test_absolute_path(self, tmp_path: Path) -> None:
        path = tmp_path / "src" / "a.py"

        assert resolve_project_path(str(path), UntrustedPath(tmp_path)) == path.resolve()

    def test_relative_path_escaping_root(self, tmp_path: Path) -> None:
        assert resolve_project_path("../outside.py", UntrustedPath(tmp_path)) is None

    def test_absolute_path_is_not_allowed(self, tmp_path: Path) -> None:
        path = tmp_path / "src" / "a.py"

        assert resolve_project_path(str(path), UntrustedPath(tmp_path), allow_absolute=False) is None

    def test_project_root_is_not_a_project_file_path(self, tmp_path: Path) -> None:
        assert resolve_project_path(str(tmp_path), UntrustedPath(tmp_path)) is None
        assert resolve_project_path(".", UntrustedPath(tmp_path)) is None


class TestNormalizePath:
    def test_root_anchored_path_inside_root(self, tmp_path: Path) -> None:
        assert normalize_path("@/src/a.py", UntrustedPath(tmp_path)) == "@/src/a.py"

    def test_classical_relative_path_inside_root(self, tmp_path: Path) -> None:
        assert normalize_path("./src/a.py", UntrustedPath(tmp_path)) == "@/src/a.py"

    def test_root_anchored_path_with_dotdot(self, tmp_path: Path) -> None:
        assert normalize_path("@/src/../README.md", UntrustedPath(tmp_path)) == "@/README.md"

    def test_path_relative_to_cwd(self, tmp_path: Path) -> None:
        cwd = tmp_path / "src"
        cwd.mkdir()

        assert normalize_path("a.py", UntrustedPath(tmp_path), cwd=UntrustedPath(cwd)) == "@/src/a.py"

    def test_path_outside_root(self, tmp_path: Path) -> None:
        path = tmp_path.parent / "outside.py"

        with pytest.raises(errors.InvalidProjectPath):
            normalize_path(str(path), UntrustedPath(tmp_path))


class TestNormalizeExistingPath:
    def test_path_inside_root(self, tmp_path: Path) -> None:
        path = tmp_path / "src" / "a.py"
        path.parent.mkdir()
        path.write_text("", encoding="utf-8")

        assert normalize_existing_path(UntrustedPath(path), UntrustedPath(tmp_path)) == "@/src/a.py"

    def test_path_outside_root(self, tmp_path: Path) -> None:
        path = tmp_path.parent / "outside.py"

        with pytest.raises(errors.InvalidProjectPath):
            normalize_existing_path(UntrustedPath(path), UntrustedPath(tmp_path))
