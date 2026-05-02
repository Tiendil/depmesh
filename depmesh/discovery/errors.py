from __future__ import annotations

from depmesh.core import errors as core_errors
from depmesh.domain.entities import RelationId


class Error(core_errors.Error):
    code = "query_error"


class UnknownRelationFilter(Error):
    code = "unknown_relation"

    def __init__(self, relation_id: RelationId) -> None:
        super().__init__(
            f"unknown relation `{relation_id}`",
            details={"relation": str(relation_id)},
        )
