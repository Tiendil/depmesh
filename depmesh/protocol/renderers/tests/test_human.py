from __future__ import annotations

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import ArtifactId, Dependency, Relation, RelationDescription, RelationId
from depmesh.protocol.renderers.human import HumanRendered


def dependency(relation: str, artifact: str) -> Dependency:
    return Dependency(relation=RelationId(relation), dependency=ArtifactId(artifact))


def relation(id_: str, description: str | None = None) -> Relation:
    return Relation(
        id=RelationId(id_),
        description=RelationDescription(description) if description is not None else None,
    )


class TestHumanRendered:
    def test_render_query__complete_data(self) -> None:
        result = QueryResult(
            dependencies=(
                dependency("tests", "@/tests/test_b.py"),
                dependency("specs", "@/specs/a.md"),
                dependency("tests", "@/tests/test_a.py"),
            )
        )

        assert HumanRendered().render_query(
            result,
            ["first warning", "second warning"],
            relations=(),
        ) == (
            "specs:\n"
            "  @/specs/a.md\n\n"
            "tests:\n"
            "  @/tests/test_a.py\n"
            "  @/tests/test_b.py\n\n"
            "warnings:\n"
            "  first warning\n"
            "  second warning\n"
        )

    def test_render_query__groups_dependencies_and_warnings(self) -> None:
        result = QueryResult(dependencies=(dependency("tests", "@/tests/test_a.py"),))

        assert HumanRendered().render_query(result, ["warning"], relations=()) == (
            "tests:\n  @/tests/test_a.py\n\nwarnings:\n  warning\n"
        )

    def test_render_relations__orders_relations_and_descriptions(self) -> None:
        assert (
            HumanRendered().render_relations(
                (
                    relation("tests", "Tests related to input artifacts."),
                    relation("imports"),
                )
            )
            == "imports:\n\ntests:\n  Tests related to input artifacts.\n"
        )
