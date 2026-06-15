# Tasks

Status reviewed 2026-06-15.

This change remains directionally valid, but its checklist has not yet been reconciled item-by-item against the current implementation. The current product already contains several relevant contracts and workflows, including multiple project creation entry paths, storyboard source traces, asset-aware generation, video preflight, review findings, and explicit task outcomes. Keep unchecked items unchecked until their ownership boundaries, persistence behavior, and end-to-end verification are confirmed.

Near-term reconciliation priorities:

- Confirm whether video quality results are persisted after rendering or only represented during review.
- Confirm task status and progress-event contracts across API, database, worker, and frontend.
- Audit remaining direct cross-domain reads before claiming domain ownership separation.
- Verify source-independent storyboard and video workflows through end-to-end tests.

## 1. Establish Domain Contracts

- [ ] Define source artifact contracts for novel chapters, image references, and user briefs.
- [ ] Define canonical `source_mode` values and compatibility mappings for existing image-first workflow names.
- [ ] Define storyboard shot plan output with source trace, continuity rules, narration intent, visual prompt, and asset requirements.
- [ ] Define asset reference contracts for locked character visuals, key images, first frames, and generated media.
- [ ] Define video preflight result contracts with quality blocking reasons.
- [ ] Define video quality plan and video quality result contracts.

## 2. Separate Domain Ownership

- [ ] Mark current models and tables by owning domain.
- [ ] Identify direct cross-domain reads and writes that violate ownership.
- [ ] Replace video-to-novel internals access with chapter artifacts or storyboard source traces.
- [ ] Ensure provider calls are routed through adapter boundaries instead of scattered business code.

## 3. Make Storyboard Source-Independent

- [ ] Support finalized novel chapters as one storyboard source mode.
- [ ] Support image/reference assets as one storyboard source mode.
- [ ] Support user brief as one storyboard source mode.
- [ ] Store source mode and source trace for each storyboard and shot.

## 4. Strengthen Asset & Visual Generation

- [ ] Treat assets as reviewable, lockable, versioned creative inputs.
- [ ] Support generation and locking of character visuals, key images, and shot first frames.
- [ ] Ensure video consumes approved or usable asset references instead of generating around missing inputs.

## 5. Add Quality-First Video Gates

- [ ] Create a video quality plan before rendering that describes opening, development, ending, shot purpose, pacing, narration, subtitle, and visual continuity expectations.
- [ ] Record a video quality result after rendering that reports short-film structure, visual stability, and content consistency status.
- [ ] Block video tasks when required story constraints, source traces, or visual assets are missing.
- [ ] Block image-to-video paths when required first frames are missing.
- [ ] Prevent silent fallback to lower-quality paths when the selected source mode requires controlled assets.
- [ ] Expose quality gate failures as user-actionable states.

## 6. Normalize Task Runtime

- [ ] Define task statuses and progress event types.
- [ ] Separate blocked, failed, retryable, and completed outcomes.
- [ ] Persist provider task ids, provider errors, retry counts, and user-action-required details.
- [ ] Keep local worker execution initially, but make the contract replaceable by a queue-backed runtime.

## 7. Frontend Workflow

- [ ] Present video creation as multiple source modes instead of a novel-only continuation.
- [ ] Show source trace, missing assets, quality gate failures, and next actions.
- [ ] Preserve novel-to-video as one option, not the only option.

## 8. Verification

- [ ] Verify novel-sourced video preserves chapter artifact constraints.
- [ ] Verify image-sourced video can proceed without selecting a novel chapter.
- [ ] Verify brief-sourced video can create a storyboard without novel internals.
- [ ] Verify missing required visual inputs block video creation with an actionable reason.
- [ ] Verify final video quality checks cover short-film feel, visual stability, and content consistency.
