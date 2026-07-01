"""Flet desktop interface for atomicOS."""

from __future__ import annotations

from datetime import datetime
from threading import Thread

import flet as ft

from atomicos.config import AppConfig
from atomicos.diagnostics import get_logger
from atomicos.ollama import OllamaClient, ReadinessResult
from atomicos.vault import VaultManager
from atomicos.workflow import NoteWorkflow, WorkflowInput, WorkflowResult


logger = get_logger("ui")


def _border_all(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def launch_app(config: AppConfig) -> None:
    ft.app(target=lambda page: build_page(page, config))


def build_page(page: ft.Page, config: AppConfig) -> None:
    page.title = "atomicOS"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#05070a"
    page.padding = 20

    vault = VaultManager(config.vault_root, config.obsidian_executable)
    ollama = OllamaClient(config.ollama)

    raw_editor = ft.TextField(
        label="RAW INPUT",
        hint_text="Cole aqui suas anotações brutas...",
        multiline=True,
        min_lines=22,
        max_lines=22,
        border_color="#1fffe0",
        color="#d6fff8",
        cursor_color="#1fffe0",
        text_style=ft.TextStyle(font_family="Consolas", size=14),
        on_change=lambda event: update_byte_counter(),
    )
    byte_counter = ft.Text("0 bytes", color="#6dfacb", font_family="Consolas", size=12)
    title_field = ft.TextField(label="Target title", border_color="#37556a", color="#d6fff8")
    folder_dropdown = ft.Dropdown(label="Vault folder", options=[], border_color="#37556a")
    subfolder_field = ft.TextField(label="Optional subfolder", border_color="#37556a", color="#d6fff8")
    log_panel = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    synthesize_button = ft.ElevatedButton("SYNTHESIZE", icon=ft.Icons.AUTO_AWESOME)

    def append_log(message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_panel.controls.append(
            ft.Text(f"{timestamp} {message}", color="#a9fff0", font_family="Consolas", size=12)
        )
        page.update()

    def update_byte_counter() -> None:
        byte_counter.value = f"{len((raw_editor.value or '').encode('utf-8'))} bytes"
        page.update()

    def set_busy(is_busy: bool) -> None:
        synthesize_button.disabled = is_busy or not bool(folder_dropdown.options)
        synthesize_button.text = "WORKING..." if is_busy else "SYNTHESIZE"
        page.update()

    def load_folders() -> None:
        try:
            folders = vault.list_folders()
        except Exception as exc:  # noqa: BLE001 - UI must surface concise recoverable startup errors.
            folder_dropdown.options = []
            synthesize_button.disabled = True
            append_log(f"[ERROR] {exc}")
            return

        folder_dropdown.options = [ft.dropdown.Option(folder) for folder in folders]
        if folders:
            folder_dropdown.value = folders[0]
            synthesize_button.disabled = False
            append_log(f"[OK] {len(folders)} pastas carregadas do Vault")
        else:
            synthesize_button.disabled = True
            append_log("[ERROR] Nenhuma pasta encontrada no Vault configurado")
        page.update()

    def check_ai_readiness() -> None:
        try:
            result = ollama.check_readiness()
        except Exception:  # noqa: BLE001 - startup diagnostics should warn, not block Vault loading.
            logger.exception("Unexpected AI readiness check failure")
            result = ReadinessResult(False, "AI readiness check failed unexpectedly")
        append_log(format_readiness_log(result))

    def run_workflow() -> None:
        try:
            workflow = NoteWorkflow(ollama, vault, append_log)
            result: WorkflowResult = workflow.run(
                WorkflowInput(
                    raw_text=raw_editor.value or "",
                    title=title_field.value or "",
                    selected_folder=folder_dropdown.value or "",
                    optional_subfolder=subfolder_field.value or "",
                )
            )
            if result.clear_editor:
                raw_editor.value = ""
                update_byte_counter()
        except Exception:  # noqa: BLE001 - background thread must not leave the UI busy forever.
            logger.exception("Unexpected background workflow failure")
            append_log("[ERROR] Falha inesperada durante a sintese. Consulte os logs tecnicos.")
        finally:
            set_busy(False)

    def on_synthesize(_: ft.ControlEvent) -> None:
        if synthesize_button.disabled:
            return
        set_busy(True)
        Thread(target=run_workflow, daemon=True).start()

    synthesize_button.on_click = on_synthesize
    synthesize_button.disabled = True

    left_panel = ft.Container(
        expand=3,
        padding=16,
        border=_border_all(1, "#12333a"),
        bgcolor="#071014",
        content=ft.Column(
            [
                ft.Text("atomicOS // capture", color="#1fffe0", font_family="Consolas", size=18),
                raw_editor,
                byte_counter,
            ],
            expand=True,
        ),
    )
    right_panel = ft.Container(
        expand=2,
        padding=16,
        border=_border_all(1, "#243040"),
        bgcolor="#090b12",
        content=ft.Column(
            [
                ft.Text("metadata", color="#ff4fd8", font_family="Consolas", size=18),
                title_field,
                folder_dropdown,
                subfolder_field,
                synthesize_button,
                ft.Divider(color="#243040"),
                ft.Text("logs", color="#6dfacb", font_family="Consolas", size=14),
                ft.Container(content=log_panel, expand=True, bgcolor="#030507", padding=10),
            ],
            expand=True,
        ),
    )

    page.add(ft.Row([left_panel, right_panel], expand=True, spacing=16))
    check_ai_readiness()
    load_folders()


def format_readiness_log(result: ReadinessResult) -> str:
    if result.available:
        return "[OK] Backend de IA acessivel"
    return "[WARN] Backend de IA indisponivel; a sintese pode falhar ate iniciar ou reconfigurar o Ollama"
