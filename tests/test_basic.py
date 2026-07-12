"""Basic smoke tests for rate-limit-handoff."""

from __future__ import annotations

import datetime as dt
import shlex
import tempfile
from pathlib import Path

import rate_limit_handoff.scheduler as scheduler_module
from rate_limit_handoff.models import MODELS, resolve_model
from rate_limit_handoff.scheduler import LimitScheduler


def test_models_registry():
    assert "claude" in MODELS
    assert "codex" in MODELS
    assert "antigravity" in MODELS
    assert resolve_model("claude-code") is not None
    assert resolve_model("agy") is not None
    assert resolve_model("nonexistent") is None


def test_parse_usage_codex():
    with tempfile.TemporaryDirectory() as tmp:
        sched = LimitScheduler(workspace=Path(tmp))
        text = "5h limit: [████░░░░] 18% left (resets 04:00) weekly 55%"
        parsed = sched.parse_usage_text(text)
        assert parsed["5h_remaining_pct"] == 18
        assert parsed["reset_hint"] == "04:00"
        assert parsed["source"] == "codex"


def test_parse_usage_agy():
    with tempfile.TemporaryDirectory() as tmp:
        sched = LimitScheduler(workspace=Path(tmp))
        text = "Individual quota reached. Resets in 2h15m"
        parsed = sched.parse_usage_text(text)
        assert "2h15m" in (parsed["reset_hint"] or "")
        assert parsed["source"] == "antigravity"


def test_next_reset_hhmm():
    with tempfile.TemporaryDirectory() as tmp:
        sched = LimitScheduler(workspace=Path(tmp), default_reset_hour=4, default_reset_minute=0)
        # Just ensure it returns a datetime without crashing
        r = sched.next_reset("04:00")
        assert r.hour == 4
        assert r.minute == 0


def test_schedule_creates_files():
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        sched = LimitScheduler(workspace=workspace)
        sched.schedule(
            summary="Test remaining work",
            reset_at="04:00",
            model="codex",
        )
        assert (workspace / "handoff.md").exists()
        notes = list((workspace / "second_brain" / "inbox").glob("*.md"))
        assert len(notes) >= 1


def test_update_only_records_active_checkpoint():
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        (workspace / "handoff.md").write_text(
            "# Session Handoff Document\n\n**Status:** Active\n",
            encoding="utf-8",
        )
        sched = LimitScheduler(workspace=workspace)

        sched.update_only("Capture current state", reset_at="23:59", model="codex")

        handoff = (workspace / "handoff.md").read_text(encoding="utf-8")
        assert "## Handoff Update" in handoff
        assert "**Status:** ACTIVE" in handoff
        assert "SCHEDULED" not in handoff
        assert "**Continuation:**" in handoff
        assert "after reset" not in handoff.lower()
        assert "limits have reset" not in handoff.lower()

        notes = list((workspace / "second_brain" / "inbox").glob("*.md"))
        assert len(notes) == 1
        assert "scheduled-handoff" not in notes[0].name
        note = notes[0].read_text(encoding="utf-8")
        assert note.startswith("# Handoff Update")
        assert "**Reference time:**" in note
        assert "## Continuation Command" in note
        assert "after 23:59" not in note


def test_existing_obsidian_vault_uses_canonical_directories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workspace = root / "artifact"
        vault = root / "vault"
        (vault / "00 Inbox").mkdir(parents=True)
        (vault / "10 Projects").mkdir()

        sched = LimitScheduler(workspace=workspace, second_brain_root=vault)

        resolved_workspace = workspace.resolve()
        resolved_vault = vault.resolve()
        assert sched.handoff == resolved_workspace / "handoff.md"
        assert sched.inbox == resolved_vault / "00 Inbox"
        assert sched.projects == resolved_vault / "10 Projects" / "ai-rate-limit-handoff"
        assert sched.second_brain_link == "10 Projects/ai-rate-limit-handoff/README"
        assert sched.logs == resolved_workspace / "second_brain" / "logs"
        assert sched.skills == resolved_workspace / "second_brain" / "system" / "skills"


def test_at_scheduler_does_not_invoke_a_shell(monkeypatch, tmp_path):
    calls = []

    monkeypatch.setattr(scheduler_module.shutil, "which", lambda name: "/usr/bin/at")

    def capture_run(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(scheduler_module.subprocess, "run", capture_run)

    malicious_summary = "$(touch /tmp/unsafe)"
    sched = LimitScheduler(workspace=tmp_path)
    sched.try_schedule_system_job(sched.now() + dt.timedelta(hours=1), malicious_summary)

    args, kwargs = calls[0]
    assert args[0][0] == "at"
    assert kwargs.get("shell") is not True
    assert kwargs["text"] is True
    expected_message = shlex.quote(f"Resume handoff: {malicious_summary}...")
    assert expected_message in kwargs["input"]
