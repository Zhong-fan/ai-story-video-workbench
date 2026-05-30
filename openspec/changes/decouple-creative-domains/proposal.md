# Change: Decouple Creative Domains for Quality-First Video Production

## Why

The current workbench is too close to a demo-style fixed pipeline: project setup flows into novel generation, then storyboard generation, then video generation. This makes video creation feel strongly bound to novels even though the product should support more flexible creative entry points such as reference images, uploaded images, visual briefs, and pre-existing storyboard ideas.

The goal is not to introduce microservices immediately. The goal is to make the current system enterprise-ready in structure: high cohesion, low coupling, clear data ownership, explicit contracts, traceable tasks, and quality-first video production.

## What Changes

- Introduce a formal domain model for:
  - Project Context
  - Novel
  - Storyboard
  - Asset & Visual Generation
  - Video Production
  - Task/Event Runtime
  - Provider Adapter Layer
- Make Storyboard an independent domain instead of a video subroutine or a novel extension.
- Allow video workflows to start from:
  - finalized novel chapters
  - images or reference assets
  - user briefs
- Use source artifacts, source traces, constraint snapshots, storyboard shot plans, and asset references to preserve constraints without tightly coupling domains.
- Make video quality the primary acceptance target:
  - finished short-film feel
  - visual stability
  - content consistency
  - explainable quality blocking
- Keep the near-term architecture as a modular monolith while documenting future extraction boundaries.

## Non-Goals

- Do not require immediate microservice deployment.
- Do not require separate databases in the near term.
- Do not build a full node-based workflow editor in this change.
- Do not remove the ability to create video from finalized novel chapters.
- Do not allow low-quality fallback behavior that silently ignores missing source assets or constraints.

## Impact

- Backend services should be reorganized around domain ownership instead of fixed workflow order.
- API contracts should expose source modes, source artifacts, storyboard shot plans, asset requirements, and quality gate results.
- Frontend video creation should no longer imply that a novel chapter is mandatory.
- Tests and acceptance criteria should focus on video quality outcomes, not only technical execution success.

