from collections.abc import Iterator

import pytest
from llm_tool_cli.output import output
from llm_tool_cli.output.tests.helpers import CollectingEmitter


@pytest.fixture(autouse=True)
def collected_output() -> Iterator[CollectingEmitter]:
    emitter = CollectingEmitter()
    with output.scope(emitter):
        yield emitter
