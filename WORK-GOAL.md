# Work Goal — Self-hosted Codex Usage Monitor MVP

## Role Model

**Sol = Technical Lead / Planner / Reviewer**

Sol owns the overall MVP goal, canonical-document interpretation, task sequencing, bounded-task delegation, evidence review, escalation decisions, and final validation gate.

**Luna = Implementation Agent**

Luna owns exactly one bounded `TASK-xxxx` at a time, repository changes within allowed scope, required tests, actual validation commands, evidence-based execution reports, and allowed updates to `implementation-status.md`.

## Goal

Complete the Self-hosted Codex Usage Monitor MVP according to the canonical SDD documents.

## Canonical Order

1. `docs/specification.md`
2. `docs/design.md`
3. `docs/test-plan.md`
4. `docs/implementation-plan.md`
5. `docs/implementation-status.md` — status/evidence only, not requirements

## Operating Loop

1. Sol reads current status and relevant canonical sections.
2. Sol selects only the current READY task.
3. Sol delegates the bounded implementation to Luna when delegation is available.
4. Luna implements, tests, validates, and reports evidence.
5. Sol reviews the result against the canonical documents.
6. Sol returns exactly one planning outcome: CONTINUE with one bounded action, HUMAN_REQUIRED with evidence, or GOAL_COMPLETE with NEXT_ACTION: NONE.
7. Continue until the Stage 10 MVP validation gate passes or Human input is required.

## Hard Rules

- Do not expand scope or implement future tasks early.
- Do not change canonical requirements to make code pass.
- Do not substitute mock evidence for real runtime evidence.
- Do not expose OpenAI credentials.
- Do not use private `/backend-api/wham/*` as formal integration.
- Do not directly depend on `~/.codex/auth.json`.
- Do not guess undocumented Codex protocol behavior.
- Protocol/architecture/security conflicts are escalated to Sol/Human.
- Android and Phase 2 features are out of MVP.
- Do not declare MVP complete unless `OVERALL: PASS`.

## Initial State

```text
CURRENT_STAGE: Stage 0 — Repository Foundation
CURRENT_TASK: TASK-0001 — Create Project Skeleton
```

Begin with TASK-0001 only.
