from __future__ import annotations

import re
from functools import cached_property
from typing import Literal

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.entities import DependencyRule
from depmesh.domain.entities import (
    Relation,
    RelationDescription,
    RelationId,
)

RELATION_ID_RE = re.compile(r"^[a-z0-9_]+$")


class RelationConfig(Relation):
    def to_relation(self) -> Relation:
        return Relation(
            id=self.id,
            description=self.description,
        )

    @pydantic.field_validator("id")
    @classmethod
    def validate_relation_id(cls, value: str) -> RelationId:
        if not RELATION_ID_RE.fullmatch(value):
            raise ValueError("relation id must contain only lowercase ASCII letters, digits, and underscores")
        return RelationId(value)

    @pydantic.field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> RelationDescription | None:
        if value == "":
            raise ValueError("relation descriptions must be non-empty when present")
        return RelationDescription(value) if value is not None else None


class Config(BaseEntity):
    version: Literal[1] = 1
    relations: tuple[RelationConfig, ...] = ()
    rules: tuple[DependencyRule, ...] = ()

    @pydantic.model_validator(mode="after")
    def validate_references(self) -> "Config":
        seen_ids: set[RelationId] = set()

        for relation in self.relations:
            if relation.id in seen_ids:
                raise ValueError(f"duplicate relation id `{relation.id}`")
            seen_ids.add(relation.id)

        relation_ids = {relation.id for relation in self.relations}
        for rule in self.rules:
            if rule.relation not in relation_ids:
                raise ValueError(f"rule references unknown relation `{rule.relation}`")

        return self


class Workspace(BaseEntity):
    root: pydantic.DirectoryPath
    relations: tuple[Relation, ...] = ()
    rules: tuple[DependencyRule, ...] = ()

    @cached_property
    def relations_by_id(self) -> dict[RelationId, Relation]:
        return {relation.id: relation for relation in self.relations}
