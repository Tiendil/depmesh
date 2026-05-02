from __future__ import annotations

from pathlib import Path

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Dependency, Relation
from depmesh.protocol.renderers.llm import LLMRendered
from depmesh.workspace.config import parse_config


class TestLLMRendered:
    def test_render_query__complete_data(self) -> None:
        result = QueryResult(
            dependencies=(
                Dependency(relation="tests", dependency="./tests/test_b.py"),
                Dependency(relation="specs", dependency="./specs/a.md"),
                Dependency(relation="tests", dependency="./tests/test_a.py"),
            )
        )
        relations = (
            Relation(id="tests", reverse_id="tested_by", description="Tests related to the input artifacts."),
            Relation(id="specs", reverse_id="specified_by"),
        )

        assert LLMRendered().render_query(
            result,
            ["first warning", "second warning"],
            relations=relations,
        ) == (
            "## specs\n\n"
            "- ./specs/a.md\n\n"
            "## tests\n\n"
            "Tests related to the input artifacts.\n\n"
            "- ./tests/test_a.py\n"
            "- ./tests/test_b.py\n\n"
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
                        "reverse_id": "tested_by",
                        "description": "Tests related to the input artifacts.",
                    }
                ]
            },
            config_path=tmp_path / "depmesh.toml",
        )
        result = QueryResult(dependencies=(Dependency(relation="tests", dependency="./tests/test_a.py"),))

        assert LLMRendered().render_query(result, [], relations=config.relations) == (
            "## tests\n\n"
            "Tests related to the input artifacts.\n\n"
            "- ./tests/test_a.py\n"
        )

    def test_render_query__includes_reverse_relation_description(self) -> None:
        relations = (
            Relation(
                id="tests",
                reverse_id="tested_by",
                reverse_description="Artifacts tested by the input artifacts.",
            ),
        )
        result = QueryResult(dependencies=(Dependency(relation="tested_by", dependency="./src/a.py"),))

        assert LLMRendered().render_query(result, [], relations=relations) == (
            "## tested_by\n\n"
            "Artifacts tested by the input artifacts.\n\n"
            "- ./src/a.py\n"
        )
