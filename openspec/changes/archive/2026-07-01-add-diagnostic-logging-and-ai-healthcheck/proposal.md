## Why

The application currently shows basic UI messages, but it does not persist technical logs with enough context to diagnose where and why failures happen. Adding structured diagnostic logging and an Ollama readiness check will make startup and runtime failures visible without exposing sensitive note content.

## What Changes

- Add Python standard-library logging for technical diagnostics, including exception stack traces for unexpected failures.
- Create a `run_id` for each synthesis execution and include it in workflow, Ollama, and Vault diagnostics.
- Improve Ollama diagnostics with base URL, model, timeout, status code, request duration, and input/output sizes without logging prompt text or generated note content.
- Improve Vault/Obsidian CLI diagnostics with target path, return code, execution duration, and truncated stdout/stderr without logging full note content.
- Handle configuration and boot errors with clear technical logs and user-visible messages.
- Add an application-start readiness check that calls the configured AI API before normal use and warns in the interface if the API is not listening.
- No breaking changes to user-facing workflow inputs or note persistence behavior.

## Capabilities

### New Capabilities
- `operational-diagnostics`: Covers persistent technical logging, run correlation, safe diagnostic context, and exception capture.

### Modified Capabilities
- `remote-ollama-synthesis`: Adds AI API readiness validation and diagnostic metadata requirements around Ollama calls.
- `obsidian-vault-integration`: Adds safe diagnostic metadata requirements around Obsidian CLI execution failures.
- `responsive-flet-interface`: Adds startup warning behavior when the configured AI API is unavailable.
- `desktop-note-workflow`: Adds run correlation and unexpected-error reporting requirements for each synthesis execution.

## Impact

- Affected code: `src/atomicos/main.py`, `src/atomicos/config.py`, `src/atomicos/ui.py`, `src/atomicos/workflow.py`, `src/atomicos/ollama.py`, and `src/atomicos/vault.py`.
- Affected tests: workflow, Ollama client, Vault manager, configuration boot paths, and UI startup behavior may need new or updated tests.
- Dependencies: no required third-party logging dependency; use Python `logging`.
- Security/privacy: diagnostics must avoid logging raw note text, full generated Markdown, secrets, or full CLI content arguments.
