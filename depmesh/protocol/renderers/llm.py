from __future__ import annotations

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Relation
from depmesh.protocol.renderers.base import Rendered


class LLMRendered(Rendered):
    def render_query(
        self,
        result: QueryResult,
        warnings: list[str],
        *,
        relations: tuple[Relation, ...],
    ) -> str:
        sections = []
        descriptions = {}

        for relation in relations:
            descriptions[relation.id] = relation.description
            descriptions[relation.reverse_id] = relation.reverse_description

        for relation, dependencies in result.grouped().items():
            lines = [f"## {relation}"]
            description = descriptions.get(relation)
            if description is not None:
                lines.extend(["", description])
            lines.append("")
            lines.extend(f"- {dependency}" for dependency in dependencies)
            sections.append("\n".join(lines))

        if warnings:
            lines = ["## warnings", ""]
            lines.extend(f"- {warning}" for warning in warnings)
            sections.append("\n".join(lines))

        return "\n\n".join(sections) + ("\n" if sections else "")
