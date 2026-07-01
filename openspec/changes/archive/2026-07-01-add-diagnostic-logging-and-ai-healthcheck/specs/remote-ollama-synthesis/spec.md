## ADDED Requirements

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
