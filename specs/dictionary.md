# Dictionary

## Goal of the document

This document defines terms that are specific to the `depmesh` project and are shared by multiple specifications.

## Scope

The scope of this specification is limited to project-specific terminology.

The following topics are out of scope:

- detailed behavior.
- implementation requirements.
- configuration schemas.

## Terms

- `artifact` — an entity whose dependencies can be queried by `depmesh`; initially expected to be a file path, with future room for other identifiers. Future artifact identifiers may include:
  - directories.
  - URLs.
  - DOI values.
  - ISBN values.
  - other identifiers.
- `dependency` — an artifact related to an input artifact by a configured relation.
- `relation` — a configured dependency category that connects artifacts.
- `forward relation id` — the identifier used for a relation in the forward direction.
- `backward relation id` — the identifier used for a relation in the backward direction.
- `directional relation id` — a forward relation id or backward relation id.
- `relation description` — optional text configured for one direction of a relation and rendered in outputs that need explanatory context.
- `protocol` — a CLI output contract selected by `--protocol`.
- `human protocol` — output protocol optimized for terminal users.
- `llm protocol` — output protocol optimized for coding agents that invoke `depmesh` as a tool.
- `automation protocol` — output protocol optimized for programs; output is serialized as JSON Lines.
- `warning` — a non-fatal problem discovered while processing a request.
