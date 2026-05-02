from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.discovery.matchers.all import AllMatcher
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.domain.entities import ArtifactId


class TestAllMatcher:
    def test_captures__combines_item_captures(self) -> None:
        matcher = AllMatcher.model_validate(
            {
                "type": "all",
                "items": [
                    {"type": "glob", "pattern": "./src/{*module}.py"},
                    {"type": "regex", "pattern": r"^\./src/[a-z]+\.py$"},
                ],
            }
        )

        assert matcher.captures() == {CaptureName("module")}

    def test_match__combines_captures_when_all_items_match(self, tmp_path: Path) -> None:
        matcher = AllMatcher.model_validate(
            {
                "type": "all",
                "items": [
                    {"type": "glob", "pattern": "./src/{*module}.py"},
                    {"type": "regex", "pattern": r"^\./src/(?P<module>[a-z]+)\.py$"},
                ],
            }
        )

        assert matcher.match(ArtifactId("./src/a.py"), tmp_path) == {"module": "a"}

    def test_match__fails_when_one_item_does_not_match(self, tmp_path: Path) -> None:
        matcher = AllMatcher.model_validate(
            {
                "type": "all",
                "items": [
                    {"type": "glob", "pattern": "./src/{*module}.py"},
                    {"type": "regex", "pattern": r"^\./lib/(?P<module>[a-z]+)\.py$"},
                ],
            }
        )

        assert matcher.match(ArtifactId("./src/a.py"), tmp_path) is None

    def test_match__fails_on_conflicting_capture_values(self, tmp_path: Path) -> None:
        matcher = AllMatcher.model_validate(
            {
                "type": "all",
                "items": [
                    {"type": "glob", "pattern": "./src/{*module}.py"},
                    {"type": "regex", "pattern": r"^\./(?P<module>src)/[a-z]+\.py$"},
                ],
            }
        )

        assert matcher.match(ArtifactId("./src/a.py"), tmp_path) is None

    def test_items__empty(self) -> None:
        with pytest.raises(ValueError):
            AllMatcher.model_validate({"type": "all", "items": []})
