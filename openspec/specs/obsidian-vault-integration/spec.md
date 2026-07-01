## Purpose

Defines how atomicOS discovers Obsidian Vault folders, builds safe note destinations, and creates notes through the Obsidian CLI.

## Requirements

### Requirement: Vault folder discovery
The system SHALL discover folders under the configured Obsidian Vault root and expose relative folder paths for UI selection.

#### Scenario: Vault contains nested folders
- **WHEN** the Vault root contains nested directories
- **THEN** the system SHALL return relative folder paths suitable for display in the folder dropdown.

#### Scenario: Vault root is unavailable
- **WHEN** the configured Vault root does not exist or cannot be read
- **THEN** the system SHALL return a recoverable configuration error and SHALL not show stale folder choices as valid.

### Requirement: Safe target path construction
The system SHALL build note target paths from the selected folder, optional subfolder, and title using normalized relative paths and SHALL reject absolute paths or parent traversal.

#### Scenario: Valid nested destination
- **WHEN** the user selects `Conhecimento/Java/SOLID`, enters optional subfolder `Principios`, and title `Single Responsibility Principle`
- **THEN** the system SHALL target `Conhecimento/Java/SOLID/Principios/Single Responsibility Principle` within the configured Vault.

#### Scenario: Unsafe destination path
- **WHEN** the selected folder, optional subfolder, or title would escape the Vault root
- **THEN** the system SHALL reject the request and SHALL not invoke the Obsidian CLI.

### Requirement: Obsidian CLI note creation
The system SHALL create missing target directories and invoke the Obsidian CLI to create the note with generated Markdown content.

#### Scenario: CLI succeeds
- **WHEN** the target path is safe and the Obsidian CLI exits with return code 0
- **THEN** the system SHALL report persistence success to the workflow.

#### Scenario: CLI fails
- **WHEN** the Obsidian CLI exits with a non-zero return code or cannot be executed
- **THEN** the system SHALL report a recoverable persistence error including the relevant stderr or exception summary.

### Requirement: Vault persistence diagnostics
The system SHALL log safe diagnostic metadata for target construction, directory creation, and Obsidian CLI note creation.

#### Scenario: Obsidian CLI succeeds
- **WHEN** the Obsidian CLI creates a note successfully
- **THEN** the system SHALL log the relative target path, Vault root, return code, and execution duration without logging generated Markdown content.

#### Scenario: Obsidian CLI fails
- **WHEN** the Obsidian CLI exits with a non-zero return code or cannot be executed
- **THEN** the system SHALL log the relative target path when available, Vault root, sanitized command shape, return code when available, duration when available, and truncated stdout or stderr.

#### Scenario: Target directory creation fails
- **WHEN** the system cannot create the target note directory
- **THEN** the system SHALL log the target parent directory and exception details while returning a recoverable persistence error.
