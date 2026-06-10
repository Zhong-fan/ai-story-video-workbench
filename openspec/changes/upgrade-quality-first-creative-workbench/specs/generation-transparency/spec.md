# Generation Transparency Specification

## ADDED Requirements

### Requirement: Every Major Generation Step Has An Operator View

The system SHALL provide an operator-level view for each major generation step so users can understand what the step is doing without reading raw prompts or payloads.

Major generation steps in the near-term SHALL include at least:

- source preparation
- storyboard generation
- shot image or first-frame generation
- video preflight
- video render execution
- post-render review

#### Scenario: User opens a storyboard generation step

- **GIVEN** a storyboard generation step exists
- **WHEN** the user opens the default step view
- **THEN** the system SHALL show the source mode, the upstream artifacts used, the visual assets used, the main purpose of the step, and the next required action

### Requirement: Every Major Generation Step Has A Technical Detail View

The system SHALL provide a technical detail view for each major generation step so advanced users can diagnose and tune generation behavior.

#### Scenario: User expands generation details

- **GIVEN** a generation step exists
- **WHEN** the user expands the technical detail view
- **THEN** the system SHALL show the full prompt text, structured payload fields, selected provider and model, and key generation parameters

#### Scenario: Step inherits upstream context

- **GIVEN** a generation step uses upstream assets, traces, or locked visuals
- **WHEN** the user expands the technical detail view
- **THEN** the system SHALL show which inherited inputs were passed into the step
- **AND** the user SHALL NOT need to infer them from hidden backend behavior

#### Scenario: Render prompt sources are visible without raw JSON inspection

- **GIVEN** render-stage prompt sources have been persisted through asset prompts or task progress
- **WHEN** the user expands render-stage technical details
- **THEN** the system SHALL show render prompt sources as a dedicated UI section
- **AND** the user SHALL NOT need to locate them only by scanning raw JSON blobs

#### Scenario: Final render prompt is visually prioritized

- **GIVEN** the system has persisted a final or near-final render-stage prompt
- **WHEN** the user expands render-stage technical details
- **THEN** the system SHALL visually prioritize that final render prompt above supporting parameter dumps
- **AND** supporting prompt sources MAY appear as secondary diagnostic content

### Requirement: Input Provenance Is Visible

The system SHALL show where each major generation input came from.

#### Scenario: Input provenance for shot generation

- **GIVEN** a shot image or video generation step exists
- **WHEN** the user inspects the inputs
- **THEN** the system SHALL show whether the step used chapter-derived context, user brief context, uploaded references, locked character visuals, first frames, previous last frames, or generated prompts

### Requirement: Transparency Supports Diagnosis Rather Than Raw Data Dumping

The system SHALL organize generation details so users can identify why a result is poor and what to change next.

#### Scenario: User diagnoses a bad result

- **GIVEN** a generated result is poor
- **WHEN** the user inspects the step that produced it
- **THEN** the system SHALL highlight missing dependencies, risky fallbacks, and user-editable inputs
- **AND** the user SHALL NOT be limited to reading an unstructured raw payload dump

#### Scenario: Transparency is grouped by generation stage

- **GIVEN** a workflow contains source, storyboard, asset, preflight, and render stages
- **WHEN** the user inspects generation transparency
- **THEN** the system SHALL present those steps as a staged diagnostic sequence with per-step summaries
- **AND** it SHALL distinguish operator summary content from technical expansion content

#### Scenario: Render prompt source links back to correction

- **GIVEN** a render prompt source is associated with a specific shot
- **WHEN** the user selects that render prompt source
- **THEN** the system SHOULD focus the matching shot or shot-edit surface
- **AND** the user SHOULD NOT need to manually search the storyboard for the affected shot
