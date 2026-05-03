from __future__ import annotations

from depmesh.discovery import errors
from depmesh.domain.entities import RelationId


class TestUnknownRelationFilter:
    def test_as_record__uses_stable_code_and_relation_detail(self) -> None:
        error = errors.UnknownRelationFilter(RelationId("missing"))

        assert error.as_record() == {
            "type": "error",
            "code": "unknown_relation",
            "message": "unknown relation `missing`",
            "relation": "missing",
        }


class TestInvalidProjectPath:
    def test_as_record__uses_stable_code_and_path_detail(self) -> None:
        error = errors.InvalidProjectPath("../outside.py")

        assert error.as_record() == {
            "type": "error",
            "code": "invalid_project_path",
            "message": "invalid project path `../outside.py`",
            "path": "../outside.py",
        }
