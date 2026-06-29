## Context

atomicOS will be a local desktop assistant for transforming rough notes into structured atomic notes. The desktop app runs on Windows, owns the UI and filesystem orchestration, calls a LAN Ollama server running `qwen2.5:3b` on Pop!_OS for inference, and persists the generated Markdown into the user's Obsidian Vault through filesystem operations and the Obsidian CLI.

The repository currently contains planning infrastructure but no application implementation. The first implementation should therefore establish a small modular Python codebase rather than a broad framework. The architecture should keep UI, workflow orchestration, network inference, and Vault persistence separated so each module can be tested independently and later swapped, for example by replacing Ollama with another local inference backend.

## Goals / Non-Goals

**Goals:**

- Provide a Python/Flet desktop interface for raw note input, target title, Vault folder selection, optional subfolder entry, action triggering, and operational logs.
- Execute the full note workflow without freezing the UI while remote inference or disk operations are in progress.
- Generate deterministic atomic-note Markdown from raw text using the remote Ollama API.
- Persist generated content into the selected Obsidian Vault path using safe path handling and Obsidian CLI invocation.
- Keep the implementation modular with clear boundaries between presentation, use case orchestration, network client, and Vault manager.
- Include tests for prompt creation, response cleanup, validation, path handling, and workflow success/failure behavior where practical.

**Non-Goals:**

- Building a plugin for Obsidian.
- Supporting cloud LLM providers in the first version.
- Implementing multi-user accounts, synchronization, or remote storage.
- Implementing a full knowledge graph, semantic search, or note deduplication engine.
- Packaging installers for distribution beyond a locally runnable desktop app.

## Decisions

### Decision: Use a modular monolith in Python

The first version will use one Python application with separate modules for UI, workflow orchestration, Ollama access, Vault integration, configuration, and logging. This keeps deployment simple while preserving single responsibility boundaries.

Alternatives considered:
- Multiple processes or services: rejected because the app's first version does not need distributed local components beyond the existing Ollama server.
- A web app frontend plus API backend: rejected because the product target is a desktop utility with local Vault access.

### Decision: Use Flet for the desktop UI

Flet provides a Python-native path to a desktop UI without adding a JavaScript frontend stack. It allows direct integration with Python services and is sufficient for the split-screen editor, metadata panel, logs, and action button.

Alternatives considered:
- Tkinter: simpler but less suitable for the requested polished terminal-style interface.
- Electron: flexible but would add a Node/JS stack and more packaging complexity.

### Decision: Keep inference behind an `IAClient` abstraction

The UI and workflow should depend on an interface-like client contract rather than constructing HTTP requests directly. The concrete Ollama client will build the prompt, send POST requests to `/api/generate`, validate responses, and return clean Markdown.

Alternatives considered:
- Inline HTTP calls in UI callbacks: rejected because it couples presentation to infrastructure and makes tests brittle.
- A generic plugin system: rejected as premature for one inference backend.

### Decision: Use bounded background work for long operations

The synthesize action will disable the button, log progress, then run network and disk work off the UI event path using Flet-compatible async execution or a worker thread. UI updates should be marshalled back through safe callbacks.

Alternatives considered:
- Blocking the click handler: rejected because it freezes the app during inference and file writes.
- Full job queue: rejected as overbuilt for a single-user desktop action.

### Decision: Persist notes through a Vault manager plus Obsidian CLI

The Vault manager will discover folders, normalize user-selected relative paths, create missing directories, and invoke `obsidian note:create` with the generated content. The module will validate subprocess results before reporting success.

Alternatives considered:
- Direct Markdown file writes only: simpler, but does not honor the requested Obsidian CLI integration.
- Obsidian API/plugin automation: rejected because it requires an Obsidian-side extension.

### Decision: Use explicit configuration

Runtime settings such as Vault root, Ollama base URL, model, timeout, temperature, context size, and Obsidian executable should be loaded from environment variables or a small local config file with sane defaults where possible.

Alternatives considered:
- Hardcoded paths and URLs: rejected because both the Vault location and LAN host vary by machine.
- Complex settings database: rejected as unnecessary for local setup.

## Risks / Trade-offs

- Ollama server unavailable or slow -> expose clear timeout and connection errors in logs, keep the button re-enabled after failure, and make the base URL configurable.
- Obsidian CLI not installed or not on PATH -> validate subprocess errors and return an actionable log message.
- Unsafe or invalid note paths -> normalize relative paths, reject absolute paths and parent traversal, and sanitize titles for filesystem/CLI compatibility.
- Large pasted inputs exceed model context -> enforce or warn on byte/character count and set `num_ctx` explicitly.
- Generated Markdown contains unwanted fences or wrapper text -> centralize response cleanup and test common cleanup cases.
- Threaded work updates UI unsafely -> keep UI mutation in a small callback/logging adapter owned by the presentation layer.
- Shell quoting issues on Windows -> call subprocess with argument arrays rather than shell-concatenated strings.

## Migration Plan

1. Add the Python project structure, configuration loading, and dependency definitions.
2. Implement and test the Ollama client and Markdown cleanup in isolation.
3. Implement and test the Obsidian Vault manager with subprocess calls mockable in tests.
4. Implement the workflow orchestration service with dependency injection for the client and Vault manager.
5. Implement the Flet UI and wire it to the workflow service.
6. Run local validation with mocked services first, then a manual smoke test against the real Ollama server and Obsidian CLI.

Rollback is simple for the first version: remove the new app modules and OpenSpec change if implementation is abandoned before release. No persisted schema migration is introduced.

## Open Questions

- What exact Vault root path should be used on the target Windows machine?
- What is the final LAN URL and port for the Pop!_OS Ollama server?
- Is the installed Obsidian CLI command exactly `obsidian`, and does it accept `note:create` with the desired flags on this machine?
