## ADDED Requirements

### Requirement: Correlated workflow diagnostics
The system SHALL correlate each user-triggered workflow execution with a unique run identifier and log major workflow phases with that identifier.

#### Scenario: Workflow starts
- **WHEN** a valid workflow begins
- **THEN** the system SHALL create a run identifier and record workflow start, validation success, inference start, persistence start, and final result in technical logs.

#### Scenario: Recoverable workflow failure occurs
- **WHEN** validation, inference, or persistence raises a recoverable application error
- **THEN** the system SHALL record the failure with the run identifier and safe context and SHALL leave the user's input available for retry.

#### Scenario: Unexpected workflow failure occurs
- **WHEN** an unexpected exception escapes validation, inference, or persistence
- **THEN** the system SHALL record the exception with stack trace and run identifier, show a concise user-visible error, and re-enable the action control.
