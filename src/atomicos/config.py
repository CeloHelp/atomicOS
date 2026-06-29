"""Runtime configuration for atomicOS."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib
from typing import Any


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:3b"
    timeout_seconds: float = 120.0
    temperature: float = 0.1
    num_ctx: int = 4096


@dataclass(frozen=True)
class AppConfig:
    vault_root: Path
    obsidian_executable: str = "obsidian"
    ollama: OllamaConfig = OllamaConfig()


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load config from defaults, optional TOML, and environment overrides."""

    data: dict[str, Any] = {}
    path = Path(config_path or os.getenv("ATOMICOS_CONFIG", "atomicos.toml"))
    if path.exists():
        with path.open("rb") as file:
            data = tomllib.load(file)

    app_data = data.get("app", {})
    ollama_data = data.get("ollama", {})

    vault_root = os.getenv("ATOMICOS_VAULT_ROOT") or app_data.get("vault_root") or ""
    obsidian_executable = (
        os.getenv("ATOMICOS_OBSIDIAN_EXECUTABLE")
        or app_data.get("obsidian_executable")
        or "obsidian"
    )

    ollama = OllamaConfig(
        base_url=str(os.getenv("ATOMICOS_OLLAMA_BASE_URL") or ollama_data.get("base_url") or "http://localhost:11434"),
        model=str(os.getenv("ATOMICOS_OLLAMA_MODEL") or ollama_data.get("model") or "qwen2.5:3b"),
        timeout_seconds=_float_value(
            os.getenv("ATOMICOS_OLLAMA_TIMEOUT") or ollama_data.get("timeout_seconds"),
            default=120.0,
        ),
        temperature=_float_value(
            os.getenv("ATOMICOS_OLLAMA_TEMPERATURE") or ollama_data.get("temperature"),
            default=0.1,
        ),
        num_ctx=_int_value(
            os.getenv("ATOMICOS_OLLAMA_NUM_CTX") or ollama_data.get("num_ctx"),
            default=4096,
        ),
    )

    return AppConfig(
        vault_root=Path(vault_root).expanduser(),
        obsidian_executable=str(obsidian_executable),
        ollama=ollama,
    )


def _float_value(value: Any, default: float) -> float:
    if value in (None, ""):
        return default
    return float(value)


def _int_value(value: Any, default: int) -> int:
    if value in (None, ""):
        return default
    return int(value)
