## 1. Project Setup

- [x] 1.1 Create the Python application structure with modules for configuration, UI, workflow orchestration, Ollama client, Obsidian Vault manager, and tests.
- [x] 1.2 Add project dependency metadata for Flet, requests, pytest, and any formatting or test tooling selected for this repository.
- [x] 1.3 Implement runtime configuration loading for Vault root, Ollama base URL, model name, timeout, generation options, and Obsidian CLI executable.

## 2. Remote Ollama Synthesis

- [x] 2.1 Implement prompt construction for atomic technical notes using the configured model options.
- [x] 2.2 Implement the Ollama `/api/generate` HTTP client with timeout handling, non-2xx error handling, and JSON response validation.
- [x] 2.3 Implement Markdown response cleanup for code-fence wrappers and empty or malformed responses.
- [x] 2.4 Add unit tests for payload construction, successful response extraction, timeout/non-2xx errors, malformed JSON, and cleanup behavior.

## 3. Obsidian Vault Integration

- [x] 3.1 Implement Vault folder discovery returning relative directory paths from the configured Vault root.
- [x] 3.2 Implement safe target path construction from selected folder, optional subfolder, and title, rejecting absolute paths and parent traversal.
- [x] 3.3 Implement directory creation and Obsidian CLI note creation using subprocess argument arrays rather than shell-concatenated commands.
- [x] 3.4 Add unit tests for nested folder discovery, unavailable Vault roots, valid nested destinations, unsafe paths, CLI success, and CLI failure.

## 4. Workflow Orchestration

- [x] 4.1 Implement a workflow service that validates required inputs before calling inference or persistence.
- [x] 4.2 Implement progress logging callbacks for start, inference wait, persistence attempt, success, and recoverable failures.
- [x] 4.3 Implement dependency-injected orchestration using fake inference and Vault services in tests.
- [x] 4.4 Add workflow tests for successful note creation, missing inputs, inference failure, persistence failure, editor-clearing signal, and retry-safe input preservation.

## 5. Flet Desktop Interface

- [x] 5.1 Build the dark split-screen layout with raw-text editor, byte counter, target title, folder dropdown, optional subfolder field, logs panel, and primary synthesize button.
- [x] 5.2 Load Vault folders on page initialization and populate the dropdown, logging configuration or filesystem errors when discovery fails.
- [x] 5.3 Wire the synthesize button to the workflow service with duplicate-submit prevention and button re-enable on success or failure.
- [x] 5.4 Run synthesis and persistence off the UI event path using Flet-compatible async execution or a worker thread while keeping log updates visible.

## 6. Validation and Documentation

- [x] 6.1 Add a short README or run instructions covering configuration values, Ollama server requirements, and Obsidian CLI expectations.
- [x] 6.2 Run the automated test suite and fix failures.
- [x] 6.3 Run a local smoke test with mocked services or a dry-run mode to verify UI state transitions without requiring the real Vault or Ollama server.
- [x] 6.4 Document the remaining machine-specific values needed for a real end-to-end test: Vault root, Ollama LAN URL, and Obsidian CLI command compatibility.
