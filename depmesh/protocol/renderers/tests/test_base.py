from __future__ import annotations

from depmesh.discovery.entities import QueryResult
from depmesh.domain.entities import Relation
from depmesh.protocol.renderers.base import Rendered
from depmesh.skills.entities import SkillDocument


class RenderedForTests(Rendered):
    def render_query(
        self,
        result: QueryResult,
        warnings: list[str],
        *,
        relations: tuple[Relation, ...],
    ) -> str:
        return "query\n"

    def render_relations(self, relations: tuple[Relation, ...]) -> str:
        return "relations\n"


class TestRendered:
    def test_render_skill__returns_text_instructions(self) -> None:
        assert RenderedForTests().render_skill().startswith("# `depmesh` Usage\n")

    def test_render_skill__returns_selected_document(self) -> None:
        assert RenderedForTests().render_skill(SkillDocument.configuration).startswith("# `depmesh` Configuration\n")

    def test_render_error__returns_message_text(self) -> None:
        assert RenderedForTests().render_error({"type": "error", "message": "failed"}) == "failed\n"
