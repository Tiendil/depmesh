from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.discovery.matchers.any import AnyMatcher
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.domain.entities import ArtifactId


class TestAnyMatcher:
    def test_captures__keeps_only_captures_provided_by_every_item(self) -> None:
        matcher = AnyMatcher.model_validate(
            {
                "type": "any",
                "items": [
                    {"type": "glob", "pattern": "./src/{*module}.py"},
                    {"type": "regex", "pattern": r"^\./lib/(?P<module>[a-z]+)\.py$"},
                    {"type": "regex", "pattern": r"^\./pkg/(?P<module>[a-z]+)/(?P<name>[a-z]+)\.py$"},
                ],
            }
        )

        assert matcher.captures() == {CaptureName("module")}

    def test_match__returns_first_matching_item_captures(self, tmp_path: Path) -> None:
        matcher = AnyMatcher.model_validate(
            {
                "type": "any",
                "items": [
                    {"type": "glob", "pattern": "./src/{*module}.py"},
                    {"type": "regex", "pattern": r"^\./lib/(?P<module>[a-z]+)\.py$"},
                ],
            }
        )

        assert matcher.match(ArtifactId("./lib/a.py"), tmp_path) == {"module": "a"}

    def test_match__no_item_matches(self, tmp_path: Path) -> None:
        matcher = AnyMatcher.model_validate(
            {"type": "any", "items": [{"type": "glob", "pattern": "./src/{*module}.py"}]}
        )

        assert matcher.match(ArtifactId("./docs/a.md"), tmp_path) is None

    def test_items__empty(self) -> None:
        with pytest.raises(ValueError):
            AnyMatcher.model_validate({"type": "any", "items": []})
