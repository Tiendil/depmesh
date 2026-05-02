from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.discovery.matchers.regex import RegexMatcher
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.domain.entities import ArtifactId


class TestRegexMatcher:
    def test_captures__extracts_named_groups(self) -> None:
        matcher = RegexMatcher(type="regex", pattern=r"^\./src/(?P<module>[a-z]+)\.py$")

        assert matcher.captures() == {CaptureName("module")}

    def test_captures__invalid_regex(self) -> None:
        matcher = RegexMatcher(type="regex", pattern="[")

        with pytest.raises(ValueError, match="invalid regex matcher"):
            matcher.captures()

    def test_match__success(self, tmp_path: Path) -> None:
        matcher = RegexMatcher(type="regex", pattern=r"^\./src/(?P<module>[a-z]+)\.py$")

        assert matcher.match(ArtifactId("./src/a.py"), tmp_path) == {"module": "a"}

    def test_match__no_match(self, tmp_path: Path) -> None:
        matcher = RegexMatcher(type="regex", pattern=r"^\./src/(?P<module>[a-z]+)\.py$")

        assert matcher.match(ArtifactId("./docs/a.md"), tmp_path) is None
