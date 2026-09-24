from __future__ import annotations

from depmesh.core import errors as core_errors
from depmesh.domain.entities import RelationId


class EnvironmentError(core_errors.EnvironmentError):
    code: str = "query_error"


class UnknownRelationFilter(EnvironmentError):
    code: str = "unknown_relation"
    message: str = "unknown relation `{error.relation}`"
    relation: RelationId


class InvalidProjectPath(EnvironmentError):
    code: str = "invalid_project_path"
    message: str = "invalid project path `{error.path}`"
    path: str


class PathResolutionFailed(EnvironmentError):
    code: str = "path_resolution_failed"
    message: str = "could not resolve project path `{error.path}`: {error.reason}"
    path: str
    reason: str


class CommandFailed(EnvironmentError):
    code: str = "command_failed"
    message: str = "relation `{error.relation}`: could not execute command `{error.command}`: {error.reason}"
    relation: RelationId
    command: str
    reason: str


class FilesUnreadable(EnvironmentError):
    code: str = "files_unreadable"
    message: str = "could not discover files under `{error.path}`: {error.reason}"
    path: str
    reason: str
