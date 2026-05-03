from __future__ import annotations

from pathlib import Path

from depmesh.discovery import errors
from depmesh.domain.entities import PathInput, ProjectPathId, ProjectRootPath, ResolvedProjectPath, UntrustedPath

PROJECT_ROOT_PREFIX = "@/"


def resolve_project_root(root: UntrustedPath) -> ProjectRootPath:
    return ProjectRootPath(root.resolve())


def _resolve_inside_project(path: UntrustedPath, root: ProjectRootPath, *, original: str) -> ResolvedProjectPath:
    resolved = path.resolve()
    root_path = Path(root)

    if resolved == root_path or not resolved.is_relative_to(root_path):
        raise errors.InvalidProjectPath(original)

    return ResolvedProjectPath(resolved)


def _canonical_from_resolved(resolved: ResolvedProjectPath, root: ProjectRootPath) -> ProjectPathId:
    return ProjectPathId(PROJECT_ROOT_PREFIX + resolved.relative_to(Path(root)).as_posix())


def _normalize_root_anchored(value: str) -> str:
    if not value.startswith(PROJECT_ROOT_PREFIX):
        raise errors.InvalidProjectPath(value)

    raw = value.removeprefix(PROJECT_ROOT_PREFIX)
    parts: list[str] = []

    if not raw:
        raise errors.InvalidProjectPath(value)

    for part in raw.split("/"):
        if part == "":
            raise errors.InvalidProjectPath(value)

        if part == ".":
            continue

        if part == "..":
            if not parts:
                raise errors.InvalidProjectPath(value)
            parts.pop()
            continue

        parts.append(part)

    if not parts:
        raise errors.InvalidProjectPath(value)

    return PROJECT_ROOT_PREFIX + "/".join(parts)


def _resolve_root_anchored_path(value: str, root: ProjectRootPath) -> ResolvedProjectPath:
    normalized = _normalize_root_anchored(value)
    path = root.joinpath(*normalized.removeprefix(PROJECT_ROOT_PREFIX).split("/"))
    return _resolve_inside_project(UntrustedPath(path), root, original=value)


def resolve_project_path(value: str, root: PathInput, *, allow_absolute: bool = True) -> ResolvedProjectPath | None:
    project_root = ProjectRootPath(root.resolve())

    if value.startswith("@"):
        if not value.startswith(PROJECT_ROOT_PREFIX):
            return None
        try:
            return _resolve_root_anchored_path(value, project_root)
        except errors.InvalidProjectPath:
            return None

    path = Path(value)

    if path.is_absolute():
        if not allow_absolute:
            return None
        try:
            return _resolve_inside_project(UntrustedPath(path), project_root, original=value)
        except errors.InvalidProjectPath:
            return None

    try:
        return _resolve_inside_project(UntrustedPath(project_root / path), project_root, original=value)
    except errors.InvalidProjectPath:
        return None


def normalize_path(value: str, root: PathInput, *, cwd: PathInput | None = None) -> ProjectPathId:
    project_root = ProjectRootPath(root.resolve())

    if value.startswith("@"):
        return ProjectPathId(_normalize_root_anchored(value))

    path = Path(value)

    if path.is_absolute():
        candidate = path
    else:
        base = cwd or root
        candidate = base / path

    return _canonical_from_resolved(
        _resolve_inside_project(UntrustedPath(candidate), project_root, original=value),
        project_root,
    )


def normalize_path_pattern(value: str, root: PathInput, *, cwd: PathInput | None = None) -> str | None:
    try:
        project_root = ProjectRootPath(root.resolve())

        if value.startswith("@"):
            return _normalize_root_anchored(value)

        path = Path(value)

        if path.is_absolute():
            candidate = path
        else:
            base = cwd or root
            candidate = base / path

        return _canonical_from_resolved(
            _resolve_inside_project(UntrustedPath(candidate), project_root, original=value),
            project_root,
        )
    except errors.InvalidProjectPath:
        return None


def normalize_existing_path(path: UntrustedPath, root: PathInput) -> ProjectPathId:
    project_root = ProjectRootPath(root.resolve())
    return _canonical_from_resolved(
        _resolve_inside_project(path, project_root, original=str(path)),
        project_root,
    )
