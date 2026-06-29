## Purpose

Defines remote Ollama prompt construction, request behavior, response extraction, and Markdown cleanup for atomic note synthesis.

## Requirements

### Requirement: Ollama prompt construction
The system SHALL construct a deterministic prompt for converting raw input into a clear atomic technical note in Markdown.

#### Scenario: Prompt includes user text
- **WHEN** the system receives raw note text for synthesis
- **THEN** the Ollama request prompt SHALL include the system instruction for atomic-note summarization and the exact user-provided text.

### Requirement: Ollama generate request
The system SHALL call the configured Ollama `/api/generate` endpoint with model `qwen2.5:3b`, `stream` set to false, `temperature` set to 0.1, and `num_ctx` set to 4096 unless overridden by configuration.

#### Scenario: Request payload is sent
- **WHEN** synthesis is requested with valid text
- **THEN** the system SHALL send a JSON POST request containing the configured model, prompt, stream flag, and options.

#### Scenario: Ollama returns non-success status
- **WHEN** the Ollama API returns a non-2xx response or times out
- **THEN** the system SHALL return a recoverable inference error and SHALL not produce note content for persistence.

### Requirement: Ollama response extraction and cleanup
The system SHALL extract the `response` field from the Ollama JSON response and clean unwanted Markdown code-fence wrappers before returning content to the workflow.

#### Scenario: Response field exists
- **WHEN** Ollama returns JSON with a string `response` field
- **THEN** the system SHALL return the cleaned Markdown string.

#### Scenario: Response field is invalid
- **WHEN** Ollama returns malformed JSON or omits a usable `response` field
- **THEN** the system SHALL return a recoverable response-validation error.
