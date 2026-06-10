# Visual Asset Review Control Specification

## ADDED Requirements

### Requirement: Visual Assets Are Reviewable Before Downstream Use

The system SHALL require visual assets that affect continuity or style stability to be reviewable before downstream generation consumes them.

#### Scenario: Review character visual candidates

- **GIVEN** multiple character visual candidates exist
- **WHEN** the user opens asset review
- **THEN** the system SHALL allow the user to compare, select, and lock the preferred candidate for downstream use

### Requirement: Locked Assets Are Visible In Downstream Steps

The system SHALL show when downstream generation is using locked assets.

#### Scenario: Shot uses locked visual asset

- **GIVEN** a shot depends on a locked character visual or first-frame asset
- **WHEN** the user inspects downstream generation details
- **THEN** the system SHALL show the locked asset reference and its effect on the step

### Requirement: Missing Asset Decisions Are Actionable

The system SHALL convert missing asset prerequisites into clear user actions.

#### Scenario: Required first frame is missing

- **GIVEN** a controlled video path requires a first-frame asset
- **WHEN** no usable asset exists
- **THEN** the system SHALL show the missing prerequisite
- **AND** it SHALL offer the relevant next action such as generate, upload, replace, or lock
