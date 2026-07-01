# atomicOS

atomicOS is a local Python/Flet desktop app that turns rough notes into atomic Markdown notes and persists them into an Obsidian Vault through the Obsidian CLI.

## Requirements

- Python 3.11+
- Windows desktop runtime
- Reachable Ollama server on the LAN with `qwen2.5:3b` installed
- Obsidian CLI available as `obsidian` or configured with `ATOMICOS_OBSIDIAN_EXECUTABLE`
- Existing Obsidian Vault folder

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## Configuration

Set values with environment variables or create `atomicos.toml` in the repository root.

Environment variables:

- `ATOMICOS_VAULT_ROOT`: absolute path to the Obsidian Vault
- `ATOMICOS_OBSIDIAN_EXECUTABLE`: Obsidian CLI executable, defaults to `obsidian`
- `ATOMICOS_OLLAMA_BASE_URL`: Ollama base URL, for example `http://192.168.1.50:11434`
- `ATOMICOS_OLLAMA_MODEL`: model name, defaults to `qwen2.5:3b`
- `ATOMICOS_OLLAMA_TIMEOUT`: request timeout in seconds, defaults to `120`
- `ATOMICOS_OLLAMA_TEMPERATURE`: generation temperature, defaults to `0.1`
- `ATOMICOS_OLLAMA_NUM_CTX`: context window, defaults to `4096`

Example `atomicos.toml`:

```toml
[app]
vault_root = "C:/Users/marce/Documents/ObsidianVault"
obsidian_executable = "obsidian"

[ollama]
base_url = "http://192.168.1.50:11434"
model = "qwen2.5:3b"
timeout_seconds = 120
temperature = 0.1
num_ctx = 4096
```

## Run

```powershell
atomicos
```

or:

```powershell
python -m atomicos.main
```

## Dry-Run Smoke Test

The dry-run smoke test validates workflow state transitions without requiring a real Vault, Ollama server, or Obsidian CLI.

```powershell
python scripts\smoke_dry_run.py
```

Expected output includes `[INFO]`, `[WAIT]`, `[OK]`, `success=True`, and `clear_editor=True`.

## Real End-to-End Values Needed

Before a real end-to-end run, confirm these machine-specific values:

- The exact Windows Vault root path for `ATOMICOS_VAULT_ROOT`
- The Pop!_OS Ollama LAN URL and port for `ATOMICOS_OLLAMA_BASE_URL`
- Whether this machine's Obsidian CLI command is `obsidian` and supports `obsidian create path="..." content="..."`

## Tests

```powershell
python -m pytest
```
