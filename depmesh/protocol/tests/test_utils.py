from __future__ import annotations

from depmesh.protocol.entities import OutputProtocol
from depmesh.protocol.renderers.automation import AutomationRendered
from depmesh.protocol.renderers.human import HumanRendered
from depmesh.protocol.renderers.llm import LLMRendered
from depmesh.protocol.utils import renderer


class TestRenderer:
    def test_human_protocol(self) -> None:
        assert isinstance(renderer(OutputProtocol.human), HumanRendered)

    def test_llm_protocol(self) -> None:
        assert isinstance(renderer(OutputProtocol.llm), LLMRendered)

    def test_automation_protocol(self) -> None:
        assert isinstance(renderer(OutputProtocol.automation), AutomationRendered)
