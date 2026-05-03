from __future__ import annotations

from pathlib import Path

from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.sources import DifferenceSource, FilterSource, IntersectionSource, UnionSource
from depmesh.domain.entities import ArtifactId, RelationId


def context(root: Path) -> EvaluationContext:
    return EvaluationContext(root=root, relation_id=RelationId("tests"), captures={})


class TestUnionSource:
    def test_evaluate__deduplicates_child_artifacts(self, tmp_path: Path) -> None:
        source = UnionSource.model_validate(
            {
                "type": "union",
                "items": [
                    {"type": "list", "artifacts": ["@/a.py"]},
                    {"type": "list", "artifacts": ["@/a.py", "@/b.py"]},
                ],
            }
        )

        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/a.py"), ArtifactId("@/b.py")]


class TestIntersectionSource:
    def test_evaluate__keeps_common_artifacts(self, tmp_path: Path) -> None:
        source = IntersectionSource.model_validate(
            {
                "type": "intersection",
                "items": [
                    {"type": "list", "artifacts": ["@/a.py", "@/b.py"]},
                    {"type": "list", "artifacts": ["@/b.py", "@/c.py"]},
                ],
            }
        )

        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/b.py")]


class TestDifferenceSource:
    def test_variables__combines_child_variables(self) -> None:
        source = DifferenceSource.model_validate(
            {
                "type": "difference",
                "include": {"type": "list", "artifacts": ["@/{kind}/a.py"]},
                "exclude": {"type": "list", "artifacts": ["@/{kind}/{name}.py"]},
            }
        )

        assert source.variables() == {CaptureName("kind"), CaptureName("name")}

    def test_evaluate__removes_excluded_artifacts(self, tmp_path: Path) -> None:
        source = DifferenceSource.model_validate(
            {
                "type": "difference",
                "include": {"type": "list", "artifacts": ["@/a.py", "@/b.py"]},
                "exclude": {"type": "list", "artifacts": ["@/b.py"]},
            }
        )

        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/a.py")]


class TestFilterSource:
    def test_evaluate__keeps_matching_artifacts(self, tmp_path: Path) -> None:
        source = FilterSource.model_validate(
            {
                "type": "filter",
                "source": {"type": "list", "artifacts": ["@/src/a.py", "@/docs/a.md"]},
                "predicate": {"type": "glob", "pattern": "@/src/{*module}.py"},
            }
        )

        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/src/a.py")]
