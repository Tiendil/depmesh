from __future__ import annotations

from pathlib import Path

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import ArtifactId, Dependency, Relation, RelationDescription, RelationId
from depmesh.protocol.renderers.llm import LLMRendered
from depmesh.workspace.config import parse_config


def dependency(relation: str, artifact: str) -> Dependency:
    return Dependency(relation=RelationId(relation), dependency=ArtifactId(artifact))


def relation(id_: str, description: str | None = None) -> Relation:
    return Relation(
        id=RelationId(id_),
        description=RelationDescription(description) if description is not None else None,
    )


class TestLLMRendered:
    def test_render_query__complete_data(self) -> None:
        result = QueryResult(
            dependencies=(
                dependency("tests", "@/tests/test_b.py"),
                dependency("specs", "@/specs/a.md"),
                dependency("tests", "@/tests/test_a.py"),
            )
        )
        relations = (
            relation(
                "tests",
                "Tests related to the input artifacts.",
            ),
            relation("specs"),
        )

        assert LLMRendered().render_query(
            result,
            ["first warning", "second warning"],
            relations=relations,
        ) == (
            "## specs\n\n"
            "- @/specs/a.md\n\n"
            "## tests\n\n"
            "Tests related to the input artifacts.\n\n"
            "- @/tests/test_a.py\n"
            "- @/tests/test_b.py\n\n"
            "## warnings\n\n"
            "- first warning\n"
            "- second warning\n"
        )

    def test_render_query__includes_relation_description(self, tmp_path: Path) -> None:
        config = parse_config(
            {
                "relations": [
                    {
                        "id": "tests",
                        "description": "Tests related to the input artifacts.",
                    }
                ]
            },
            config_path=tmp_path / "depmesh.toml",
        )
        result = QueryResult(dependencies=(dependency("tests", "@/tests/test_a.py"),))

        assert LLMRendered().render_query(result, [], relations=config.relations) == (
            "## tests\n\nTests related to the input artifacts.\n\n- @/tests/test_a.py\n"
        )

    def test_render_query__includes_reverse_relation_description_when_configured(self) -> None:
        relations = (
            relation(
                "tested_by",
                "Artifacts tested by the input artifacts.",
            ),
        )
        result = QueryResult(dependencies=(dependency("tested_by", "@/src/a.py"),))

        assert LLMRendered().render_query(result, [], relations=relations) == (
            "## tested_by\n\nArtifacts tested by the input artifacts.\n\n- @/src/a.py\n"
        )

    def test_render_relations__orders_relations_and_descriptions(self) -> None:
        assert (
            LLMRendered().render_relations(
                (
                    relation("tests", "Tests related to input artifacts."),
                    relation("imports"),
                )
            )
            == "## imports\n\n## tests\n\nTests related to input artifacts.\n"
        )
