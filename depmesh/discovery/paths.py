from __future__ import annotations

from pathlib import Path

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error

from depmesh.discovery import errors
from depmesh.domain.entities import PathInput, ProjectPathId, ProjectRootPath, ResolvedProjectPath, UntrustedPath

PROJECT_ROOT_PREFIX = "@/"


def resolve_project_root(root: UntrustedPath) -> Result[ProjectRootPath, EnvironmentErrors]:
    try:
        return Ok(ProjectRootPath(root.resolve()))
    except (OSError, RuntimeError) as error:
        return Err([errors.PathResolutionFailed(path=str(root), reason=str(error)).with_cause(error)])


def _resolve_inside_project(
    path: UntrustedPath, root: ProjectRootPath, *, original: str
) -> Result[ResolvedProjectPath, EnvironmentErrors]:
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as error:
        return Err([errors.PathResolutionFailed(path=original, reason=str(error)).with_cause(error)])
    root_path = Path(root)

    if resolved == root_path or not resolved.is_relative_to(root_path):
        return Err([errors.InvalidProjectPath(path=original)])

    return Ok(ResolvedProjectPath(resolved))


def _canonical_from_resolved(resolved: ResolvedProjectPath, root: ProjectRootPath) -> ProjectPathId:
    return ProjectPathId(PROJECT_ROOT_PREFIX + resolved.relative_to(Path(root)).as_posix())


def _normalize_root_anchored(value: str) -> Result[str, EnvironmentErrors]:
    if not value.startswith(PROJECT_ROOT_PREFIX):
        return Err([errors.InvalidProjectPath(path=value)])

    raw = value.removeprefix(PROJECT_ROOT_PREFIX)
    parts: list[str] = []

    if not raw:
        return Err([errors.InvalidProjectPath(path=value)])

    for part in raw.split("/"):
        if part == "":
            return Err([errors.InvalidProjectPath(path=value)])

        if part == ".":
            continue

        if part == "..":
            if not parts:
                return Err([errors.InvalidProjectPath(path=value)])
            parts.pop()
            continue

        parts.append(part)

    if not parts:
        return Err([errors.InvalidProjectPath(path=value)])

    return Ok(PROJECT_ROOT_PREFIX + "/".join(parts))


@unwrap_to_error
def _resolve_root_anchored_path(value: str, root: ProjectRootPath) -> Result[ResolvedProjectPath, EnvironmentErrors]:
    normalized = _normalize_root_anchored(value).unwrap()
    path = root.joinpath(*normalized.removeprefix(PROJECT_ROOT_PREFIX).split("/"))
    return _resolve_inside_project(UntrustedPath(path), root, original=value)


@unwrap_to_error
def resolve_project_path(
    value: str, root: PathInput, *, allow_absolute: bool = True
) -> Result[ResolvedProjectPath | None, EnvironmentErrors]:
    project_root = resolve_project_root(UntrustedPath(root)).unwrap()

    if value.startswith("@"):
        if not value.startswith(PROJECT_ROOT_PREFIX):
            return Ok(None)
        resolved = _resolve_root_anchored_path(value, project_root)
    else:
        path = Path(value)
        if path.is_absolute() and not allow_absolute:
            return Ok(None)
        resolved = _resolve_inside_project(
            UntrustedPath(path if path.is_absolute() else project_root / path), project_root, original=value
        )

    if resolved.is_err() and all(isinstance(error, errors.InvalidProjectPath) for error in resolved.unwrap_err()):
        return Ok(None)
    return resolved


@unwrap_to_error
def normalize_path(
    value: str, root: PathInput, *, cwd: PathInput | None = None
) -> Result[ProjectPathId, EnvironmentErrors]:
    project_root = resolve_project_root(UntrustedPath(root)).unwrap()

    if value.startswith("@"):
        return Ok(ProjectPathId(_normalize_root_anchored(value).unwrap()))

    path = Path(value)
    candidate = path if path.is_absolute() else (cwd or root) / path
    resolved = _resolve_inside_project(UntrustedPath(candidate), project_root, original=value).unwrap()
    return Ok(_canonical_from_resolved(resolved, project_root))


def normalize_path_pattern(
    value: str, root: PathInput, *, cwd: PathInput | None = None
) -> Result[str | None, EnvironmentErrors]:
    result = normalize_path(value, root, cwd=cwd)
    if result.is_err() and all(isinstance(error, errors.InvalidProjectPath) for error in result.unwrap_err()):
        return Ok(None)
    return result


@unwrap_to_error
def normalize_existing_path(path: UntrustedPath, root: PathInput) -> Result[ProjectPathId, EnvironmentErrors]:
    project_root = resolve_project_root(UntrustedPath(root)).unwrap()
    resolved = _resolve_inside_project(path, project_root, original=str(path)).unwrap()
    return Ok(_canonical_from_resolved(resolved, project_root))
