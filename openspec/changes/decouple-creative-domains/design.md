# Design: Domain Core With Future Extraction

## Decision

Use a domain-oriented modular monolith now, with explicit future extraction boundaries. The system remains one FastAPI app and one database in the near term, but the OpenSpec defines strict domain ownership and cross-domain contracts.

## Domains

### Project Context Domain

Owns project setup, story boundaries, reference-work strategy, visual style rules, authorization boundaries, and Context Pack versions.

Produces:

- context packs
- constraint snapshots
- visual style constraints

### Novel Domain

Owns longform planning, chapter outlines, drafts, revisions, and finalized chapters.

Produces a `Chapter Artifact` for downstream use:

- chapter id
- canonical text
- chapter summary
- characters in scope
- required facts
- prohibited violations
- constraint snapshot
- source version

The Novel Domain must not create video tasks or call video rendering code.

### Storyboard Domain

Storyboard is an independent domain. It consumes normalized source artifacts and produces shot plans.

Supported near-term source modes:

- `novel_chapters`
- `image_first_reference`
- `existing_images`
- `user_brief`

These names intentionally align with the existing image-first planning work where possible. `user_brief` is the new brief-only mode; if implementation chooses to reuse `image_first_reference` for brief-only workflows, the API contract must document that mapping explicitly.

The Storyboard Domain produces:

- storyboard records
- storyboard shots
- shot summaries
- visual prompts
- narration plans
- source traces
- asset requirements
- continuity rules

### Asset & Visual Generation Domain

This domain is active, not just a file registry. It owns reference images, character visual assets, shot first frames, key images, lock state, versioning, review status, and visual asset generation workflows.

It may orchestrate image generation, but provider-specific calls should go through the Provider Adapter Layer.

### Video Production Domain

Owns video preflight, video tasks, render decisions, provider task submission, polling, segment handling, final assembly, and final video assets.

Video consumes storyboard shot plans and asset references. It must not read novel drafts or planning internals.

### Task/Event Runtime

Owns structured task states, progress events, failure reasons, retry semantics, and future queue extraction points.

Near-term worker execution may remain local.

### Provider Adapter Layer

Owns provider-specific calls for text models, image generation, video generation, TTS, and fallback implementations. Business domains should not scatter provider request logic.

## Constraint Propagation

Decoupling must not weaken content constraints.

When video starts from a novel chapter:

```text
Finalized Chapter
-> Chapter Artifact
-> Storyboard Source Artifact
-> Storyboard Shot Plan
-> Asset Requirements
-> Video Preflight
-> Video Task
```

When video starts from images or a brief:

```text
Images / Reference Assets / User Brief
-> Source Artifact
-> Storyboard Shot Plan
-> Asset Requirements
-> Video Preflight
-> Video Task
```

Every storyboard shot should retain `source_trace` so the final video can explain where each shot came from.

## Video Quality Acceptance

The primary acceptance target is video quality, not merely successful task execution.

The workflow should make quality inspectable through a `Video Quality Plan` before rendering and a `Video Quality Result` after rendering. These records give reviewers and tests something concrete to check instead of relying only on subjective playback impressions.

Quality is evaluated in three layers:

1. Finished short-film feel
   - clear opening, development, and ending
   - each shot has narrative purpose
   - narration, subtitles, visuals, and pacing work together
   - final output does not feel like a random demo montage

2. Visual stability
   - stable character appearance across shots
   - consistent project visual style
   - reviewable and lockable key images and first frames
   - no silent fallback that causes major style drift

3. Content consistency
   - novel-sourced video follows the chapter artifact and constraint snapshot
   - brief-sourced video covers the user's intent
   - image-sourced video preserves the selected visual subjects and style
   - key facts are not silently rewritten for video convenience

## Data Boundary

Near-term data may stay in one database, but every table or model should have one owning domain. Other domains consume data through contracts, artifacts, events, or read models.

Future schema or database extraction should happen only when justified by operational, ownership, scaling, compliance, or deployment needs.

## Task Runtime Boundary

Near-term task execution may keep the local worker. The task model should become explicit enough to support future queue-backed workers:

- task status
- task events
- retryability
- blocking reason
- provider task id
- provider error details
- user-action-required states

## Migration Strategy

The old fixed workflow may be broken or reshaped as long as existing data can be migrated or read through compatibility adapters.

Existing novel-to-video behavior should become one source mode, not the only source mode.
