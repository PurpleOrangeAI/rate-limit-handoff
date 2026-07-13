"""Basic smoke tests for rate-limit-handoff."""

from __future__ import annotations

import datetime as dt
import json
import shlex
import tempfile
from pathlib import Path

import pytest

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
        assert sched.handoff_path == resolved_workspace / "handoff.md"
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


def test_schedule_auto_run_persists_before_spawning(monkeypatch, tmp_path):
    calls: list[str] = []

    monkeypatch.setattr(
        scheduler_module,
        "create_job",
        lambda **kwargs: calls.append("create_job") or tmp_path / "job.json",
    )
    monkeypatch.setattr(
        scheduler_module,
        "spawn_waiting_job",
        lambda path: calls.append("spawn_job") or 4242,
    )

    sched = LimitScheduler(workspace=tmp_path)
    result = sched.schedule(
        summary="Resume with Claude",
        reset_at="2099-07-13 16:00",
        model="claude",
        auto_run=True,
        command_argv=["claude", "-p", "Read handoff.md"],
    )

    assert result == 0
    assert calls == ["create_job", "spawn_job"]
    active = json.loads(
        (tmp_path / "second_brain" / "logs" / "active_handoff.json").read_text()
    )
    assert active["mode"] == "same"
    assert active["status"] == "waiting"


def test_cross_handoff_records_destination_before_execution(monkeypatch, tmp_path):
    observed: list[str] = []

    def fake_execute(path, wait=False):
        active = json.loads(
            (tmp_path / "second_brain" / "logs" / "active_handoff.json").read_text()
        )
        observed.append(str(active["current_model"]))
        return 0

    monkeypatch.setattr(
        scheduler_module,
        "create_job",
        lambda **kwargs: tmp_path / "job.json",
    )
    monkeypatch.setattr(scheduler_module, "execute_job", fake_execute)

    sched = LimitScheduler(workspace=tmp_path)
    result = sched.handoff(
        summary="Continue now",
        from_model="claude",
        to_model="codex",
        auto_run=True,
        command_argv=["codex", "exec", "Read handoff.md"],
    )

    assert result == 0
    assert observed == ["codex"]


def test_return_handoff_schedules_return_before_destination(monkeypatch, tmp_path):
    calls: list[str] = []

    def fake_create(**kwargs):
        calls.append(f"create:{kwargs['mode']}")
        return tmp_path / f"{kwargs['mode']}.json"

    monkeypatch.setattr(scheduler_module, "create_job", fake_create)
    monkeypatch.setattr(
        scheduler_module,
        "spawn_waiting_job",
        lambda path: calls.append("spawn:return") or 4242,
    )
    monkeypatch.setattr(
        scheduler_module,
        "execute_job",
        lambda path, wait=False: calls.append("execute:cross") or 0,
    )

    sched = LimitScheduler(workspace=tmp_path)
    result = sched.handoff(
        summary="Use Codex, then return",
        from_model="claude",
        to_model="codex",
        return_to="claude",
        return_at="2099-07-13 16:00",
        auto_run=True,
        command_argv=["codex", "exec", "Read handoff.md"],
        return_command_argv=["claude", "-p", "Read handoff.md"],
    )

    assert result == 0
    assert calls == [
        "create:return",
        "spawn:return",
        "create:cross",
        "execute:cross",
    ]
    active = json.loads(
        (tmp_path / "second_brain" / "logs" / "active_handoff.json").read_text()
    )
    assert active["mode"] == "return"
    assert active["current_model"] == "codex"
    assert active["return_to"] == "claude"


def test_resume_preference_changes_prompt(tmp_path, capsys):
    (tmp_path / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
    sched = LimitScheduler(workspace=tmp_path)

    result = sched.resume(prefer="claude")

    assert result == 0
    assert "Preferred model: claude" in capsys.readouterr().out


@pytest.mark.parametrize("mode", ["same", "cross", "return"])
def test_auto_run_requires_all_commands_before_workspace_mutation(tmp_path, mode):
    workspace = tmp_path / mode
    sched = LimitScheduler(workspace=workspace)

    with pytest.raises(ValueError, match="explicit .*command"):
        if mode == "same":
            sched.schedule(summary="Wait", auto_run=True, command_argv=[])
        elif mode == "cross":
            sched.handoff(
                summary="Continue elsewhere",
                from_model="claude",
                to_model="unknown-provider/model",
                auto_run=True,
                command_argv=[],
            )
        else:
            sched.handoff(
                summary="Continue and return",
                from_model="claude",
                to_model="unknown-provider/model",
                return_to="claude",
                return_at="2099-07-13 16:00",
                auto_run=True,
                command_argv=["new-provider", "continue"],
                return_command_argv=[],
            )

    assert not workspace.exists()


@pytest.mark.parametrize("mode", ["same", "cross"])
def test_unknown_model_is_preserved_but_sanitized_in_note_filename(
    monkeypatch, tmp_path, mode
):
    model = "../../unknown-provider/future-model"
    sched = LimitScheduler(workspace=tmp_path)
    monkeypatch.setattr(sched, "try_schedule_system_job", lambda *args: None)

    if mode == "same":
        result = sched.schedule(summary="Continue", model=model)
    else:
        monkeypatch.setattr(
            scheduler_module,
            "create_job",
            lambda **kwargs: tmp_path / "unknown-provider-job.json",
        )
        monkeypatch.setattr(scheduler_module, "execute_job", lambda path, wait=False: 0)
        result = sched.handoff(
            summary="Continue elsewhere",
            from_model="claude",
            to_model=model,
            auto_run=True,
            command_argv=["unknown-provider", "continue"],
        )

    assert result == 0
    active = json.loads(
        (tmp_path / "second_brain" / "logs" / "active_handoff.json").read_text()
    )
    assert active["current_model"] == model
    notes = list((tmp_path / "second_brain" / "inbox").glob("*.md"))
    assert len(notes) == 1
    assert notes[0].parent.resolve() == (tmp_path / "second_brain" / "inbox").resolve()
    assert model in notes[0].read_text(encoding="utf-8")
    assert not (tmp_path / "unknown-provider").exists()
