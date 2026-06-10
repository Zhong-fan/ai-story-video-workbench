# Design: Product-Led Quality Control Workbench

## Decision

Adopt a workbench-style product model that prioritizes visibility, intervention, and explainable quality control over silent end-to-end automation. The near-term product remains a web-based modular workbench, but its primary user experience becomes a creative production control surface instead of a simple linear pipeline.

## Product Structure

The upgraded product should center on one quality-first workbench with three tightly connected layers:

1. Creative source and asset layer
   - project context
   - visual style rules
   - character visuals
   - reference images
   - locked key images and first frames

2. Storyboard and sequence control layer
   - storyboard table
   - shot cards
   - shot order and grouping
   - shot-level prompts
   - asset bindings
   - continuity expectations

3. Video production and review layer
   - preflight checks
   - render plan
   - blocked reasons
   - segment outputs
   - review findings
   - rework actions

This product structure allows users to move forward, backward, or laterally depending on the type of quality problem.

## Transparency Model

The workbench should expose two visibility levels for every major generation step.

Operator view:

- source mode
- upstream assets and artifacts used
- locked or missing dependencies
- current model class and purpose
- quality risks
- next required user action

Technical detail view:

- full prompt text
- structured payload fields
- generation parameters
- selected provider and model
- inherited context and source traces
- relevant prior outputs and references

The operator view keeps the product understandable for non-technical creators. The technical detail view gives advanced users enough surface area to diagnose and improve poor generations.

In the near-term implementation, the transparency model should be rendered as a staged diagnostic surface rather than one raw trace dump. Each stage should expose:

- a concise operator summary
- inherited inputs and locked dependencies
- a technical expansion area
- step-specific prompt and parameter details when available

For render-stage transparency in particular, the product should surface persisted prompt sources as first-class UI content instead of burying them only inside generic JSON parameters.

## Manual Intervention Strategy

Manual intervention should be built into the product as a quality feature, not treated as an exceptional fallback.

Priority order:

1. Video preflight and post-render review
2. Storyboard shot inspection and correction
3. Asset locking and confirmation

Near-term intervention points should include:

- confirm or reject video preflight before render
- inspect blocked reasons and missing dependencies
- review rendered shots or segments with explicit findings
- replace shot first frame or associated assets
- edit shot prompt or reorder shots
- lock character visual, key image, or style baseline

## Rework Routing

The product should route users to different rework levels based on problem type.

Narrative or pacing issue:

- return to sequence or storyboard level
- adjust shot order, duration, opening, ending, or shot purpose

Continuity or character consistency issue:

- return to shot level
- replace first frame, update associated assets, or revise shot prompt

Local image defect:

- route to local fix action when supported
- otherwise fall back to shot-level redo

The user should never have to guess which layer to revisit after a failure. The product should explain the likely cause and recommend the rework entry point.

The near-term UI should also close the loop between diagnosis and correction:

- selecting a review finding should focus the recommended correction surface
- shot-level findings should highlight the corresponding shot card
- shot-level findings should scroll the user to the shot edit form when that form is opened
- preflight issues that identify a specific shot should reuse the same focus behavior

## Relationship To Existing Quality Gates

This change should preserve and elevate the current continuity and blocking logic.

Toonflow's strongest product lesson is the workbench shape, asset association model, and intermediate planning surfaces. ChenFlow's stronger quality-gate behavior should remain in place:

- required first-frame validation
- previous-last-frame continuity dependency
- explainable blocked states
- no silent fallback to low-control paths

The upgraded product should therefore combine:

- Toonflow-like workbench interaction and asset-aware planning
- ChenFlow-style continuity gating and render blocking

## Delivery Shape

The first product iteration does not need a fully general node editor. A studio-style workbench with structured panels, shot cards, trace drawers, and review queues is enough if it:

- surfaces the full generation chain
- supports intervention at the right points
- makes quality failures actionable

The design should optimize for quality control and transparency first, then consider freer canvas behaviors later if they materially improve production outcomes.
