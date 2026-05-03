from __future__ import annotations

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import ArtifactId, Dependency, RelationId


class TestQueryResult:
    def test_grouped__deduplicates_and_orders_dependencies(self) -> None:
        result = QueryResult(
            dependencies=(
                Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/test_b.py")),
                Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/test_a.py")),
                Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/test_a.py")),
            )
        )

        assert result.grouped() == {
            RelationId("tests"): [ArtifactId("@/tests/test_a.py"), ArtifactId("@/tests/test_b.py")]
        }
