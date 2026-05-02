from __future__ import annotations

import abc

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Relation
from depmesh.skills import load_skill_text


class Rendered(abc.ABC):
    @abc.abstractmethod
    def render_query(
        self,
        result: QueryResult,
        warnings: list[str],
        *,
        relations: tuple[Relation, ...],
    ) -> str:
        raise NotImplementedError

    def render_skill(self) -> str:
        return load_skill_text()

    @abc.abstractmethod
    def render_relations(self, relations: tuple[Relation, ...]) -> str:
        raise NotImplementedError

    def render_error(self, error_record: dict[str, object]) -> str:
        return str(error_record.get("message", "error")) + "\n"
