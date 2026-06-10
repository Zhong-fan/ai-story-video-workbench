# Change: Upgrade Product Into a Quality-First Creative Workbench

## Why

The current product is strong at executing a linear generation pipeline, but it does not give users enough control to improve final output quality when generation goes wrong. The most serious quality failures are visual continuity drift across shots and weak short-film rhythm after video generation.

A more automated workflow alone will not solve this. Users need a product shape that makes the generation chain visible, exposes the actual creative inputs used at each step, and inserts practical review and intervention points before low-quality results propagate downstream.

The goal of this change is to upgrade the product from a pipeline-oriented workbench into a quality-first creative workbench inspired by Toonflow's interaction model, while keeping ChenFlow's stronger quality gates and continuity blocking behavior.

## What Changes

- Introduce a quality-first creative workbench product model instead of treating video production as a mostly linear continuation of novel generation.
- Add a workbench experience that makes the generation chain visible from source selection through storyboard, asset preparation, video preflight, rendering, and review.
- Expose dual-layer generation transparency:
  - an operator-level view that shows what the step uses and why
  - a technical detail view that shows full prompts, parameters, models, and upstream inputs
- Add mandatory or recommended manual intervention points around:
  - video preflight and post-render review
  - storyboard shot review and correction
  - visual asset locking and confirmation
- Add issue-driven rework paths instead of one fixed retry path:
  - narrative or pacing issues return to storyboard or sequence level
  - continuity issues return to shot level
  - local image defects return to local fix or shot redo level
- Preserve and elevate existing continuity and quality gates rather than replacing them with a purely agent-driven flow.

## Non-Goals

- Do not rewrite the product into Electron or adopt Toonflow's runtime stack.
- Do not make script generation the primary focus of this change.
- Do not remove the current chapter-based workflow.
- Do not force a full node-graph editor in the first iteration.
- Do not hide generation details behind a simplified UI with no auditability.

## Impact

- Product UX should shift from "run next step" toward "inspect, approve, adjust, and continue."
- The workbench should explain how each output was produced, which assets and prompts were used, and what the next quality-sensitive action is.
- Video generation should become more reviewable before render and more actionable after failure.
- Storyboard and asset flows should become first-class quality control surfaces instead of passive intermediate artifacts.
