from __future__ import annotations

import re
from pathlib import Path

import pytest

from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates.regex import RegexPredicate, RegexPredicateConfig
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class TestRegexPredicate:
    def test_match__invalid_substituted_pattern_raises(self, tmp_path: Path) -> None:
        predicate = RegexPredicate(RegexPredicateConfig(type="regex", pattern="^{pattern}$"))

        with pytest.raises(re.error):
            predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path), {"pattern": "["})

    def test_variables__extracts_template_variables(self) -> None:
        predicate = RegexPredicateConfig(type="regex", pattern=r"^@/src/{package}/(?P<module>[a-z]+)\.py$")

        assert predicate.variables() == {CaptureName("package")}

    def test_captures__extracts_named_groups(self) -> None:
        predicate = RegexPredicateConfig(type="regex", pattern=r"^@/src/(?P<module>[a-z]+)\.py$")

        assert predicate.captures() == {CaptureName("module")}

    def test_match__supports_templates_and_captures(self, tmp_path: Path) -> None:
        predicate = RegexPredicate(
            RegexPredicateConfig(type="regex", pattern=r"^@/src/{package}/(?P<module>[a-z]+)\.py$")
        )

        assert predicate.match(ArtifactId("@/src/core/api.py"), ProjectRootPath(tmp_path), {"package": "core"}) == {
            "module": "api"
        }

    def test_match__returns_none_for_missing_artifact(self, tmp_path: Path) -> None:
        predicate = RegexPredicate(RegexPredicateConfig(type="regex", pattern=r"^@/src/(?P<module>[a-z]+)\.py$"))

        assert predicate.match(ArtifactId("@/docs/a.md"), ProjectRootPath(tmp_path)) is None
