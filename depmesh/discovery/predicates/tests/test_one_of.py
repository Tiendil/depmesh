from __future__ import annotations

from pathlib import Path

from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates.one_of import OneOfPredicate, OneOfPredicateConfig
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class TestOneOfPredicate:
    def test_variables__extracts_template_variables(self) -> None:
        predicate = OneOfPredicateConfig.model_validate({"type": "one_of", "artifacts": ["@/src/{module}.py"]})

        assert predicate.variables() == {CaptureName("module")}

    def test_captures__returns_empty_set(self) -> None:
        predicate = OneOfPredicateConfig.model_validate({"type": "one_of", "artifacts": ["@/src/a.py"]})

        assert predicate.captures() == set()

    def test_match__matches_normalized_artifact(self, tmp_path: Path) -> None:
        predicate = OneOfPredicate(
            OneOfPredicateConfig.model_validate({"type": "one_of", "artifacts": ["src/{module}.py"]})
        )

        assert predicate.match(ArtifactId("@/src/a.py"), ProjectRootPath(tmp_path), {"module": "a"}) == {}

    def test_match__returns_none_for_missing_artifact(self, tmp_path: Path) -> None:
        predicate = OneOfPredicate(
            OneOfPredicateConfig.model_validate({"type": "one_of", "artifacts": ["@/src/a.py"]})
        )

        assert predicate.match(ArtifactId("@/src/b.py"), ProjectRootPath(tmp_path)) is None
