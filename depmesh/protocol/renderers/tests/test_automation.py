from __future__ import annotations

import json

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import ArtifactId, Dependency, Relation, RelationDescription, RelationId
from depmesh.protocol.renderers.automation import AutomationRendered, to_jsonl
from depmesh.skills.entities import SkillDocument


def dependency(relation: str, artifact: str) -> Dependency:
    return Dependency(relation=RelationId(relation), dependency=ArtifactId(artifact))


def relation(id_: str, description: str | None = None) -> Relation:
    return Relation(
        id=RelationId(id_),
        description=RelationDescription(description) if description is not None else None,
    )


class TestToJsonl:
    def test_serializes_record_with_stable_options_and_newline(self) -> None:
        assert to_jsonl({"type": "warning", "message": "привет"}) == ('{"message": "привет", "type": "warning"}\n')


class TestAutomationRendered:
    def test_render_query__complete_data(self) -> None:
        result = QueryResult(
            dependencies=(
                dependency("specs", "@/specs/a.md"),
                dependency("tests", "@/tests/test_a.py"),
                dependency("tests", "@/tests/test_b.py"),
            )
        )

        assert AutomationRendered().render_query(
            result,
            ["first warning", "second warning"],
            relations=(),
        ) == (
            '{"dependency": "@/specs/a.md", "relation": "specs", "type": "dependency"}\n'
            '{"dependency": "@/tests/test_a.py", "relation": "tests", "type": "dependency"}\n'
            '{"dependency": "@/tests/test_b.py", "relation": "tests", "type": "dependency"}\n'
            '{"message": "first warning", "type": "warning"}\n'
            '{"message": "second warning", "type": "warning"}\n'
        )

    def test_render_query__returns_json_lines_records(self) -> None:
        result = QueryResult(dependencies=(dependency("tests", "@/tests/test_a.py"),))

        records = [
            json.loads(line)
            for line in AutomationRendered().render_query(result, ["warning"], relations=()).splitlines()
        ]

        assert records == [
            {"type": "dependency", "relation": "tests", "dependency": "@/tests/test_a.py"},
            {"type": "warning", "message": "warning"},
        ]

    def test_render_skill__returns_json_record(self) -> None:
        record = json.loads(AutomationRendered().render_skill())

        assert record["type"] == "skill"
        assert record["document"] == "usage"

    def test_render_skill__returns_selected_document(self) -> None:
        record = json.loads(AutomationRendered().render_skill(SkillDocument.initialization))

        assert record["document"] == "initialization"
        assert record["text"].startswith("# `depmesh` Initialization\n")

    def test_render_relations__returns_json_lines_records(self) -> None:
        records = [
            json.loads(line)
            for line in AutomationRendered()
            .render_relations(
                (
                    relation("tests", "Tests related to input artifacts."),
                    relation("imports"),
                )
            )
            .splitlines()
        ]

        assert records == [
            {"type": "relation", "id": "imports"},
            {"type": "relation", "id": "tests", "description": "Tests related to input artifacts."},
        ]

    def test_render_error__returns_json_record(self) -> None:
        record = json.loads(AutomationRendered().render_error({"type": "error", "code": "x", "message": "failed"}))

        assert record == {"type": "error", "code": "x", "message": "failed"}
