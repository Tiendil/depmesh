from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from depmesh.core import warnings
from depmesh.discovery import errors
from depmesh.discovery.entities import DependencyRule, QueryResult
from depmesh.discovery.expressions import EvaluationContext
from depmesh.discovery.paths import normalize_existing_path, normalize_path
from depmesh.domain.entities import ArtifactId, Dependency, Relation, RelationId


def query_dependencies(
    root: Path,
    relations_by_forward_id: Mapping[RelationId, Relation],
    relations_by_backward_id: Mapping[RelationId, Relation],
    rules: tuple[DependencyRule, ...],
    artifacts: list[ArtifactId],
    *,
    relation_filters: list[RelationId] | None = None,
    cwd: Path | None = None,
) -> QueryResult:
    forward_relation_ids, backward_relation_ids = _selected_relation_ids(
        relations_by_forward_id,
        relations_by_backward_id,
        relation_filters,
    )
    dependencies: set[Dependency] = set()

    dependencies.update(
        _query_forward(
            root,
            relations_by_forward_id,
            _filter_rules(rules, forward_relation_ids),
            artifacts,
            cwd=cwd,
        ).dependencies
    )
    dependencies.update(
        _query_backward(
            root,
            relations_by_forward_id,
            _filter_rules(rules, backward_relation_ids),
            artifacts,
            cwd=cwd,
        ).dependencies
    )

    return QueryResult(dependencies=tuple(sorted(dependencies, key=lambda item: (item.relation, item.dependency))))


def _selected_relation_ids(
    relations_by_forward_id: Mapping[RelationId, Relation],
    relations_by_backward_id: Mapping[RelationId, Relation],
    relation_filters: list[RelationId] | None,
) -> tuple[set[RelationId], set[RelationId]]:
    if not relation_filters:
        return (
            set(relations_by_forward_id),
            {relation.id for relation in relations_by_backward_id.values()},
        )

    forward_relation_ids: set[RelationId] = set()
    backward_relation_ids: set[RelationId] = set()

    for relation_filter in relation_filters:
        forward_relation = relations_by_forward_id.get(relation_filter)
        if forward_relation is not None:
            forward_relation_ids.add(forward_relation.id)
            continue

        backward_relation = relations_by_backward_id.get(relation_filter)
        if backward_relation is not None:
            backward_relation_ids.add(backward_relation.id)
            continue

        raise errors.UnknownRelationFilter(relation_filter)

    return forward_relation_ids, backward_relation_ids


def _query_forward(
    root: Path,
    relations_by_forward_id: Mapping[RelationId, Relation],
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

            relation = relations_by_forward_id.get(rule.relation)
            if relation is None:
                continue

            for dependency in _evaluate_rule_dependencies(root, rule, captures):
                dependencies.add(Dependency(relation=relation.id, dependency=dependency))

    return QueryResult(dependencies=tuple(sorted(dependencies, key=lambda item: (item.relation, item.dependency))))


def _query_backward(
    root: Path,
    relations_by_forward_id: Mapping[RelationId, Relation],
    rules: tuple[DependencyRule, ...],
    artifacts: list[ArtifactId],
    *,
    cwd: Path | None,
) -> QueryResult:
    stored_warnings = warnings.read()

    try:
        warnings.clear()
        return _query_backward_without_warnings(root, relations_by_forward_id, rules, artifacts, cwd=cwd)
    finally:
        warnings.clear()
        for warning in stored_warnings:
            warnings.add(warning)


def _query_backward_without_warnings(
    root: Path,
    relations_by_forward_id: Mapping[RelationId, Relation],
    rules: tuple[DependencyRule, ...],
    artifacts: list[ArtifactId],
    *,
    cwd: Path | None,
) -> QueryResult:
    targets = {ArtifactId(normalize_path(artifact, root, cwd=cwd)) for artifact in artifacts}
    dependencies: set[Dependency] = set()

    for candidate in _project_files(root):
        candidate_query = _query_forward(
            root,
            relations_by_forward_id,
            rules,
            [candidate],
            cwd=root,
        )

        for forward_dependency in candidate_query.dependencies:
            if forward_dependency.dependency not in targets:
                continue

            relation = relations_by_forward_id.get(forward_dependency.relation)
            if relation is None:
                continue

            dependencies.add(Dependency(relation=relation.reverse_id, dependency=candidate))

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


def _project_files(root: Path) -> list[ArtifactId]:
    return [
        ArtifactId(normalize_existing_path(path, root))
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]
