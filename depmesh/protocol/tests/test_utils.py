from __future__ import annotations

from llm_tool_cli.protocol import Protocol

from depmesh.protocol.renderers.automation import AutomationRendered
from depmesh.protocol.renderers.human import HumanRendered
from depmesh.protocol.renderers.llm import LLMRendered
from depmesh.protocol.utils import renderer


class TestRenderer:
    def test_human_protocol(self) -> None:
        assert isinstance(renderer(Protocol.human), HumanRendered)

    def test_llm_protocol(self) -> None:
        assert isinstance(renderer(Protocol.llm), LLMRendered)

    def test_automation_protocol(self) -> None:
        assert isinstance(renderer(Protocol.automation), AutomationRendered)
