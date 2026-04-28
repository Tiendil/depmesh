
# Instructions for the AI Agents

This document provides instructions and guidelines for the AI agents working on this project.

Every agent MUST follow the rules and guidelines outlined in this document when performing their work.

## Intro

`depmesh` is a CLI tool designed to help coding agents understand the dependencies of a specified artifact within the project.

**DepMesh is under heavy development => everything described below may change in the future; implementation of part of the functionality may be missing.**

- You MUST not implement missed parts without explicit instructions to do so.

## Expected behavior

- For specified artifact `depmesh` should display all dependencies of this artifact, grouped by their type.
- Artifact could be a file (we'll start with files only), directory, URLs, an id of a physical artifact (such as DOI for scientific papers, or book ISBN, etc.).
- All dependencies logic are defined by the developer in a config at the root of the project `depmesh.toml`.

Simplest imaginary example of usage (output format is not final and may change):

```bash
> my-tool ./src/do_smth.py

imports:

- ./src/some_module.py
- ./src/another_module.py

tests:

- ./src/tests/test_do_smth.py

specs:

- ./specs/architecture.md
- ./specs/types.md
- ./specs/top_level_behavior.md
```

Additional possible functionality:

- display dependencies for multiple files
- display only specific kinds of relations
- display reverse dependencies (i.e., which artifacts depend on the specified one)
- configure plugins for additional dependency types or logic.

### `depmesh.toml`

`depmesh.toml` contains:

- list of plugins, if any.
- list of relation types: id + name + description
- list of rules for detecting dependencies.

Rules are defined as a combination of:

1. filename (artifact) pattern
2. identifier of the relation type
3. expressions for detecting dependencies of this type for artifacts matching the pattern.

(1) filename patterns can be:

- fixed filename
- glob pattern
- regex pattern
- in the future: terminal command that does smth

Filename syntax should allow to capture parts of filename as parameters to use in dependency detection expressions.

(2) id of the relation type is an arbitrary string equal to the id of one of the relation types defined in the config.

(3) expressions for detecting dependencies is a way to find all dependencies for the specified artifact, they are a list of:

- fixed filename
- glob pattern
- regex pattern
- terminal command that outputs a list of dependencies

All expressions must be possible to parametrize with the parameters captured from the filename pattern.

Example of parametrization: for each file `./**{path}/*{name}.py` should exist file `./{path}/tests/test_{name}.py`.

## Environment

`depmesh` is developed in Python.

All development-related operations MUST be performed in Docker containers, see `./docker-compose.yml` for details.

You MUST not perform any development-related operations directly on the host machine.

Most important commands have script shortcuts in `./bin` directory.

Command you are allowed to use:

- `./bin/dev.sh` — run utils all kind of utils, for example `/bin/dev.sh uv run -- pytest ffun/parsers/tests/test_feed.py`
- `./bin/dev-build-containers.sh` — build base Docker images for development. Call this command after making changes to Docker configs or dependencies.

If you need to search or manipulate code, do that on the host machine, no need to use scripts from `./bin` or docker containers for that.

## Specifications

All specifications for `depmesh` are located in `./specs` directory.

- You MUST read them carefully before starting to work on the project.
- You are allowed to change existing specifications if it is required for your work.
- You MUST NOT create new specifications without explicit instructions to do so.
- You MUST NOT delete or significantly change existing specifications without explicit instructions to do so.

Places of interests:

- `./specs/intro.md` — list of all specifications and their brief descriptions. You MUST update it when you add/delete a specification or make significant changes to existing ones.

## Resticted changes / operations

You ABSOLUTELY MUST NOT perform the following operations without explicit instructions to do so:

- Changing `docker-compose.yml` or any Docker-related configuration.
- Changing Docker runtime parameters (like allocated resources, volumes, etc.).
- Changing running Docker services related to other projects or unrelated to development environment.
- Installing any new dependencies, both for frontend and backend.
- Updating lock files.
- Installing any new tools, utilities, or software on the host machine or in the development containers.
- Changing project structure, such as moving files around, creating new directories, etc.

If you want to change something in the above list, you MUST ask for explicit instructions and permission to do so.

## Top priority tools

These tools MUST have the highest priority when an agent is deciding which tool to use for a given task:

### `ast-grep`

`ast-grep` — a tool for searching and manipulating Abstract Syntax Trees in code. Use it when you work with particular code patterns, structures, or constructs in the codebase.

You MUST use it to:

- Search for specific code patterns or structures in the codebase.
- Extract information from code, such as function definitions, variable declarations, or specific code constructs.
- Analyze code for specific patterns or anti-patterns, such as code smells, security vulnerabilities, performance issues, specific usage of libraries or APIs, etc.
- Refactor particular code patterns or structures across the codebase.
- Introduce new small behaviors or features into existing code.

You MUST NOT use it for:

- Implementing huge features or behaviors that require adding massive blocks of code (like adding a new class, module, writing a huge function, etc.).
