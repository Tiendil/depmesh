from __future__ import annotations

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Relation
from depmesh.protocol.renderers.base import Rendered


class HumanRendered(Rendered):
    def render_query(
        self,
        result: QueryResult,
        warnings: list[str],
        *,
        relations: tuple[Relation, ...],
    ) -> str:
        sections = []

        for relation, dependencies in result.grouped().items():
            lines = [f"{relation}:"]
            lines.extend(f"  {dependency}" for dependency in dependencies)
            sections.append("\n".join(lines))

        if warnings:
            lines = ["warnings:"]
            lines.extend(f"  {warning}" for warning in warnings)
            sections.append("\n".join(lines))

        return "\n\n".join(sections) + ("\n" if sections else "")

    def render_relations(self, relations: tuple[Relation, ...]) -> str:
        sections = []

        for relation in sorted(relations, key=lambda item: item.id):
            lines = [f"{relation.id}:"]
            if relation.description is not None:
                lines.append(f"  {relation.description}")
            sections.append("\n".join(lines))

        return "\n\n".join(sections) + ("\n" if sections else "")
