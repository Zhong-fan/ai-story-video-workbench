# Shot Rework Routing Specification

## ADDED Requirements

### Requirement: Rework Is Routed By Problem Type

The system SHALL route rework by problem type rather than exposing only a generic retry action.

#### Scenario: Continuity issue

- **GIVEN** a shot has a character consistency, style drift, or first-frame continuity problem
- **WHEN** the user chooses to fix it
- **THEN** the system SHALL route the user to shot-level rework controls

#### Scenario: Pacing or narrative issue

- **GIVEN** a sequence has weak rhythm, poor opening, weak ending, or narrative structure problems
- **WHEN** the user chooses to fix it
- **THEN** the system SHALL route the user to storyboard or sequence-level controls

#### Scenario: Local defect issue

- **GIVEN** a shot has a local visual defect without broader sequence failure
- **WHEN** the user chooses to fix it
- **THEN** the system SHALL route the user to local fix controls when supported
- **AND** it SHALL otherwise route to shot-level redo

### Requirement: Shot-Level Rework Is Specific

The system SHALL provide targeted shot-level rework actions for continuity-sensitive failures.

#### Scenario: Replace shot dependency

- **GIVEN** a shot rework task is triggered for continuity reasons
- **WHEN** the user opens shot-level rework
- **THEN** the system SHALL allow replacement or selection of first frame, associated assets, and prompt inputs

#### Scenario: Shot-level finding focuses the matching shot

- **GIVEN** a review finding identifies a specific shot-level continuity or local-defect issue
- **WHEN** the user selects that finding or its rework action
- **THEN** the system SHALL highlight the matching shot in the storyboard list
- **AND** it SHOULD scroll the user to the shot edit form when entering edit mode

#### Scenario: Render-stage source diagnostics focus the matching shot

- **GIVEN** a render-stage prompt source is attached to a specific shot
- **WHEN** the user selects that source from the transparency surface
- **THEN** the system SHOULD highlight the matching shot
- **AND** it SHOULD open or focus the shot-edit surface when direct correction is available

### Requirement: Rework Recommendation Is Explainable

The system SHALL explain why a rework route is recommended.

#### Scenario: User sees recommended route

- **GIVEN** the system identifies a likely failure cause
- **WHEN** it recommends a rework path
- **THEN** the system SHALL explain the likely cause, the recommended rework level, and the expected effect of that correction
