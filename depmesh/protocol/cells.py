from __future__ import annotations

from llm_tool_cli.protocol.logic_cells import ContentCell
from llm_tool_cli.protocol.logic_cells.base import LogicCell
from llm_tool_cli.protocol.output_cells import AutomationOutputCell, HumanOutputCell, LLMOutputCell
from llm_tool_cli.protocol.output_cells.base import MetaValue, OutputCell

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Relation


class DependenciesCell(LogicCell):
    result: QueryResult
    relations: tuple[Relation, ...]
    warnings: list[str]

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

        return [*cells, *self._warning_cells(cell_type)]

    def render_automation(self) -> list[OutputCell]:
        cells: list[OutputCell] = [
            AutomationOutputCell.build_meta(
                kind="dependency", type="dependency", relation=relation_id, dependency=dependency
            )
            for relation_id, dependencies in self.result.grouped().items()
            for dependency in dependencies
        ]
        return [*cells, *self._warning_cells(AutomationOutputCell)]

    def _warning_cells(self, cell_type: type[OutputCell]) -> list[OutputCell]:
        return [cell_type.build_meta(kind="warning", type="warning", message=warning) for warning in self.warnings]


def relation_cells(relations: tuple[Relation, ...]) -> list[ContentCell]:
    cells: list[ContentCell] = []
    for relation in sorted(relations, key=lambda item: item.id):
        meta: dict[str, MetaValue] = {"type": "relation", "relation": relation.id}
        if relation.description is not None:
            meta["description"] = relation.description
        cells.append(ContentCell(kind="relation", meta=meta))
    return cells
