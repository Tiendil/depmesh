# Instructions for AI Agents

This document contains project-specific instructions for agents working on `depmesh`.

Every agent MUST follow these instructions.

## Project Overview

`depmesh` is a Python CLI tool that helps coding agents understand dependencies of project artifacts.

The project is under active early development. Some behavior described in specifications may not be implemented yet.

Agents MUST NOT implement missing functionality unless explicitly asked to do so.

## Source Of Truth

Project behavior and architecture are specified in `./specs/`.

Agents MUST read the relevant specifications before making changes.

Start from `./specs/intro.md` to find the relevant specification documents.

When adding, deleting, or significantly changing a specification, agents MUST update `./specs/intro.md`.

Agents MUST NOT create new specifications without explicit instructions.

Agents MUST NOT delete or significantly change existing specifications without explicit instructions.

## Development Environment

All development-related operations MUST be performed in Docker containers.

Agents MUST NOT perform development-related operations directly on the host machine.

Allowed development commands:

- `./bin/dev.sh` — run development utilities inside the container, for example `./bin/dev.sh uv run -- pytest`.
- `./bin/dev-build-containers.sh` — build base Docker images for development; use only after approved Docker or dependency changes.

Searching, reading, and editing repository files MAY be done on the host machine.

## Restricted Changes And Operations

Agents MUST NOT perform these operations without explicit permission:

- Change `docker-compose.yml` or Docker-related configuration.
- Change Docker runtime parameters such as resources or volumes.
- Change running Docker services unrelated to this project.
- Install new dependencies.
- Update lock files.
- Install new tools, utilities, or software on the host machine or in development containers.
- Change project structure by moving files or creating new top-level directories.

If one of these operations seems necessary, agents MUST ask for explicit permission before doing it.

## Implementation Guidance

Follow existing specifications and local project patterns.

Keep changes scoped to the requested task.

Do not implement behavior that is only mentioned as future or possible functionality unless explicitly requested.

When code is added, tests SHOULD follow `./specs/architecture/tests.md`.

When entities, errors, warnings, or module layout are affected, agents MUST check the corresponding architecture specs.

## Tool Priority

Use `rg` for text and file searches unless a structural code query is needed.

Use `ast-grep` for structural Python code searches and code-pattern refactors.

Agents MUST use `ast-grep` when they need to:

- Search for specific Python constructs.
- Extract function, class, or variable definitions.
- Analyze code patterns or anti-patterns.
- Refactor specific code patterns across the codebase.
- Introduce small behavior changes into existing code.

Agents MUST NOT use `ast-grep` as the main tool for implementing large features that require substantial new code.
