## Context

atomicOS is a local desktop Flet application that orchestrates note synthesis through a configured Ollama HTTP endpoint and persists generated Markdown through the Obsidian CLI. Current user-visible logs are appended to the UI only, are not persisted, and do not include stack traces or enough technical context to diagnose failures across startup, Ollama, workflow orchestration, and Vault persistence.

The implementation should improve diagnostics without turning user note content into log data. Raw input, generated Markdown, secrets, and full CLI `--content` values must remain out of technical logs.

## Goals / Non-Goals

**Goals:**

- Add standard Python logging for technical diagnostics with useful context and stack traces.
- Keep user-visible UI logs concise while writing richer technical logs to logger sinks.
- Correlate each synthesis attempt with a generated `run_id`.
- Add safe diagnostics for Ollama requests, Obsidian CLI executions, workflow failures, and startup/configuration failures.
- Check whether the configured AI API is reachable when the interface starts and warn the user if it is unavailable.
- Preserve existing note creation behavior and user workflow.

**Non-Goals:**

- Add external observability dependencies or remote telemetry.
- Log raw notes, full generated Markdown, API secrets, or full CLI content arguments.
- Replace Flet UI logging with a new UI framework.
- Change the Ollama generation endpoint, model defaults, or Obsidian persistence contract.

## Decisions

### Use Python standard-library logging

Use `logging` instead of adding `loguru`, `structlog`, `winston`, or another dependency. This keeps the application lightweight and satisfies the requirement for standard Python logging. Configure a simple app logger namespace such as `atomicos` from startup, with console output as the minimum sink.

Alternative considered: add structured JSON logging. Rejected for this change because the current app is local desktop software and the immediate need is diagnosability, not centralized ingestion.

### Separate user-facing messages from technical diagnostics

Continue using the existing UI log callback for concise user-facing messages. Add module loggers for technical details, including exception stack traces through `logger.exception(...)` where failures are unexpected.

Alternative considered: route all logs through the UI panel. Rejected because stack traces and transport details would clutter the interface and could expose sensitive data.

### Generate a `run_id` per workflow execution

Create a short unique identifier when a synthesis run starts and include it in workflow, Ollama, and Vault logs. The UI can show the `run_id` in start/error messages so users can match visible errors to technical logs.

Alternative considered: use timestamps only. Rejected because multiple quick retries can produce overlapping logs that are hard to correlate.

### Add safe diagnostic context at integration boundaries

Ollama logs should include URL, model, timeout, status code when available, duration, raw input byte/character size, and response size. Vault logs should include target path, Vault root, sanitized command shape, return code, duration, and truncated stdout/stderr. Neither boundary should log raw prompt text, generated Markdown, or full `--content` values.

Alternative considered: log complete request payloads and CLI commands. Rejected due to privacy and secret/content leakage risk.

### Add startup AI readiness check in the UI path

Expose a lightweight Ollama client readiness method and call it during page initialization. The check should use a simple configured API call with a short timeout and report `[WARN]` in the UI if unavailable. A failed check should warn the user early, but it should not prevent Vault folder loading or permanently block the interface by itself because Ollama could become available later before the user clicks synthesize.

Alternative considered: fail application boot when AI is unavailable. Rejected because this is a desktop workflow and the user benefits from seeing the UI plus a clear warning.

## Risks / Trade-offs

- Technical logs could accidentally include sensitive note content if command or payload logging is naive. → Centralize sanitization/truncation helpers and avoid logging `prompt`, `markdown`, or `--content` values.
- Startup health checks could slow page initialization if they use the generation timeout. → Use a short readiness timeout separate from synthesis timeout or cap the startup check duration.
- Threaded workflow exceptions can leave the UI button disabled. → Wrap background execution in `try/except/finally`, log unexpected exceptions with stack trace, and always reset busy state in `finally`.
- Console-only logs may still be lost when launched outside a terminal. → Start with console logging and leave file logging as optional configuration if existing project patterns support it during implementation.
