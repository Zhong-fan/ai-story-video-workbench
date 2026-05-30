# Creative Workflow Specification

## ADDED Requirements

### Requirement: Multi-Source Video Creation

The system SHALL support video creation from multiple source modes instead of requiring every video workflow to start from a novel chapter.

The canonical near-term source mode values SHALL include `novel_chapters`, `image_first_reference`, `existing_images`, and `user_brief`. Compatibility mappings to existing payloads SHALL be documented when legacy names or broader UI labels are used.

#### Scenario: Create video from finalized novel chapter

- **GIVEN** a project has a finalized chapter
- **WHEN** the user starts a video workflow from that chapter
- **THEN** the system SHALL create a chapter source artifact containing canonical text, summary, source version, and constraint snapshot
- **AND** the storyboard SHALL retain traceability to the chapter source artifact

#### Scenario: Create video from image references

- **GIVEN** a project has selected reference images or uploaded images
- **WHEN** the user starts a video workflow from images
- **THEN** the system SHALL create an image-reference source artifact
- **AND** the workflow SHALL NOT require a novel chapter id

#### Scenario: Create video from user brief

- **GIVEN** the user provides a video brief and project context exists
- **WHEN** the user starts a video workflow from the brief
- **THEN** the system SHALL create a brief source artifact
- **AND** the storyboard SHALL use project context and visual style constraints

### Requirement: Source Artifact Boundary

The system SHALL pass creative intent between domains through source artifacts rather than direct reads of another domain's internal workflow state.

#### Scenario: Video does not read novel internals

- **GIVEN** a video task is created from a novel-sourced storyboard
- **WHEN** the video domain prepares rendering
- **THEN** it SHALL consume storyboard shot plans and asset references
- **AND** it SHALL NOT read novel drafts, outline internals, or revision state directly

### Requirement: Future Combination Inputs

The system SHOULD allow future workflows to combine novels, images, characters, reference works, briefs, and existing storyboard inputs through a normalized source artifact contract.

#### Scenario: Combined source is introduced later

- **GIVEN** a future workflow combines a chapter excerpt with images and a brief
- **WHEN** the workflow is added
- **THEN** it SHOULD use the existing source artifact contract rather than creating a domain-specific shortcut
