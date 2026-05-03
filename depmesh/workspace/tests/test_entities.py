from __future__ import annotations

from pathlib import Path

from depmesh.domain.entities import Relation, RelationDescription, RelationId
from depmesh.workspace.entities import RelationConfig, Workspace


class TestRelationConfig:
    def test_to_relation__returns_domain_relation(self) -> None:
        relation = RelationConfig.model_validate(
            {
                "id": "tests",
                "description": "Tests related to the input artifacts.",
            }
        )

        assert relation.to_relation() == Relation(
            id=RelationId("tests"),
            description=RelationDescription("Tests related to the input artifacts."),
        )


class TestWorkspace:
    def test_relations_by_id__indexes_relations_by_id(self, tmp_path: Path) -> None:
        relation = Relation(id=RelationId("tests"))
        workspace = Workspace(root=tmp_path, relations=(relation,))

        assert workspace.relations_by_id == {RelationId("tests"): relation}
