from __future__ import annotations

import enum


class OutputProtocol(enum.StrEnum):
    human = "human"
    llm = "llm"
    automation = "automation"
