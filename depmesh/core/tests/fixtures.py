from collections.abc import Iterator

import pytest

from depmesh.core import warnings


@pytest.fixture(autouse=True)
def isolated_warnings() -> Iterator[None]:
    warnings.clear()
    try:
        yield
    finally:
        warnings.clear()
