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

### Requirement: Ollama readiness validation
The system SHALL validate whether the configured Ollama API is reachable before normal program use and return a recoverable readiness result.

#### Scenario: Ollama is listening on startup
- **WHEN** the application starts and the configured Ollama API responds to the readiness check
- **THEN** the system SHALL record a technical success log containing the configured base URL and model without sending note content.

#### Scenario: Ollama is unavailable on startup
- **WHEN** the application starts and the configured Ollama API times out, refuses connection, or returns an unusable readiness response
- **THEN** the system SHALL record a technical warning with base URL, model, timeout, and error summary and SHALL expose a recoverable status to the interface.

### Requirement: Ollama request diagnostics
The system SHALL log safe diagnostic metadata for every Ollama synthesis request.

#### Scenario: Ollama request succeeds
- **WHEN** an Ollama synthesis request completes successfully
- **THEN** the system SHALL log base URL, model, timeout, HTTP status code, duration, raw input size, and response size without logging prompt text or generated Markdown.

#### Scenario: Ollama request fails
- **WHEN** an Ollama synthesis request times out, raises a request exception, returns a non-success status, returns malformed JSON, or returns unusable content
- **THEN** the system SHALL log the failure with safe context and stack trace or exception chain while returning a recoverable inference error.
