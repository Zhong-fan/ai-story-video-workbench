# ChenFlow Workbench OpenSpec Project Guide

## Product Context

ChenFlow Workbench is a local-first Chinese creative workbench for longform fiction, storyboard planning, visual asset generation, and short video production. The current product already contains novel generation, storyboard generation, visual reference assets, first-frame generation, video rendering, and local worker execution.

The next architecture direction is not full microservices. The project should first become a modular, domain-oriented monolith with clear ownership, typed contracts, and future extraction points.

## Architecture Principles

- Prefer high cohesion and low coupling over deployment-unit count.
- Keep the near-term system as one FastAPI application and one database unless a boundary has a proven operational reason to split.
- Treat `Novel`, `Storyboard`, `Asset & Visual Generation`, `Video Production`, `Project Context`, `Task/Event Runtime`, and `Provider Adapter` as separate domains.
- Do not let video code depend on novel internals. Video consumes storyboard shot plans and asset references.
- Do not force every video workflow to start from a novel chapter.
- Preserve quality constraints through explicit artifacts, snapshots, source traces, and quality gates.

## Spec Conventions

- Use `SHALL` for mandatory behavior.
- Use `SHOULD` for recommended behavior.
- Use `MAY` for optional future behavior.
- Every requirement should include at least one scenario.
- Prefer source artifacts, shot plans, asset references, and task events over cross-domain table reads.

## Near-Term Constraints

- The near-term implementation may remain a single backend application.
- The near-term implementation may remain a single MySQL database.
- The near-term worker may remain local, but task state, progress events, retry semantics, and failure reasons must become explicit.
- Provider integrations should be isolated behind adapter interfaces before adding more providers.

