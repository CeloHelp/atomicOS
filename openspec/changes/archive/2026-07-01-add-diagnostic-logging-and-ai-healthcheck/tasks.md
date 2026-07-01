## 1. Logging Foundation

- [x] 1.1 Add a standard Python logging setup for the `atomicos` logger namespace during application startup.
- [x] 1.2 Add safe diagnostic helpers for truncating uncontrolled output and representing commands without sensitive `--content` values.
- [x] 1.3 Add tests or assertions that sensitive note content and generated Markdown are not emitted by diagnostic helpers.

## 2. Workflow Correlation and Exception Handling

- [x] 2.1 Generate a unique `run_id` for each synthesis workflow execution.
- [x] 2.2 Include `run_id` in workflow phase technical logs for validation, inference start, persistence start, success, and recoverable failure.
- [x] 2.3 Catch unexpected workflow or background-thread exceptions with `logger.exception(...)`, show a concise UI error, and always re-enable the synthesize button.
- [x] 2.4 Update workflow tests to cover recoverable failure logging, unexpected failure handling, and editor retry behavior.

## 3. Ollama Readiness and Request Diagnostics

- [x] 3.1 Add a lightweight Ollama readiness method that validates the configured API with a short timeout and no note content.
- [x] 3.2 Log readiness success or failure with base URL, model, timeout, duration, and safe error summary.
- [x] 3.3 Log synthesis request diagnostics with base URL, model, timeout, status code, duration, raw input size, and response size without logging prompt text or generated Markdown.
- [x] 3.4 Update Ollama client tests for readiness success, readiness failure, request success diagnostics, timeout diagnostics, HTTP failure diagnostics, malformed JSON, and unusable content.

## 4. Vault and Obsidian CLI Diagnostics

- [x] 4.1 Log target path, Vault root, directory creation failures, and exception details during target preparation.
- [x] 4.2 Log sanitized Obsidian CLI execution metadata including command shape, return code, duration, and truncated stdout/stderr.
- [x] 4.3 Ensure generated Markdown and complete `--content` values are never logged for CLI execution.
- [x] 4.4 Update Vault tests for successful CLI diagnostics, non-zero return diagnostics, execution failure diagnostics, and truncation behavior.

## 5. Startup and UI Feedback

- [x] 5.1 Wrap configuration loading and app startup with technical logging for boot/configuration errors.
- [x] 5.2 Call the Ollama readiness check during Flet page initialization before or alongside folder loading.
- [x] 5.3 Show a concise `[OK]` or `[WARN]` message in the UI log panel for AI readiness without blocking Vault folder loading solely due to AI unavailability.
- [x] 5.4 Update UI-level tests or smoke coverage to verify startup warnings and successful readiness messages where feasible.

## 6. Verification

- [x] 6.1 Run the full automated test suite with `python -m pytest`.
- [x] 6.2 Run `python scripts\smoke_dry_run.py` to confirm the dry-run workflow still succeeds.
- [x] 6.3 Manually verify `python -m atomicos.main` with a bad `ATOMICOS_OLLAMA_BASE_URL` shows an AI warning in the UI and records technical diagnostics.
