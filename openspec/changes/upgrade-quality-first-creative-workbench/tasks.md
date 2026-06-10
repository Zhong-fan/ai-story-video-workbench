# Tasks

## Phase 1 Priority

- [ ] Ship generation transparency for storyboard, first-frame, preflight, render, and review, including prioritized render prompt display and source-level drill-down.
- [ ] Ship visible video preflight with blocked reasons, quality-risk warnings, and shot-level focus behavior where a shot can be identified.
- [ ] Ship post-render review with blocking versus advisory findings and direct focus into the recommended correction surface.
- [ ] Ship shot-level and storyboard-level rework routing based on issue type, including shot highlight and scroll-to-edit behavior.
- [ ] Ship minimal storyboard review controls that directly improve continuity and pacing.
- [ ] Ship downstream visibility for locked and missing visual assets.

## Phase 2 Priority

- [ ] Expand the workbench interaction model beyond the minimal studio layout.
- [ ] Expand asset review and compare flows.
- [ ] Add deeper local repair tooling where the stack supports it.
- [ ] Broaden the workbench model across more creation entry paths.

## 1. Define Workbench Product Scope

- [ ] Define the quality-first workbench as the primary creative control surface for video production.
- [ ] Preserve the current chapter-based flow as one entry path inside the workbench instead of the only product shape.
- [ ] Define the near-term workbench layout and navigation model without requiring a full node editor.

## 2. Define Generation Transparency

- [ ] Define operator-level step visibility for source inputs, asset bindings, quality risks, and next actions.
- [ ] Define technical detail visibility for prompts, models, parameters, payloads, and source traces.
- [ ] Define which generation steps must expose dual-layer transparency in the first iteration.
- [ ] Define how input provenance is presented for storyboard, first-frame, and video generation.
- [ ] Define how render-stage prompt sources are surfaced outside of raw JSON parameter dumps.
- [ ] Define how final render prompts are visually prioritized over supporting diagnostic payloads.

## 3. Define Manual Review And Approval Points

- [ ] Define the pre-render video review and approval flow.
- [ ] Define the post-render review flow with actionable findings.
- [ ] Define storyboard shot review actions including reorder, prompt edit, and asset replacement.
- [ ] Define asset locking actions for character visuals, key images, and first frames.
- [ ] Define blocking versus advisory review findings.

## 4. Define Rework Routing

- [ ] Define issue categories for narrative, continuity, and local visual defects.
- [ ] Define the recommended rework entry point for each issue category.
- [ ] Define how the product presents suggested fixes instead of generic retry actions.
- [ ] Define the shot-level rework action set for continuity-sensitive failures.
- [ ] Define the focus and highlight behavior when a review finding maps to a specific shot.
- [ ] Define the same focus behavior for shot-identifiable preflight issues and render-source diagnostics.

## 5. Align Product With Existing Gates

- [ ] Keep first-frame and continuity dependency checks as visible preflight conditions.
- [ ] Define blocked-state UX that explains why rendering cannot proceed.
- [ ] Prevent silent downgrade from controlled asset-based flows to lower-control generation paths.
- [ ] Define how locked visual assets are surfaced in downstream generation review.

## 6. Verification

- [ ] Verify users can see the generation chain and actual inputs used at each major step.
- [ ] Verify users can inspect both operator-level and technical-level generation details.
- [ ] Verify continuity failures route users back to shot-level rework.
- [ ] Verify pacing or structure failures route users back to storyboard or sequence-level rework.
- [ ] Verify video preflight and post-render review become first-class product steps rather than hidden backend checks.
