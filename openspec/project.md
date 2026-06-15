# ChenFlow Workbench OpenSpec Project Guide

## Product Context

ChenFlow Workbench is a local-first Chinese creative workbench for longform fiction, storyboard planning, visual asset generation, and short video production. The current product already contains novel generation, storyboard generation, visual reference assets, first-frame generation, video rendering, and local worker execution.

The next architecture direction is not full microservices. The project should first become a modular, domain-oriented monolith with clear ownership, typed contracts, and future extraction points.

## Current Implementation Snapshot

As of 2026-06-15, the product is in the middle of a frontend workbench refactor.

- The primary frontend surface is a pink frosted-glass production workbench inspired by Toonflow's information architecture and interaction model. Toonflow's technical implementation is not being copied.
- Manual project creation, imported-text project drafting, and AI-brief project drafting are available as creation entry paths.
- The workbench exposes project context, storyboard state, asset status, video production status, and direct actions for character turnaround generation, shot first-frame generation, storyboard narration, video preflight, and video task creation.
- Existing backend and store capabilities are broader than the controls currently exposed by the new workbench.
- Shot editing, shot add/delete/reorder, longform planning, chapter generation, revision/finalization, detailed video-task progress, and issue-driven recovery still need to be reconnected or completed in the new frontend.
- The near-term priority is completing real production workflows and review/rework controls before adding freer canvas behavior or deeper visual polish.

Current verification baseline:

- Python unit and contract tests: 77 passing.
- Frontend template check, Vue type check, and production build: passing.
- Browser regression has passed against the current workbench flow.

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

## Validation

The official CLI package is `@fission-ai/openspec`.

Run strict validation without installing it globally:

```powershell
npx -y @fission-ai/openspec@latest validate --all --strict --no-interactive
```

For a persistent global command:

```powershell
npm install -g @fission-ai/openspec@latest
openspec validate --all --strict --no-interactive
```

Strict validation is required after editing OpenSpec requirements. Every added requirement must contain at least one mandatory `SHALL` or `MUST` statement.

## Near-Term Constraints

- The near-term implementation may remain a single backend application.
- The near-term implementation may remain a single MySQL database.
- The near-term worker may remain local, but task state, progress events, retry semantics, and failure reasons must become explicit.
- Provider integrations should be isolated behind adapter interfaces before adding more providers.
- The default backend port may conflict with Windows/Docker reserved port ranges on some development machines; local configuration must allow an alternate port.

