from __future__ import annotations

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Relation
from depmesh.protocol.renderers.base import Rendered


class RenderedForTests(Rendered):
    def render_query(
        self,
        result: QueryResult,
        warnings: list[str],
        *,
        relations: tuple[Relation, ...],
    ) -> str:
        return "query\n"


class TestRendered:
    def test_render_skill__returns_text_instructions(self) -> None:
        assert RenderedForTests().render_skill().startswith("# depmesh usage\n")

    def test_render_error__returns_message_text(self) -> None:
        assert RenderedForTests().render_error({"type": "error", "message": "failed"}) == "failed\n"
