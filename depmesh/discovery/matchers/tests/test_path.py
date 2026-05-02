from __future__ import annotations

from pathlib import Path

from depmesh.discovery.matchers.path import PathMatcher
from depmesh.domain.entities import ArtifactId


class TestPathMatcher:
    def test_captures__empty(self) -> None:
        matcher = PathMatcher(type="path", path="./src/a.py")

        assert matcher.captures() == set()

    def test_match__success(self, tmp_path: Path) -> None:
        matcher = PathMatcher(type="path", path="./src/a.py")

        assert matcher.match(ArtifactId("./src/a.py"), tmp_path) == {}

    def test_match__no_match(self, tmp_path: Path) -> None:
        matcher = PathMatcher(type="path", path="./src/a.py")

        assert matcher.match(ArtifactId("./src/b.py"), tmp_path) is None
