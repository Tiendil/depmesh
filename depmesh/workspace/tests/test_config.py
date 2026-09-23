from __future__ import annotations

from pathlib import Path

from depmesh.discovery.query import query_dependencies
from depmesh.domain.entities import ArtifactId, Dependency, ProjectRootPath, Relation, RelationDescription, RelationId
from depmesh.workspace import Config, construct_workspace


class TestConstructWorkspace:
    def test_converts_relations_without_loading_configuration(self, tmp_path: Path) -> None:
        config = Config.model_validate(
            {"relations": [{"id": "tests", "description": "Related tests"}, {"id": "imports"}]}
        )

        workspace = construct_workspace(config, root=tmp_path)

        assert workspace.root == tmp_path
        assert workspace.relations == (
            Relation(id=RelationId("tests"), description=RelationDescription("Related tests")),
            Relation(id=RelationId("imports")),
        )

    def test_compiles_rules_into_usable_runtime_sources(self, tmp_path: Path) -> None:
        config = Config.model_validate(
            {
                "relations": [{"id": "tests"}],
                "rules": [
                    {
                        "relation": "tests",
                        "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                        "output": {"type": "list", "artifacts": ["@/tests/test_{module}.py"]},
                    }
                ],
            }
        )

        workspace = construct_workspace(config, root=tmp_path)
        result = query_dependencies(
            ProjectRootPath(workspace.root),
            workspace.relations_by_id,
            workspace.rules,
            ArtifactId("@/src/example.py"),
            relation_ids={RelationId("tests")},
        )

        assert result.dependencies == (
            Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/test_example.py")),
        )

    def test_empty_config(self, tmp_path: Path) -> None:
        workspace = construct_workspace(Config(), root=tmp_path)

        assert not workspace.relations
        assert not workspace.rules
