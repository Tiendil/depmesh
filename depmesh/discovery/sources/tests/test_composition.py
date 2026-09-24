from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.discovery import errors
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.sources import (
    DifferenceSourceConfig,
    FilterSourceConfig,
    IntersectionSourceConfig,
    UnionSourceConfig,
    compile_source,
)
from depmesh.discovery.sources.entities import ArtifactSourceConfig
from depmesh.domain.entities import ArtifactId, ProjectRootPath, RelationId


def context(root: Path) -> EvaluationContext:
    return EvaluationContext(root=ProjectRootPath(root), relation_id=RelationId("tests"), captures={})


class TestUnionSource:
    @pytest.mark.parametrize("source_type", ["union", "intersection", "difference", "filter"])
    def test_evaluate__propagates_child_failure(self, tmp_path: Path, source_type: str) -> None:
        invalid = {"type": "list", "artifacts": ["../outside.py"]}
        valid = {"type": "list", "artifacts": ["@/a.py"]}
        config: ArtifactSourceConfig
        if source_type == "union":
            config = UnionSourceConfig.model_validate({"type": source_type, "items": [valid, invalid]})
        elif source_type == "intersection":
            config = IntersectionSourceConfig.model_validate({"type": source_type, "items": [valid, invalid]})
        elif source_type == "difference":
            config = DifferenceSourceConfig.model_validate({"type": source_type, "include": valid, "exclude": invalid})
        else:
            config = FilterSourceConfig.model_validate(
                {"type": source_type, "source": invalid, "predicate": {"type": "glob", "pattern": "@/**"}}
            )
        source = compile_source(config)

        assert source.evaluate(context(tmp_path)).unwrap_err() == [errors.InvalidProjectPath(path="../outside.py")]

    def test_evaluate__deduplicates_child_artifacts(self, tmp_path: Path) -> None:
        source = compile_source(
            UnionSourceConfig.model_validate(
                {
                    "type": "union",
                    "items": [
                        {"type": "list", "artifacts": ["@/a.py"]},
                        {"type": "list", "artifacts": ["@/a.py", "@/b.py"]},
                    ],
                }
            )
        )

        assert source.evaluate(context(tmp_path)).unwrap() == [ArtifactId("@/a.py"), ArtifactId("@/b.py")]


class TestIntersectionSource:
    def test_evaluate__keeps_common_artifacts(self, tmp_path: Path) -> None:
        source = compile_source(
            IntersectionSourceConfig.model_validate(
                {
                    "type": "intersection",
                    "items": [
                        {"type": "list", "artifacts": ["@/a.py", "@/b.py"]},
                        {"type": "list", "artifacts": ["@/b.py", "@/c.py"]},
                    ],
                }
            )
        )

        assert source.evaluate(context(tmp_path)).unwrap() == [ArtifactId("@/b.py")]


class TestDifferenceSource:
    def test_variables__combines_child_variables(self) -> None:
        source = DifferenceSourceConfig.model_validate(
            {
                "type": "difference",
                "include": {"type": "list", "artifacts": ["@/{kind}/a.py"]},
                "exclude": {"type": "list", "artifacts": ["@/{kind}/{name}.py"]},
            }
        )

        assert source.variables() == {CaptureName("kind"), CaptureName("name")}

    def test_evaluate__removes_excluded_artifacts(self, tmp_path: Path) -> None:
        source = compile_source(
            DifferenceSourceConfig.model_validate(
                {
                    "type": "difference",
                    "include": {"type": "list", "artifacts": ["@/a.py", "@/b.py"]},
                    "exclude": {"type": "list", "artifacts": ["@/b.py"]},
                }
            )
        )

        assert source.evaluate(context(tmp_path)).unwrap() == [ArtifactId("@/a.py")]


class TestFilterSource:
    def test_evaluate__propagates_predicate_path_failure(self, tmp_path: Path) -> None:
        source = compile_source(
            FilterSourceConfig.model_validate(
                {
                    "type": "filter",
                    "source": {"type": "list", "artifacts": ["@/a.py"]},
                    "predicate": {"type": "one_of", "artifacts": ["../outside.py"]},
                }
            )
        )

        assert source.evaluate(context(tmp_path)).unwrap_err() == [errors.InvalidProjectPath(path="../outside.py")]

    def test_evaluate__keeps_matching_artifacts(self, tmp_path: Path) -> None:
        source = compile_source(
            FilterSourceConfig.model_validate(
                {
                    "type": "filter",
                    "source": {"type": "list", "artifacts": ["@/src/a.py", "@/docs/a.md"]},
                    "predicate": {"type": "glob", "pattern": "@/src/{*module}.py"},
                }
            )
        )

        assert source.evaluate(context(tmp_path)).unwrap() == [ArtifactId("@/src/a.py")]
