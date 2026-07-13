from __future__ import annotations

import datetime as dt
import json
import subprocess
from typing import Any

import pytest

from rate_limit_handoff.continuity import HandoffState
from rate_limit_handoff.runner import (
    create_job,
    execute_job,
    parse_command,
    spawn_waiting_job,
)

NOW = dt.datetime(2026, 7, 13, 16, 0)


def returned_state() -> HandoffState:
    return HandoffState(
        mode="return",
        source_model="claude",
        current_model="claude",
        summary="Return for final review",
        status="returned",
        created_at=NOW,
        updated_at=NOW,
        return_to="claude",
        return_at=NOW,
    )


def test_parse_command_returns_argv_and_rejects_empty():
    assert parse_command('codex exec "Read handoff.md"') == [
        "codex",
        "exec",
        "Read handoff.md",
    ]
    with pytest.raises(ValueError, match="empty"):
        parse_command("   ")


def test_create_job_is_private_and_pending(tmp_path):
    path = create_job(
        logs_path=tmp_path / "second_brain" / "logs",
        workspace=tmp_path,
        mode="same",
        model="claude",
        run_at=NOW,
        argv=["python", "-c", "print('ok')"],
        transition=None,
        now=lambda: NOW,
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "pending"
    assert data["argv"] == ["python", "-c", "print('ok')"]
    assert path.stat().st_mode & 0o077 == 0


def test_execute_job_uses_no_shell_and_records_success(tmp_path):
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0)

    path = create_job(
        logs_path=tmp_path / "second_brain" / "logs",
        workspace=tmp_path,
        mode="cross",
        model="codex",
        run_at=NOW,
        argv=["codex", "exec", "Read handoff.md"],
        transition=None,
        now=lambda: NOW,
    )

    result = execute_job(path, wait=False, run=fake_run, clock=lambda: NOW)

    assert result == 0
    assert calls[0][0] == ["codex", "exec", "Read handoff.md"]
    assert calls[0][1]["shell"] is False
    assert calls[0][1]["cwd"] == tmp_path.resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "succeeded"
    assert data["exit_code"] == 0


def test_execute_job_applies_return_transition_before_command(tmp_path):
    observed: list[str] = []

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        active = json.loads(
            (tmp_path / "second_brain" / "logs" / "active_handoff.json").read_text(
                encoding="utf-8"
            )
        )
        observed.append(str(active["status"]))
        return subprocess.CompletedProcess(argv, 0)

    path = create_job(
        logs_path=tmp_path / "second_brain" / "logs",
        workspace=tmp_path,
        mode="return",
        model="claude",
        run_at=NOW,
        argv=["claude", "-p", "Read handoff.md"],
        transition=returned_state(),
        now=lambda: NOW,
    )

    execute_job(path, wait=False, run=fake_run, clock=lambda: NOW)

    assert observed == ["returned"]


def test_spawn_waiting_job_uses_module_runner_and_new_session(tmp_path):
    captured: dict[str, Any] = {}

    class Process:
        pid = 4242

    def fake_popen(argv: list[str], **kwargs: Any) -> Process:
        captured["argv"] = argv
        captured.update(kwargs)
        return Process()

    path = create_job(
        logs_path=tmp_path / "second_brain" / "logs",
        workspace=tmp_path,
        mode="same",
        model="claude",
        run_at=NOW,
        argv=["claude", "-p", "Continue"],
        transition=None,
        now=lambda: NOW,
    )

    pid = spawn_waiting_job(path, popen=fake_popen)

    assert pid == 4242
    assert captured["argv"][1:4] == [
        "-m",
        "rate_limit_handoff.runner",
        "--wait",
    ]
    assert captured["argv"][-2:] == ["--job", str(path.resolve())]
    assert captured["start_new_session"] is True
    assert captured["shell"] is False
