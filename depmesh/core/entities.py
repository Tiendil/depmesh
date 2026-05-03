from __future__ import annotations

from typing import Any, Self

import pydantic


class BaseEntity(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid",
        frozen=True,
        validate_assignment=True,
        from_attributes=False,
    )

    def replace(self, **changes: Any) -> Self:
        return self.model_copy(update=changes, deep=True)
