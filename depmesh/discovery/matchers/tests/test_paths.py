from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.discovery.matchers.paths import PathsMatcher
from depmesh.domain.entities import ArtifactId


class TestPathsMatcher:
    def test_captures__empty(self) -> None:
        matcher = PathsMatcher(type="paths", paths=("./src/a.py",))

        assert matcher.captures() == set()

    def test_match__success(self, tmp_path: Path) -> None:
        matcher = PathsMatcher(type="paths", paths=("./src/a.py", "./src/b.py"))

        assert matcher.match(ArtifactId("./src/b.py"), tmp_path) == {}

    def test_match__no_match(self, tmp_path: Path) -> None:
        matcher = PathsMatcher(type="paths", paths=("./src/a.py", "./src/b.py"))

        assert matcher.match(ArtifactId("./src/c.py"), tmp_path) is None

    def test_paths__empty(self) -> None:
        with pytest.raises(ValueError):
            PathsMatcher.model_validate({"type": "paths", "paths": []})
