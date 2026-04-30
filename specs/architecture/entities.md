# Entity architecture

## Goal of the document

This document describes the architecture of project entities and data structures used to pass dependency, configuration, and command information between modules.

## Scope

The scope of this specification is limited to architectural requirements for Python data structures that represent project concepts.

The following topics are out of scope:

- exact class names.
- exact constructor signatures.
- serialization formats for CLI protocols.
- dependency discovery algorithms.
- validation rules already specified by behavior specifications.

## Dictionary

- `entity` - a typed Python object that represents one project concept and can be passed across module boundaries.
- `value entity` - an entity whose equality is based on its data rather than object identity.
- `boundary entity` - an entity that is passed between modules with different responsibilities.
- `serialized representation` - a plain data representation prepared for an external protocol such as JSON Lines.

## General principles

Project concepts MUST be represented as explicit typed entities before they cross module boundaries.

Boundary entities MUST NOT be represented as untyped dictionaries unless the data is already being prepared as a serialized representation.

Entities SHOULD use Pydantic v2 for structured data models.

Entities SHOULD keep behavior close to their data only when that behavior is pure and local to the entity.

Entities MUST NOT perform:

- filesystem access.
- process execution.
- terminal output.
- configuration file discovery.
- plugin loading.

Value entities SHOULD be immutable after construction when practical.

Entities that can be used for de-duplication SHOULD be hashable when practical.

## Pydantic baseline

The project accepts Pydantic v2 as the default dependency for entity modeling.

The project SHOULD define a shared base entity in `./depmesh/core/entities.py`.

The shared base entity SHOULD inherit from `pydantic.BaseModel`.

The shared base entity SHOULD configure Pydantic with:

- `str_strip_whitespace=True`.
- `validate_default=True`.
- `extra="forbid"`.
- `frozen=True`.
- `validate_assignment=True`.
- `from_attributes=False`.

Project entities SHOULD inherit from the shared base entity unless they have a specific reason to use `pydantic.BaseModel` directly.

Entities SHOULD use `pydantic.Field` for default factories, validation constraints, discriminators, and metadata that belongs to the model field.

Entities SHOULD use Pydantic validators for local field and model invariants.

Entities SHOULD use Pydantic serialization methods at boundaries that need model dumps or JSON.

The shared base entity SHOULD provide a `replace` helper that returns a deep copied model with selected fields changed.

Very small internal helper values MAY use plain Python classes with `__slots__` when Pydantic would add no practical value.

Project data structures MUST NOT use `dataclasses.dataclass`.

## Entity ownership

Shared entity infrastructure MUST belong to `./depmesh/core/entities.py`.

Shared domain entities MUST belong to `./depmesh/domain/entities.py` or to submodules under `./depmesh/domain/entities/` if the entity set grows.

Module-specific entities MUST belong to the module that owns the corresponding responsibility.

Examples:

- configuration loading entities belong to `./depmesh/workspace/`.
- CLI argument and command selection entities belong to `./depmesh/cli/`.
- pure dependency query entities that are independent from CLI and workspace behavior belong to `./depmesh/domain/`.

A module MAY expose entities from its public package interface when doing so simplifies imports for callers.

Public re-exports MUST NOT hide ownership. The defining module MUST remain clear from the source tree.

## Core domain entities

The domain layer MUST contain entities for concepts that are shared by dependency query behavior and output behavior.

Domain entities MUST model dependency query concepts independently from the concrete interface that created or renders them.

Domain entities MUST NOT depend on CLI protocol names, CLI option parsing, or concrete configuration file syntax.

Domain entities MAY store normalized artifact identifiers when normalization is part of the domain behavior.

Domain entities MAY also preserve user-provided artifact spelling when that spelling is needed for output or error messages.

## Configuration entities

Configuration entities MUST represent already parsed configuration data, not raw TOML documents.

Configuration entities SHOULD use Pydantic validation to reject malformed parsed data before it reaches lower layers.

Configuration entities MUST model validated configuration concepts independently from raw TOML table shapes.

Configuration entities MUST preserve enough information to report useful configuration errors.

Configuration entities MUST NOT execute dependency expressions.

Configuration entities MAY reference domain entities when the referenced concept has already been validated as a domain concept.

## CLI entities

CLI entities MUST represent parsed user intent before the command is executed.

CLI entities MUST model command selection and parsed options independently from rendered output.

CLI entities MUST NOT contain rendered output.

CLI entities MUST NOT perform command execution.

## Data structure conventions

Ordered input from users and configuration files SHOULD be represented with ordered collections.

Sets MAY be used internally for de-duplication, but externally visible output order MUST be produced explicitly according to the relevant behavior specification.

Mappings keyed by relation id SHOULD be used when grouping dependencies by relation.

Optional values MUST be represented with `None` instead of sentinel strings.

Serialized representations MUST be created at protocol boundaries and SHOULD be treated as write-only output data.

Serialized representations SHOULD be produced from Pydantic models through explicit boundary code, not by leaking Pydantic dump shapes into domain behavior.

## Validation boundaries

Parsing layers SHOULD validate external data before creating entities that are used by lower layers.

Pydantic model validation MAY validate local invariants that are always true for the entity.

Validation that requires filesystem access, configuration discovery, or command execution MUST live outside pure entity definitions.

Invalid external input MUST be reported through the error architecture instead of by returning partially valid entities.
