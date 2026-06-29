## ADDED Requirements

### Requirement: Split-screen desktop layout
The system SHALL present a dark retro-futurist split-screen interface with a raw-text editor on the left and metadata, folder selection, optional subfolder input, and logs on the right.

#### Scenario: Application opens
- **WHEN** the desktop application loads
- **THEN** the UI SHALL show the text editor, target title field, folder dropdown, optional subfolder field, log panel, and primary synthesize button.

### Requirement: Initial folder loading
The system SHALL load Vault folder options during page initialization and populate the folder dropdown from the Vault manager.

#### Scenario: Folder discovery succeeds on load
- **WHEN** the UI initializes and folder discovery succeeds
- **THEN** the folder dropdown SHALL contain the discovered relative Vault folders.

#### Scenario: Folder discovery fails on load
- **WHEN** the UI initializes and folder discovery fails
- **THEN** the log panel SHALL show the configuration or filesystem error and the synthesize action SHALL remain unavailable until a valid destination can be selected.

### Requirement: Non-blocking action state
The system SHALL prevent duplicate submissions and keep the UI responsive while synthesis and persistence are running.

#### Scenario: User clicks synthesize
- **WHEN** the user triggers synthesis with valid inputs
- **THEN** the primary button SHALL become disabled before backend work starts and SHALL become enabled again after success or failure.

#### Scenario: Backend work is waiting
- **WHEN** the workflow is awaiting Ollama inference or Obsidian persistence
- **THEN** the UI SHALL continue updating visible logs and SHALL not freeze due to blocking work on the UI event path.
