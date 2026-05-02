from __future__ import annotations

from pathlib import Path

from depmesh.discovery.matchers.entities import CaptureName
from depmesh.discovery.matchers.not_ import NotMatcher
from depmesh.domain.entities import ArtifactId


class TestNotMatcher:
    def test_captures__empty(self) -> None:
        matcher = NotMatcher.model_validate(
            {"type": "not", "item": {"type": "glob", "pattern": "./src/{*module}.py"}}
        )

        assert matcher.captures() == set()

    def test_match__success_when_item_does_not_match(self, tmp_path: Path) -> None:
        matcher = NotMatcher.model_validate(
            {"type": "not", "item": {"type": "paths", "paths": ["./src/excluded.py"]}}
        )

        assert matcher.match(ArtifactId("./src/included.py"), tmp_path) == {}

    def test_match__fails_when_item_matches(self, tmp_path: Path) -> None:
        matcher = NotMatcher.model_validate(
            {"type": "not", "item": {"type": "glob", "pattern": "./src/{*module}.py"}}
        )

        assert matcher.match(ArtifactId("./src/a.py"), tmp_path) is None

    def test_captures__does_not_expose_item_captures(self) -> None:
        matcher = NotMatcher.model_validate(
            {"type": "not", "item": {"type": "glob", "pattern": "./src/{*module}.py"}}
        )

        assert CaptureName("module") not in matcher.captures()
