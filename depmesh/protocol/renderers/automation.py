from __future__ import annotations

from llm_tool_cli.core.result import Result
from llm_tool_cli.protocol import to_jsonl

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Relation
from depmesh.protocol.renderers.base import Rendered
from depmesh.skills.entities import SkillDocument
from depmesh.skills.fixtures import load_skill_text


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

    def render_skill(self, document: SkillDocument = SkillDocument.usage) -> Result[str]:
        return load_skill_text(document).map(
            lambda text: to_jsonl({"type": "skill", "document": document, "text": text})
        )

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
