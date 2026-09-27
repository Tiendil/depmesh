from __future__ import annotations

from pathlib import Path

import pytest
from llm_tool_cli.paths.errors import PathResolutionFailed

from depmesh.discovery.paths import normalize_path_pattern
from depmesh.domain.entities import UntrustedPath


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
