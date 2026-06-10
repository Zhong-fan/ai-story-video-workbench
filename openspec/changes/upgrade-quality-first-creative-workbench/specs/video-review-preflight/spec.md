# Video Review And Preflight Specification

## ADDED Requirements

### Requirement: Video Preflight Is A User-Visible Review Stage

The system SHALL present video preflight as a visible review stage before render instead of only as a backend validation step.

#### Scenario: User opens preflight before render

- **GIVEN** a storyboard is ready to enter video generation
- **WHEN** the user opens video preflight
- **THEN** the system SHALL show readiness status, required dependencies, continuity requirements, blocked reasons, and recommended next actions

### Requirement: Preflight Explains Quality Risk

The system SHALL explain not only whether rendering is allowed, but also what quality risks remain.

#### Scenario: Render is technically allowed but risky

- **GIVEN** required render inputs exist but continuity or style stability risk remains
- **WHEN** the user reviews preflight
- **THEN** the system SHALL show the quality risk and its likely downstream impact
- **AND** the user SHALL be able to continue knowingly or return to rework

#### Scenario: Shot-specific preflight issue focuses the matching shot

- **GIVEN** a preflight issue message identifies a specific shot-level problem
- **WHEN** the user selects that issue in the preflight surface
- **THEN** the system SHOULD focus the matching shot in the storyboard controls
- **AND** it SHOULD reuse the same shot-focus behavior used by post-render review findings

### Requirement: Post-Render Review Produces Actionable Findings

The system SHALL provide a post-render review surface that turns quality failures into explicit findings and rework actions.

#### Scenario: Review a rendered sequence

- **GIVEN** a video task completes or partially completes
- **WHEN** the user opens post-render review
- **THEN** the system SHALL show findings for continuity, pacing, structure, and local visual issues
- **AND** each finding SHALL map to a recommended rework path

#### Scenario: User can act directly from a review finding

- **GIVEN** review findings are visible in the post-render review surface
- **WHEN** the user selects one finding
- **THEN** the system SHALL route the user to the recommended correction layer
- **AND** the system SHOULD focus the relevant edit surface instead of leaving the user to search manually

### Requirement: Review Distinguishes Blocking From Advisory Findings

The system SHALL distinguish hard blockers from advisory quality concerns.

#### Scenario: Blocking review finding

- **GIVEN** a required visual dependency is missing or the output is unusable for continuation
- **WHEN** the review is shown
- **THEN** the system SHALL mark the finding as blocking
- **AND** the workflow SHALL require correction before dependent steps continue

#### Scenario: Advisory review finding

- **GIVEN** a result is usable but not ideal
- **WHEN** the review is shown
- **THEN** the system SHALL mark the finding as advisory
- **AND** the user MAY accept the result or choose to refine it
