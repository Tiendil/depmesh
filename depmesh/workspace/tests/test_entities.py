from __future__ import annotations

from pathlib import Path

from depmesh.domain.entities import Relation
from depmesh.workspace.entities import RelationConfig, Workspace


class TestRelationConfig:
    def test_to_relation__returns_domain_relation(self) -> None:
        relation = RelationConfig(
            forward_id="tests",
            backward_id="tested_by",
            forward_description="Tests related to the input artifacts.",
            backward_description="Artifacts tested by the input artifacts.",
        )

        assert relation.to_relation() == Relation(
            forward_id="tests",
            backward_id="tested_by",
            forward_description="Tests related to the input artifacts.",
            backward_description="Artifacts tested by the input artifacts.",
        )


class TestWorkspace:
    def test_relations_by_forward_id__indexes_relations_by_forward_id(self, tmp_path: Path) -> None:
        relation = Relation(forward_id="tests", backward_id="tested_by")
        workspace = Workspace(root=tmp_path, relations=(relation,))

        assert workspace.relations_by_forward_id == {"tests": relation}

    def test_relations_by_backward_id__indexes_relations_by_backward_id(self, tmp_path: Path) -> None:
        relation = Relation(forward_id="tests", backward_id="tested_by")
        workspace = Workspace(root=tmp_path, relations=(relation,))

        assert workspace.relations_by_backward_id == {"tested_by": relation}

    def test_relations_by_id__indexes_all_relation_ids(self, tmp_path: Path) -> None:
        relation = Relation(forward_id="tests", backward_id="tested_by")
        workspace = Workspace(root=tmp_path, relations=(relation,))

        assert workspace.relations_by_id == {"tests": relation, "tested_by": relation}
