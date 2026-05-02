from __future__ import annotations

import json

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Dependency
from depmesh.protocol.renderers.automation import AutomationRendered, to_jsonl


class TestToJsonl:
    def test_serializes_record_with_stable_options_and_newline(self) -> None:
        assert to_jsonl({"type": "warning", "message": "привет"}) == (
            '{"message": "привет", "type": "warning"}\n'
        )


class TestAutomationRendered:
    def test_render_query__complete_data(self) -> None:
        result = QueryResult(
            dependencies=(
                Dependency(relation="specs", dependency="./specs/a.md"),
                Dependency(relation="tests", dependency="./tests/test_a.py"),
                Dependency(relation="tests", dependency="./tests/test_b.py"),
            )
        )

        assert AutomationRendered().render_query(
            result,
            ["first warning", "second warning"],
            relations=(),
        ) == (
            '{"dependency": "./specs/a.md", "relation": "specs", "type": "dependency"}\n'
            '{"dependency": "./tests/test_a.py", "relation": "tests", "type": "dependency"}\n'
            '{"dependency": "./tests/test_b.py", "relation": "tests", "type": "dependency"}\n'
            '{"message": "first warning", "type": "warning"}\n'
            '{"message": "second warning", "type": "warning"}\n'
        )

    def test_render_query__returns_json_lines_records(self) -> None:
        result = QueryResult(dependencies=(Dependency(relation="tests", dependency="./tests/test_a.py"),))

        records = [
            json.loads(line)
            for line in AutomationRendered().render_query(result, ["warning"], relations=()).splitlines()
        ]

        assert records == [
            {"type": "dependency", "relation": "tests", "dependency": "./tests/test_a.py"},
            {"type": "warning", "message": "warning"},
        ]

    def test_render_skill__returns_json_record(self) -> None:
        record = json.loads(AutomationRendered().render_skill())

        assert record["type"] == "skill"

    def test_render_error__returns_json_record(self) -> None:
        record = json.loads(AutomationRendered().render_error({"type": "error", "code": "x", "message": "failed"}))

        assert record == {"type": "error", "code": "x", "message": "failed"}
