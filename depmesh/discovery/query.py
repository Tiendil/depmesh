from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from depmesh.discovery import errors
from depmesh.discovery.entities import DependencyRule, QueryResult
from depmesh.discovery.expressions import EvaluationContext
from depmesh.discovery.paths import normalize_path
from depmesh.domain.entities import ArtifactId, Dependency, Relation, RelationId


def query_dependencies(
    root: Path,
    relations_by_id: Mapping[RelationId, Relation],
    rules: tuple[DependencyRule, ...],
    artifacts: list[ArtifactId],
    *,
    relation_filters: list[RelationId] | None = None,
    cwd: Path | None = None,
) -> QueryResult:
    relation_ids = _selected_relation_ids(relations_by_id, relation_filters)

    return _query_relations(
        root,
        relations_by_id,
        _filter_rules(rules, relation_ids),
        artifacts,
        cwd=cwd,
    )


def _selected_relation_ids(
    relations_by_id: Mapping[RelationId, Relation],
    relation_filters: list[RelationId] | None,
) -> set[RelationId]:
    if not relation_filters:
        return set(relations_by_id)

    selected_relation_ids: set[RelationId] = set()

    for relation_filter in relation_filters:
        relation = relations_by_id.get(relation_filter)
        if relation is not None:
            selected_relation_ids.add(relation.id)
            continue

        raise errors.UnknownRelationFilter(relation_filter)

    return selected_relation_ids


def _query_relations(
    root: Path,
    relations_by_id: Mapping[RelationId, Relation],
    rules: tuple[DependencyRule, ...],
    artifacts: list[ArtifactId],
    *,
    cwd: Path | None,
) -> QueryResult:
    dependencies: set[Dependency] = set()

    for artifact in artifacts:
        normalized_artifact = ArtifactId(normalize_path(artifact, root, cwd=cwd))

        for rule in rules:
            captures = rule.artifact.match(normalized_artifact, root)
            if captures is None:
                continue

            relation = relations_by_id.get(rule.relation)
            if relation is None:
                continue

            for dependency in _evaluate_rule_dependencies(root, rule, captures):
                dependencies.add(Dependency(relation=relation.id, dependency=dependency))

    return QueryResult(dependencies=tuple(sorted(dependencies, key=lambda item: (item.relation, item.dependency))))


def _filter_rules(
    rules: tuple[DependencyRule, ...],
    allowed_relations: set[RelationId],
) -> tuple[DependencyRule, ...]:
    return tuple(rule for rule in rules if rule.relation in allowed_relations)


def _evaluate_rule_dependencies(root: Path, rule: DependencyRule, captures: dict[str, str]) -> list[ArtifactId]:
    dependencies: set[ArtifactId] = set()
    context = EvaluationContext(root=root, relation_id=rule.relation, captures=captures)

    dependencies.update(rule.dependency.evaluate(context))

    return sorted(dependencies)
