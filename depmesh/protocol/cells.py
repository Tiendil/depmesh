from __future__ import annotations

from typing import Literal

import pydantic
from llm_tool_cli.protocol.logic_cells import ContentCell
from llm_tool_cli.protocol.logic_cells.base import LogicCell
from llm_tool_cli.protocol.output_cells import AutomationOutputCell, HumanOutputCell, LLMOutputCell
from llm_tool_cli.protocol.output_cells.base import OutputCell

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Relation


class DependenciesCell(LogicCell):
    is_journal: Literal[False] = pydantic.Field(default=False, exclude=True)
    result: QueryResult
    relations: tuple[Relation, ...]

    def render_human(self) -> list[OutputCell]:
        return self._render_text(HumanOutputCell)

    def render_llm(self) -> list[OutputCell]:
        return self._render_text(LLMOutputCell)

    def _render_text(self, cell_type: type[OutputCell]) -> list[OutputCell]:
        cells: list[OutputCell] = []
        descriptions = {relation.id: relation.description for relation in self.relations}

        for relation_id, dependencies in self.result.grouped().items():
            description = descriptions.get(relation_id)
            lines = [description, ""] if description is not None else []
            lines.extend(f"- {dependency}" for dependency in dependencies)
            cells.append(
                cell_type.build_markdown(
                    kind="dependencies", content="\n".join(lines), type="dependencies", relation=relation_id
                )
            )

        return cells

    def render_automation(self) -> list[OutputCell]:
        cells: list[OutputCell] = [
            AutomationOutputCell.build_meta(
                kind="dependency", type="dependency", relation=relation_id, dependency=dependency
            )
            for relation_id, dependencies in self.result.grouped().items()
            for dependency in dependencies
        ]
        return cells


def relation_cells(relations: tuple[Relation, ...]) -> list[ContentCell]:
    cells: list[ContentCell] = []
    for relation in sorted(relations, key=lambda item: item.id):
        cells.append(
            ContentCell(
                kind="relation",
                media_type="text/markdown" if relation.description is not None else None,
                content=relation.description,
                meta={"type": "relation", "relation": relation.id},
            )
        )
    return cells
