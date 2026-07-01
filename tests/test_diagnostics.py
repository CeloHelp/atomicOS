from __future__ import annotations

from atomicos.diagnostics import CONTENT_PLACEHOLDER, sanitize_command, truncate_value


def test_sanitize_command_omits_content_value():
    secret_markdown = "# Private note\nraw sensitive generated markdown"

    sanitized = sanitize_command(["obsidian", "create", "path=Folder/Note.md", "--content", secret_markdown])

    assert sanitized == ["obsidian", "create", "path=Folder/Note.md", "--content", CONTENT_PLACEHOLDER]
    assert secret_markdown not in " ".join(sanitized)


def test_sanitize_command_omits_content_assignment():
    secret_markdown = "# Private note\nraw sensitive generated markdown"

    sanitized = sanitize_command(["obsidian", "create", "path=Folder/Note.md", f"content={secret_markdown}"])

    assert sanitized == ["obsidian", "create", "path=Folder/Note.md", f"content={CONTENT_PLACEHOLDER}"]
    assert secret_markdown not in " ".join(sanitized)


def test_truncate_value_limits_uncontrolled_output():
    output = "x" * 20

    truncated = truncate_value(output, limit=8)

    assert truncated.startswith("xxxxxxxx")
    assert "truncated 12 chars" in truncated
    assert len(truncated) < len(output) + 20
