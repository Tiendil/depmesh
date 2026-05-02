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

Value entities SHOULD be immutable after construction when practical.

Entities that can be used for de-duplication SHOULD be hashable when practical.

## Pydantic baseline

The project accepts Pydantic v2 as the default dependency for entity modeling.

The project SHOULD provide shared base entity infrastructure owned by the core module.

Project entities SHOULD inherit from the shared base entity unless they have a specific reason to use Pydantic directly.

Shared entity defaults SHOULD:

- strip surrounding whitespace from string values.
- validate default values.
- reject unknown fields.
- prefer immutable value objects where practical.
- avoid attribute-based construction unless a boundary explicitly needs it.

Entities SHOULD use Pydantic field metadata and validators for local field constraints, default factories, discriminators, and model invariants.

Entities SHOULD use Pydantic serialization methods at boundaries that need model dumps or JSON.

The shared base entity SHOULD provide a copy-with-changes operation.

Very small internal helper values MAY use plain Python classes with `__slots__` when Pydantic would add no practical value.

Project data structures MUST NOT use `dataclasses.dataclass`.

## Enumeration conventions

Closed sets of named values MUST be represented as Python enums.

String-valued external protocols, modes, record kinds, predicate kinds, source kinds, and similar closed type sets MUST use `enum.StrEnum`.

Integer-valued closed sets MUST use `enum.IntEnum` when the integer value is part of the external contract.

Plain strings MUST NOT be used as the primary internal representation for values that have a finite configured or specified set of allowed names.

Enum values that cross external boundaries MUST preserve the specified serialized value exactly.

Output protocol values are a closed set of named string values and MUST be represented internally with an enum rather than raw strings or lists of strings.

## Semantic primitive types

Semantically specific primitive values MUST have semantically specific Python types before they cross module boundaries.

For example, a relation id, artifact id, or template variable name MUST NOT be represented as an unqualified `str` in entities or public function signatures when the value has a distinct project meaning.

Semantic primitive types SHOULD use `typing.NewType` when runtime behavior is identical to the underlying primitive.

Raw primitive types MAY be used at parsing, rendering, and serialization boundaries where external data is converted into or out of project types.

Raw primitive types MAY be used inside local helper code when the value has already been validated or when adding a semantic type would not improve module-boundary clarity.

Semantic primitive types SHOULD be owned by the module that owns the corresponding project concept.

## Entity ownership

Shared entity infrastructure MUST belong to the core module.

Shared domain entities MUST belong to the domain module.

Module-specific entities MUST belong to the module that owns the corresponding responsibility.

A module MAY expose entities from its public package interface when doing so simplifies imports for callers.

Public re-exports MUST NOT hide ownership. The defining module MUST remain clear from the source tree.

## Core domain entities

The domain layer MUST contain only universal entities for concepts shared by all or most other modules.

Domain entities MUST model universal dependency concepts independently from the concrete interface that created or renders them.

Domain entities MUST NOT depend on CLI protocol names, CLI option parsing, or concrete configuration file syntax.

Domain entities MUST NOT contain subsystem-specific entities when those entities are required only by one narrower module.

## Configuration entities

Configuration entities MAY represent parsed TOML data at the configuration loading boundary when their responsibility is to validate the configuration file shape.

Configuration entities SHOULD use Pydantic validation to reject malformed parsed data before it reaches lower layers.

Workspace entities MUST model validated configuration concepts independently from raw TOML table shapes before data reaches lower layers.

Workspace entities MUST expose shared project concepts as domain entities rather than configuration-specific entities.

Configuration entities MUST preserve enough information to report useful configuration errors.

Configuration entities MUST NOT execute artifact sources.

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
