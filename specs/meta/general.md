# General specification requirements

## Goal of the document

This document describes the general requirements for specifications in this project.

## Scope

The scope of this specification is limited to requirements for specification documents in this project.

The following topics are out of scope except when they affect how specification documents should be written:

- project behavior.
- implementation requirements.
- product requirements.

## Dictionary

- `specification` — a Markdown document in `./specs/` that describes requirements, behavior, terminology, or documentation rules for the project.
- `top-level section` — a section introduced by an `h2` Markdown header.
- `nested section` — a section introduced by an `h3` or deeper Markdown header.

## Sections

A specification MUST contain a single `h1` header with the name of the specification, which SHOULD be unique across all specifications.

Top-level information SHOULD be organized in sections with `h2` headers.

Nested sections MAY use `h3`, `h4`, and deeper headers when they make the document easier to navigate.

Nested sections SHOULD be used for details that belong to a parent top-level section, such as:

- examples.
- option descriptions.
- record fields.
- subsections of a larger topic.

Sections that are mandatory for all specifications:

- `Goal of the document` — a brief description of what the specification is about and what it aims to achieve.
- `Scope` — a brief description of what the specification covers and what it intentionally does not cover.

Optional sections:

- `Dictionary` — a list of terms that are specific to the specification.

The first sections of a specification SHOULD be placed in this order:

1. `Goal of the document`
2. `Scope`
3. `Dictionary`, when the section exists

The `Goal of the document` section MUST describe the content and purpose of the document.

The `Goal of the document` section MUST NOT define requirements for the document itself, such as saying that the document:

- MUST define something.
- MUST list something.
- MUST describe something.

The `Scope` section MUST describe the boundaries of the specification. It SHOULD be descriptive rather than normative when it explains what the document covers. It SHOULD explicitly mention important topics that are out of scope when those boundaries are useful for readers or future authors. It MUST NOT explain where to find requirements that belong to other specifications.

The `Dictionary` section SHOULD be placed immediately after the `Scope` section. It SHOULD contain only terms that are specific to the specification. Terms that are used by multiple specifications SHOULD be defined in `./specs/dictionary.md`.

## Style

- Specifications MUST use Markdown syntax for formatting the document.
- Specifications MUST follow [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).
- Specifications MUST NOT break long lines to fit within 80 characters or any other number; they MUST use as many characters as needed to express the idea clearly.
- Long enumerations SHOULD be organized as Markdown lists when possible.
