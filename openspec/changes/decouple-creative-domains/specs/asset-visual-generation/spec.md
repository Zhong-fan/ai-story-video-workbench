# Asset & Visual Generation Specification

## ADDED Requirements

### Requirement: Assets Are Reviewable Creative Inputs

The system SHALL treat visual assets as reviewable, lockable, reusable creative inputs rather than transient generated files.

#### Scenario: Character visual is locked

- **GIVEN** multiple visual candidates exist for a character
- **WHEN** the user locks one candidate
- **THEN** downstream shot image generation and video generation SHALL prefer the locked character visual

#### Scenario: Shot first frame is required

- **GIVEN** a shot requires controlled image-to-video generation
- **WHEN** the user attempts to create a video task
- **THEN** the system SHALL require a usable first-frame or key-image asset before rendering

### Requirement: Asset Domain Owns Visual Generation Workflow

The asset domain SHALL own visual asset generation workflows such as reference candidates, character visuals, key images, and shot first frames.

#### Scenario: Generate shot first frame

- **WHEN** a shot needs a first frame
- **THEN** the asset domain SHALL create and track the generated first-frame asset
- **AND** provider-specific image generation SHALL go through the provider adapter layer

### Requirement: Asset References Are Cross-Domain Contracts

Other domains SHALL reference assets through stable asset identifiers and status fields rather than file-path assumptions.

#### Scenario: Video consumes asset reference

- **GIVEN** a video task consumes a storyboard shot
- **WHEN** it needs visual inputs
- **THEN** it SHALL use asset references and asset status to determine readiness

