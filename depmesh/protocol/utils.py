from __future__ import annotations

from depmesh.protocol.entities import OutputProtocol
from depmesh.protocol.renderers.automation import AutomationRendered
from depmesh.protocol.renderers.base import Rendered
from depmesh.protocol.renderers.human import HumanRendered
from depmesh.protocol.renderers.llm import LLMRendered


def renderer(protocol: OutputProtocol) -> Rendered:
    if protocol is OutputProtocol.human:
        return HumanRendered()

    if protocol is OutputProtocol.llm:
        return LLMRendered()

    return AutomationRendered()
