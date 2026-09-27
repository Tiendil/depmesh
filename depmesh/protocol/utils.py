from __future__ import annotations

from llm_tool_cli.protocol import Protocol

from depmesh.protocol.renderers.automation import AutomationRendered
from depmesh.protocol.renderers.base import Rendered
from depmesh.protocol.renderers.human import HumanRendered
from depmesh.protocol.renderers.llm import LLMRendered


def renderer(protocol: Protocol) -> Rendered:
    if protocol is Protocol.human:
        return HumanRendered()

    if protocol is Protocol.llm:
        return LLMRendered()

    return AutomationRendered()
