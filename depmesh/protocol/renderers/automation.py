from __future__ import annotations

import json

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Relation
from depmesh.protocol.renderers.base import Rendered
from depmesh.skills import load_skill_text


def to_jsonl(record: dict[str, object]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"


class AutomationRendered(Rendered):
    def render_query(
        self,
        result: QueryResult,
        warnings: list[str],
        *,
        relations: tuple[Relation, ...],
    ) -> str:
        lines: list[str] = []

        for dependency in result.dependencies:
            lines.append(
                to_jsonl(
                    {
                        "type": "dependency",
                        "relation": dependency.relation,
                        "dependency": dependency.dependency,
                    }
                )
            )

        for warning in warnings:
            lines.append(to_jsonl({"type": "warning", "message": warning}))

        return "".join(lines)

    def render_skill(self) -> str:
        return to_jsonl({"type": "skill", "text": load_skill_text()})

    def render_relations(self, relations: tuple[Relation, ...]) -> str:
        lines = []

        for relation in sorted(relations, key=lambda item: item.id):
            record: dict[str, object] = {
                "type": "relation",
                "id": relation.id,
            }
            if relation.description is not None:
                record["description"] = relation.description
            lines.append(to_jsonl(record))

        return "".join(lines)

    def render_error(self, error_record: dict[str, object]) -> str:
        return to_jsonl(error_record)
