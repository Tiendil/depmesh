from __future__ import annotations

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Dependency
from depmesh.protocol.renderers.human import HumanRendered


class TestHumanRendered:
    def test_render_query__complete_data(self) -> None:
        result = QueryResult(
            dependencies=(
                Dependency(relation="tests", dependency="./tests/test_b.py"),
                Dependency(relation="specs", dependency="./specs/a.md"),
                Dependency(relation="tests", dependency="./tests/test_a.py"),
            )
        )

        assert HumanRendered().render_query(
            result,
            ["first warning", "second warning"],
            relations=(),
        ) == (
            "specs:\n"
            "  ./specs/a.md\n\n"
            "tests:\n"
            "  ./tests/test_a.py\n"
            "  ./tests/test_b.py\n\n"
            "warnings:\n"
            "  first warning\n"
            "  second warning\n"
        )

    def test_render_query__groups_dependencies_and_warnings(self) -> None:
        result = QueryResult(dependencies=(Dependency(relation="tests", dependency="./tests/test_a.py"),))

        assert HumanRendered().render_query(result, ["warning"], relations=()) == (
            "tests:\n"
            "  ./tests/test_a.py\n\n"
            "warnings:\n"
            "  warning\n"
        )
