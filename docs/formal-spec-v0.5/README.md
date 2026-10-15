# Codex Usage Monitor — Formal Executable Specification Package v0.5

## Package Contents

1. `00-decisions.md` — unchanged Current Canonical Decision Record.
2. `01-product-requirements.md` — unchanged Current Canonical Product Requirements.
3. `02-system-architecture.md` — unchanged Current Canonical Architecture.
4. `03-formal-executable-specification.md` — formal, testable execution contract derived from 00–02.
5. `04-validation-execution-record.md` — executable Gate A/B/C evidence template.

## Authority

The three files `00`–`02` remain the Current Canonical Context because DEC-017 currently defines that canonical set.

Files `03` and `04` are formal derivative execution documents. They do not silently change the canonical set and do not override Accepted/Proposed/Superseded Decision status.

## What “Executable” Means

This package is executable in the engineering-specification sense:

- requirements are normative and testable;
- stop conditions are explicit;
- unresolved Human Gates are explicit;
- Validation Gates contain execution steps and PASS criteria;
- future implementers/coding agents are prohibited from inventing missing decisions.

It is intentionally **not** an Implementation Plan.

## Current Next Executable Work

The first independent executable activity is **Gate A — Windows Native Codex**.

Gate B and Gate C can also be executed when the real IIS/share environment is available.

Implementation work that depends on an unresolved Human Gate or failed/unrun Validation Gate must not assume a result.
