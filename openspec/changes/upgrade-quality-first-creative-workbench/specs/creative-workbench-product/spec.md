# Creative Workbench Product Specification

## ADDED Requirements

### Requirement: Quality-First Workbench Is The Primary Product Surface

The system SHALL present video-oriented creative production through a quality-first workbench instead of only through a linear next-step pipeline.

The near-term workbench MAY use a studio-style layout with structured panels rather than a full freeform node canvas, as long as it supports inspection, approval, correction, and continuation.

#### Scenario: Enter video production from the workbench

- **GIVEN** a user wants to create or improve a video workflow
- **WHEN** the user opens the primary production surface
- **THEN** the system SHALL show a workbench that includes source context, storyboard control, asset status, and video production status
- **AND** the workflow SHALL NOT require the user to navigate only by hidden backend state transitions

#### Scenario: Chapter-based flow remains supported

- **GIVEN** a project has finalized novel chapters
- **WHEN** the user starts from a finalized chapter
- **THEN** the system SHALL support that workflow as one workbench entry mode
- **AND** the chapter-based entry SHALL NOT be the only product path

### Requirement: The Generation Chain Is Visible

The system SHALL make the generation chain visible from source selection through render review.

#### Scenario: User inspects workflow chain

- **GIVEN** a storyboard or video task exists
- **WHEN** the user inspects the workbench
- **THEN** the system SHALL show which upstream artifacts, assets, and generation steps led to the current output
- **AND** the system SHALL show the current step, completed steps, blocked steps, and next available actions

### Requirement: Dual-Layer Generation Transparency

The system SHALL expose both an operator-level summary and a technical detail view for major generation steps.

#### Scenario: Operator-level step summary

- **GIVEN** a user reviews a generation step
- **WHEN** the user opens the default step view
- **THEN** the system SHALL show understandable business-level information including source inputs, asset bindings, model purpose, quality risks, and required next action

#### Scenario: Technical detail expansion

- **GIVEN** a user needs to diagnose or tune a generation step
- **WHEN** the user expands technical details
- **THEN** the system SHALL show full prompt text, structured payload fields, generation parameters, selected model, and source traces

### Requirement: Manual Review Is A First-Class Product Behavior

The system SHALL present manual review and approval points as intentional workflow stages for quality control.

#### Scenario: Pre-render review

- **GIVEN** a storyboard is about to enter video generation
- **WHEN** the user opens preflight review
- **THEN** the system SHALL show readiness, missing dependencies, quality risks, and recommended actions before render

#### Scenario: Post-render review

- **GIVEN** a video task finishes or partially finishes
- **WHEN** the user opens the review surface
- **THEN** the system SHALL allow the user to inspect quality findings and choose a rework action rather than only retrying the same task

### Requirement: Product Routes Rework By Issue Type

The system SHALL route rework based on issue type instead of using one generic retry flow.

#### Scenario: Continuity issue routes to shot-level work

- **GIVEN** the user or the system identifies a character consistency or shot continuity issue
- **WHEN** the user chooses to fix the issue
- **THEN** the product SHALL route the user to shot-level controls
- **AND** the available actions SHALL include prompt revision, first-frame replacement, and associated asset adjustment

#### Scenario: Pacing issue routes to storyboard-level work

- **GIVEN** the user or the system identifies a pacing or narrative structure issue
- **WHEN** the user chooses to fix the issue
- **THEN** the product SHALL route the user to storyboard or sequence-level controls
- **AND** the available actions SHALL include shot reorder, shot duration adjustment, and opening or ending revision

#### Scenario: Local visual defect routes to local fix or shot redo

- **GIVEN** a shot has a local visual defect without broader continuity failure
- **WHEN** the user chooses to fix the issue
- **THEN** the product SHALL route the user to a local fix action when supported
- **AND** it SHALL otherwise recommend shot-level regeneration
