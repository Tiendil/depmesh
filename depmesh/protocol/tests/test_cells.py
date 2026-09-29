import pytest
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.output_cells import AutomationOutputCell, HumanOutputCell, LLMOutputCell
from llm_tool_cli.protocol.output_cells.base import OutputCell

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import ArtifactId, Dependency, Relation, RelationDescription, RelationId
from depmesh.protocol.cells import DependenciesCell, relation_cells


def dependency(relation: str, artifact: str) -> Dependency:
    return Dependency(relation=RelationId(relation), dependency=ArtifactId(artifact))


def relation(id_: str, description: str | None = None) -> Relation:
    return Relation(
        id=RelationId(id_),
        description=RelationDescription(description) if description is not None else None,
    )


def payloads(cells: list[OutputCell]) -> list[dict[str, object]]:
    return [cell.model_dump(exclude={"id"}) for cell in cells]


class TestDependenciesCell:
    @pytest.mark.parametrize("protocol", list(Protocol))
    def test_render__repeated_calls_preserve_payloads_and_input(self, protocol: Protocol) -> None:
        cell = DependenciesCell(
            result=QueryResult(dependencies=(dependency("tests", "@/a.py"),)),
            relations=(relation("tests", "Tests for café."),),
            warnings=["first", "second"],
        )
        original = cell.model_dump()

        first = cell.render(protocol)
        cell.render(Protocol.automation)
        second = cell.render(protocol)

        assert payloads(first) == payloads(second)
        assert {output.id for output in first}.isdisjoint(output.id for output in second)
        assert cell.model_dump() == original

    @pytest.mark.parametrize("protocol", [Protocol.human, Protocol.llm])
    def test_render__grouped_markdown_is_sorted_and_deduplicated(self, protocol: Protocol) -> None:
        result = QueryResult(
            dependencies=(
                dependency("tests", "@/tests/b.py"),
                dependency("specs", "@/specs/a.md"),
                dependency("tests", "@/tests/a.py"),
                dependency("tests", "@/tests/a.py"),
            )
        )

        cells = DependenciesCell(result=result, warnings=[], relations=(relation("tests", "Tests for café."),)).render(
            protocol
        )

        assert payloads(cells) == [
            {
                "kind": "dependencies",
                "media_type": "text/markdown",
                "content": "- @/specs/a.md",
                "meta": {"type": "dependencies", "relation": "specs"},
            },
            {
                "kind": "dependencies",
                "media_type": "text/markdown",
                "content": "Tests for café.\n\n- @/tests/a.py\n- @/tests/b.py",
                "meta": {"type": "dependencies", "relation": "tests"},
            },
        ]

    def test_render__automation_keeps_individual_structured_dependencies(self) -> None:
        result = QueryResult(
            dependencies=(
                dependency("tests", "@/b.py"),
                dependency("imports", "@/a.py"),
                dependency("tests", "@/a.py"),
                dependency("tests", "@/a.py"),
            )
        )

        cells = DependenciesCell(result=result, warnings=[], relations=()).render(Protocol.automation)

        assert payloads(cells) == [
            {
                "kind": "dependency",
                "media_type": None,
                "content": None,
                "meta": {"type": "dependency", "relation": "imports", "dependency": "@/a.py"},
            },
            {
                "kind": "dependency",
                "media_type": None,
                "content": None,
                "meta": {"type": "dependency", "relation": "tests", "dependency": "@/a.py"},
            },
            {
                "kind": "dependency",
                "media_type": None,
                "content": None,
                "meta": {"type": "dependency", "relation": "tests", "dependency": "@/b.py"},
            },
        ]

    @pytest.mark.parametrize("protocol", list(Protocol))
    def test_render__empty_result(self, protocol: Protocol) -> None:
        assert DependenciesCell(result=QueryResult(dependencies=()), warnings=[], relations=()).render(protocol) == []

    @pytest.mark.parametrize("protocol", list(Protocol))
    @pytest.mark.parametrize("with_dependencies", [False, True])
    def test_render__warnings_follow_results_in_insertion_order(
        self, protocol: Protocol, with_dependencies: bool
    ) -> None:
        result = QueryResult(dependencies=(dependency("tests", "@/a.py"),) if with_dependencies else ())

        cells = DependenciesCell(result=result, warnings=["first", "café\nsecond"], relations=()).render(protocol)

        assert len(cells) == 2 + int(with_dependencies)
        assert payloads(cells[-2:]) == [
            {"kind": "warning", "media_type": None, "content": None, "meta": {"type": "warning", "message": "first"}},
            {
                "kind": "warning",
                "media_type": None,
                "content": None,
                "meta": {"type": "warning", "message": "café\nsecond"},
            },
        ]

    @pytest.mark.parametrize("description", [None, "", "Artifacts tested by this artifact."])
    def test_render__optional_description(self, description: str | None) -> None:
        cells = DependenciesCell(
            result=QueryResult(dependencies=(dependency("tested_by", "@/a.py"),)),
            warnings=[],
            relations=(relation("tested_by", description),),
        ).render(Protocol.llm)

        prefix = f"{description}\n\n" if description else ""
        assert cells[0].content == prefix + "- @/a.py"

    @pytest.mark.parametrize(
        ("protocol", "cell_type"),
        [
            (Protocol.human, HumanOutputCell),
            (Protocol.llm, LLMOutputCell),
            (Protocol.automation, AutomationOutputCell),
        ],
    )
    def test_render__results_and_warnings_use_selected_output_type(
        self, protocol: Protocol, cell_type: type[OutputCell]
    ) -> None:
        cell = DependenciesCell(
            result=QueryResult(dependencies=(dependency("tests", "@/a.py"),)),
            relations=(),
            warnings=["warning"],
        )

        outputs = cell.render(protocol)

        assert len(outputs) == 2
        assert all(isinstance(output, cell_type) for output in outputs)


class TestRelationCells:
    def test_sorted_metadata_preserves_description_and_relation_identity(self) -> None:
        cells = relation_cells((relation("tests", "Tests for café."), relation("imports")))

        assert [cell.model_dump() for cell in cells] == [
            {
                "kind": "relation",
                "media_type": None,
                "content": None,
                "meta": {"type": "relation", "relation": "imports"},
            },
            {
                "kind": "relation",
                "media_type": None,
                "content": None,
                "meta": {"type": "relation", "relation": "tests", "description": "Tests for café."},
            },
        ]

    def test_empty(self) -> None:
        assert relation_cells(()) == []

    def test_empty_description_is_preserved(self) -> None:
        assert relation_cells((relation("tests", ""),))[0].meta["description"] == ""
