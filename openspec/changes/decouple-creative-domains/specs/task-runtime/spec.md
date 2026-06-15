# Task Runtime Specification

## ADDED Requirements

### Requirement: Structured Task States

The system SHALL use structured task states for long-running creative generation.

#### Scenario: Task is waiting on user action

- **GIVEN** a video task lacks a required locked asset
- **WHEN** preflight runs
- **THEN** the task SHALL become `blocked`
- **AND** the blocking reason SHALL identify the missing requirement

#### Scenario: Provider fails

- **GIVEN** a provider call fails
- **WHEN** the task records the failure
- **THEN** the task SHALL store provider task id when available, provider error detail, retry count, and retryability

### Requirement: Progress Events

The system SHALL record progress events for long-running creative workflows.

#### Scenario: Video generation progresses

- **WHEN** a video task moves through preflight, provider submission, polling, segment download, and final assembly
- **THEN** each major step SHALL be recorded as a progress event

### Requirement: Replaceable Worker Runtime

The system SHALL define task contracts that remain executable by the near-term local worker and can later be executed by queue-backed workers.

#### Scenario: Queue-backed worker is introduced

- **WHEN** a queue-backed runtime replaces the local worker
- **THEN** domain contracts, task states, progress events, and quality gate semantics SHALL remain stable

