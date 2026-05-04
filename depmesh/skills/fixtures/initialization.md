# `depmesh` Initialization

`depmesh init` creates a starter `depmesh.toml` for a project that does not have one yet.

The generated file is intentionally small. It gives the project a valid schema version, a basic governance relation pair, and commented rule examples that can be adapted to the project's real artifact layout.

Use this document when a configuration file is missing, when relation coverage is too small to be useful, or when adding `depmesh` to a new project.

For configuration syntax details, use:

```bash
depmesh -p llm skill configuration
```

## Project Root

Run initialization from the directory that should contain `depmesh.toml`.

Without `--config`, `depmesh init` creates `depmesh.toml` in the current working directory. With `--config PATH`, it creates that exact file and treats its parent directory as the project root for later commands.

The project root matters because artifact paths, glob patterns, file sources, and command sources are resolved from the directory containing `depmesh.toml`.

## Create The Starter File

Create `depmesh.toml` in the current directory:

```bash
depmesh init
```

Create it at an explicit path:

```bash
depmesh --config ./path/to/depmesh.toml init
```

`init` does not overwrite an existing file.

Right after creating the starter file, fill it with useful project-specific relations and rules. Ask the developer for expected dependency relations when they are available; otherwise, use the heuristics and examples below to infer an initial configuration from the project layout.

The starter file begins like this:

```toml
version = 1

[[relations]]
id = "governed_by"
description = "Specifications that apply to the artifact."

[[relations]]
id = "governs"
description = "Artifacts governed by the specification."
```

## Relation Descriptions

Write each relation description as the set of artifacts returned for the queried artifact.

Use `artifact` as the default term for the queried relation source. When the returned dependencies must be called `artifacts`, choose a more specific source role instead, such as specification, test, dictionary, index, source module, or document.

Prefer `Artifacts governed by the specification.` over wording that calls both sides artifacts or hides the queried artifact role.

Reverse relations should have independent descriptions:

```toml
[[relations]]
id = "governed_by"
description = "Specifications that apply to the artifact."

[[relations]]
id = "governs"
description = "Artifacts governed by the specification."
```

## Filling The Configuration

Start from artifact relationships that are stable in the project. Add relation definitions first, then add one or more rules for each direction that should be queryable.

Before choosing relations, investigate the project layout and tooling. Check source directories, test directories, specification or documentation directories, package manifests, dependency files, installed packages, build tools, static-analysis tools, and existing scripts. These usually reveal which relations can be discovered reliably.

General workflow:

1. Investigate project layout, dependencies, installed packages, and available tools.
2. List artifact families that matter: source files, tests, specs, docs, generated files, or package manifests.
3. Choose relation ids for each query direction.
4. Write descriptions that explain what the relation returns.
5. Choose predicates that match queried artifacts.
6. Use captures in predicates when output paths or commands need path-derived names.
7. Choose sources that produce dependency artifacts.
8. Add reverse relations only when reverse lookup is useful.

## Configuration Examples

1. Connect implementation files to specifications.

Use this when specifications govern implementation files:

```toml
[[relations]]
id = "governed_by"
description = "Specifications that apply to the artifact."

[[relations]]
id = "governs"
description = "Artifacts governed by the specification."

[[rules]]
relation = "governed_by"
input = { type = "glob", pattern = "@/src/**/*.py" }
output = { type = "files", pattern = "@/specs/**/*.md" }

[[rules]]
relation = "governs"
input = { type = "glob", pattern = "@/specs/**/*.md" }
output = { type = "files", pattern = "@/src/**/*.py" }
```

Use narrower patterns when only some specs apply to some implementation files.

2. Connect Python files by imports.

Use `command` sources when a project-specific script or static analyzer can print exact dependencies. The command must print one artifact id per stdout line.

```toml
[[relations]]
id = "imports"
description = "Python files imported by the artifact."

[[relations]]
id = "imported_by"
description = "Python files that import the artifact."

[[rules]]
relation = "imports"
input = { type = "glob", pattern = "@/src/{**module_path}.py" }
output = {
  type = "command",
  command = "python ./tools/list_imports.py --artifact @/src/{module_path}.py",
}

[[rules]]
relation = "imported_by"
input = { type = "glob", pattern = "@/src/{**module_path}.py" }
output = {
  type = "command",
  command = "python ./tools/list_imports.py --reverse --artifact @/src/{module_path}.py",
}
```

Example command output:

```text
@/src/settings.py
@/src/database.py
```

3. Connect source files to predictable tests.

Use captures when source and test paths share a module name:

```toml
[[relations]]
id = "tested_by"
description = "Tests that verify the artifact."

[[relations]]
id = "tests"
description = "Artifacts verified by the test."

[[rules]]
relation = "tested_by"
input = { type = "glob", pattern = "@/src/{*module}.py" }
output = { type = "files", pattern = "@/tests/test_{module}.py" }

[[rules]]
relation = "tests"
input = { type = "glob", pattern = "@/tests/test_{*module}.py" }
output = { type = "list", artifacts = ["@/src/{module}.py"] }
```

The capture name `module` from the predicate is reused as `{module}` in the output. Capture names must match exactly.

Use `files` for dependencies that should exist in the project. Use `list` when the artifact id is meaningful even if the file does not exist yet.

## Validation Loop

After editing `depmesh.toml`, list configured relations first:

```bash
depmesh -p llm relations
```

Example output:

```text
## governed_by

Specifications that apply to the artifact.

## tested_by

Tests that verify the artifact.
```

Then query representative artifacts:

```bash
depmesh -p llm dependencies --relation governed_by --relation tested_by @/src/app.py
```

Example output:

```text
## governed_by

- @/specs/behavior/app.md

## tested_by

- @/tests/test_app.py
```

When a query returns too many dependencies, narrow the rule predicate or output source. When it returns none, check path spelling, leading `@/`, capture names, and whether the output source is `files` and the files exist.
