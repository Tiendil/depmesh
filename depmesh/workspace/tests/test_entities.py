from __future__ import annotations

from pathlib import Path

import pydantic
import pytest

from depmesh.domain.entities import Relation, RelationDescription, RelationId
from depmesh.workspace.entities import Config, RelationConfig, Workspace


class TestRelationConfig:
    def test_to_relation__returns_domain_relation(self) -> None:
        relation = RelationConfig.model_validate(
            {
                "id": "tests",
                "description": "Tests related to the input artifacts.",
            }
        )

        assert relation.to_relation() == Relation(
            id=RelationId("tests"),
            description=RelationDescription("Tests related to the input artifacts."),
        )


class TestWorkspace:
    def test_relations_by_id__indexes_relations_by_id(self, tmp_path: Path) -> None:
        relation = Relation(id=RelationId("tests"))
        workspace = Workspace(root=tmp_path, relations=(relation,))

        assert workspace.relations_by_id == {RelationId("tests"): relation}


class TestConfig:
    def test_model_validate__valid_minimal_config(self) -> None:
        config = Config.model_validate(
            {
                "relations": [
                    {
                        "id": "tests",
                        "description": "Tests related to the input artifacts.",
                    }
                ],
                "rules": [
                    {
                        "relation": "tests",
                        "input": {"type": "glob", "pattern": "./src/{*module}.py"},
                        "output": {"type": "list", "artifacts": ["./tests/test_{module}.py"]},
                    }
                ],
            },
        )

        assert config.relations == (
            RelationConfig(
                id=RelationId("tests"),
                description=RelationDescription("Tests related to the input artifacts."),
            ),
        )
        assert config.rules[0].input_predicate.type == "glob"
        assert config.version == 1

    def test_model_validate__version_omitted_defaults_to_one(self) -> None:
        config = Config.model_validate(
            {"relations": [{"id": "tests"}]},
        )

        assert config.version == 1
        assert config.relations[0].id == "tests"

    def test_model_validate__relations_omitted_defaults_to_empty(self) -> None:
        config = Config.model_validate({})

        assert config.relations == ()

    def test_model_validate__relations_empty_is_allowed(self) -> None:
        config = Config.model_validate({"relations": []})

        assert config.relations == ()

    def test_model_validate__unknown_top_level_field(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Config.model_validate(
                {"relations": [{"id": "tests"}], "unknown": True},
            )

    def test_model_validate__unsupported_version(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Config.model_validate(
                {"version": 2, "relations": [{"id": "tests"}]},
            )

    def test_model_validate__duplicate_relation_ids(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Config.model_validate(
                {
                    "relations": [
                        {"id": "tests"},
                        {"id": "tests"},
                    ]
                },
            )

    def test_model_validate__rule_references_unknown_relation(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Config.model_validate(
                {
                    "relations": [{"id": "tests"}],
                    "rules": [
                        {
                            "relation": "imports",
                            "input": {"type": "one_of", "artifacts": ["./src/a.py"]},
                            "output": {"type": "list", "artifacts": ["./src/b.py"]},
                        }
                    ],
                },
            )

    def test_model_validate__output_template_must_be_provided_by_every_input_predicate(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            Config.model_validate(
                {
                    "relations": [{"id": "tests"}],
                    "rules": [
                        {
                            "relation": "tests",
                            "input": {
                                "type": "any",
                                "items": [
                                    {"type": "glob", "pattern": "./src/{*module}.py"},
                                    {"type": "one_of", "artifacts": ["./src/special.py"]},
                                ],
                            },
                            "output": {"type": "list", "artifacts": ["./tests/test_{module}.py"]},
                        }
                    ],
                },
            )
