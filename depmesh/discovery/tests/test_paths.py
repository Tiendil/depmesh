from __future__ import annotations

from pathlib import Path

from depmesh.discovery.paths import normalize_existing_path, normalize_path, resolve_project_path


class TestResolveProjectPath:
    def test_relative_path(self, tmp_path: Path) -> None:
        assert resolve_project_path("./src/a.py", tmp_path) == (tmp_path / "src" / "a.py").resolve()

    def test_absolute_path(self, tmp_path: Path) -> None:
        path = tmp_path / "src" / "a.py"

        assert resolve_project_path(str(path), tmp_path) == path.resolve()

    def test_relative_path_escaping_root(self, tmp_path: Path) -> None:
        assert resolve_project_path("../outside.py", tmp_path) is None

    def test_absolute_path_is_not_allowed(self, tmp_path: Path) -> None:
        path = tmp_path / "src" / "a.py"

        assert resolve_project_path(str(path), tmp_path, allow_absolute=False) is None


class TestNormalizePath:
    def test_path_inside_root(self, tmp_path: Path) -> None:
        assert normalize_path("./src/a.py", tmp_path) == "./src/a.py"

    def test_path_relative_to_cwd(self, tmp_path: Path) -> None:
        cwd = tmp_path / "src"
        cwd.mkdir()

        assert normalize_path("a.py", tmp_path, cwd=cwd) == "./src/a.py"

    def test_path_outside_root(self, tmp_path: Path) -> None:
        path = tmp_path.parent / "outside.py"

        assert normalize_path(str(path), tmp_path) == path.resolve().as_posix()


class TestNormalizeExistingPath:
    def test_path_inside_root(self, tmp_path: Path) -> None:
        path = tmp_path / "src" / "a.py"
        path.parent.mkdir()
        path.write_text("", encoding="utf-8")

        assert normalize_existing_path(path, tmp_path) == "./src/a.py"

    def test_path_outside_root(self, tmp_path: Path) -> None:
        path = tmp_path.parent / "outside.py"

        assert normalize_existing_path(path, tmp_path) == path.resolve().as_posix()
