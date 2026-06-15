# Phasing: Quality-First Creative Workbench

## Scoping Principle

Phase 1 should solve the current quality bottlenecks directly:

- users cannot clearly see what was sent into generation
- users cannot review or stop risky video generation before render
- users cannot efficiently route rework when continuity or pacing fails

Phase 1 should not attempt to deliver the full idealized workbench in one pass.

## Current Phase Status

As of 2026-06-15, the workbench shell and several direct production actions are implemented, but Phase 1 is not complete.

The current frontend provides a useful production overview and can initiate key generation and preflight actions. The next implementation pass should prioritize the missing correction loop:

1. Restore shot edit, add, delete, and reorder controls inside the new workbench.
2. Make preflight and post-render findings route directly into those controls.
3. Complete generation transparency for prompts, models, parameters, source traces, and inherited assets.
4. Surface detailed task progress, failure reasons, and retry or recovery actions.

Broader canvas behavior and additional visual redesign remain lower priority than completing these production workflows.

## Phase 1: Must Ship First

### 1. Generation Transparency

Ship dual-layer transparency for the most quality-sensitive steps:

- storyboard generation
- shot first-frame or shot image generation
- video preflight
- video render execution
- post-render review

Users should be able to see:

- source mode
- upstream assets and references
- locked or missing dependencies
- prompt text
- selected model and key parameters
- continuity-sensitive inherited inputs such as first frame or previous last frame

### 2. Video Preflight And Post-Render Review

Ship a visible review stage before render and a visible finding surface after render.

This should include:

- readiness and blocked reasons
- quality risks that are not hard blockers
- blocking vs advisory findings
- recommended next actions

### 3. Shot-Level Rework Routing

Ship problem-based rework routing for the most common failure types:

- continuity issue -> shot-level rework
- pacing or narrative issue -> storyboard-level rework
- local defect issue -> local fix if supported, otherwise shot redo

### 4. Storyboard Review Controls

Ship only the controls needed to materially improve output quality:

- edit shot prompt
- replace associated assets
- replace first frame
- reorder shots
- adjust shot duration

### 5. Locked Visual Asset Visibility

Ship clear visibility of which locked assets are being used downstream and which missing asset decisions block render.

## Phase 1: Explicitly Out Of Scope

- full freeform node canvas
- broad workflow redesign for every low-priority step
- advanced local image repair tooling if the current stack cannot support it cleanly
- generalized provider studio or prompt-programming surface beyond transparent viewing and limited editing
- large script-writing workflow redesign

## Phase 2: Next After Phase 1

### 1. Richer Workbench Interaction

- more flexible studio layout
- denser trace drawers and cross-step comparisons
- stronger cross-surface navigation

### 2. Asset Review Expansion

- richer compare-and-lock flows for character visual candidates
- better key-image management
- more reusable asset collections

### 3. Deeper Local Repair

- local defect correction tools
- more granular shot patch workflows

### 4. Broader Product Unification

- wider adoption of the workbench model across more entry flows
- stronger consistency between chapter-based, image-based, and brief-based creation

## Why This Scope Is Simpler

This scope drops several tempting but premature additions:

- no full Toonflow-style canvas in Phase 1
- no Electron-like product reshaping
- no speculative plugin system for generation transparency
- no broad rewrite of creative writing flows

That is acceptable because the confirmed present problem is video quality control, especially continuity and reviewability, not lack of a graph editor or lack of a new runtime model.
