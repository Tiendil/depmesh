from __future__ import annotations

from pathlib import Path

from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates.regex import RegexPredicate, RegexPredicateConfig
from depmesh.domain.entities import ArtifactId


class TestRegexPredicate:
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

        assert predicate.match(ArtifactId("@/src/core/api.py"), tmp_path, {"package": "core"}) == {"module": "api"}

    def test_match__returns_none_for_missing_artifact(self, tmp_path: Path) -> None:
        predicate = RegexPredicate(RegexPredicateConfig(type="regex", pattern=r"^@/src/(?P<module>[a-z]+)\.py$"))

        assert predicate.match(ArtifactId("@/docs/a.md"), tmp_path) is None
