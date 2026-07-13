from __future__ import annotations

import datetime as dt
import json
import os
import stat
import subprocess
from typing import Any

import pytest

import rate_limit_handoff.runner as runner_module
from rate_limit_handoff.continuity import ACTIVE_START, HandoffState
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


def test_execute_job_persists_transition_failure_without_running_command(tmp_path):
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0)

    (tmp_path / "handoff.md").write_text(
        f"# Handoff\n\n{ACTIVE_START}\n",
        encoding="utf-8",
    )
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

    result = execute_job(path, wait=False, run=fake_run, clock=lambda: NOW)

    assert result == 1
    assert calls == []
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "failed"
    assert data["exit_code"] == 1
    assert "active chain markers" in data["error"]
    assert data["finished_at"] == NOW.isoformat()


def test_execute_job_records_nonzero_subprocess_exit(tmp_path):
    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 23)

    path = create_job(
        logs_path=tmp_path / "second_brain" / "logs",
        workspace=tmp_path,
        mode="same",
        model="python",
        run_at=NOW,
        argv=["python", "-c", "raise SystemExit(23)"],
        transition=None,
        now=lambda: NOW,
    )

    result = execute_job(path, wait=False, run=fake_run, clock=lambda: NOW)

    assert result == 23
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "failed"
    assert data["exit_code"] == 23
    assert data["error"] is None
    assert data["finished_at"] == NOW.isoformat()


def test_execute_job_records_oserror_as_exit_127(tmp_path):
    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise OSError("missing executable")

    path = create_job(
        logs_path=tmp_path / "second_brain" / "logs",
        workspace=tmp_path,
        mode="same",
        model="missing",
        run_at=NOW,
        argv=["missing-command"],
        transition=None,
        now=lambda: NOW,
    )

    result = execute_job(path, wait=False, run=fake_run, clock=lambda: NOW)

    assert result == 127
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "failed"
    assert data["exit_code"] == 127
    assert data["error"] == "missing executable"
    assert data["finished_at"] == NOW.isoformat()


def test_execute_job_waits_exact_positive_delay_then_executes(tmp_path):
    sleeps: list[float] = []
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0)

    path = create_job(
        logs_path=tmp_path / "second_brain" / "logs",
        workspace=tmp_path,
        mode="same",
        model="python",
        run_at=NOW + dt.timedelta(seconds=45),
        argv=["python", "-c", "print('ok')"],
        transition=None,
        now=lambda: NOW,
    )

    result = execute_job(
        path,
        run=fake_run,
        sleeper=sleeps.append,
        clock=lambda: NOW,
    )

    assert result == 0
    assert sleeps == [45.0]
    assert calls == [["python", "-c", "print('ok')"]]


def test_spawn_waiting_job_uses_module_runner_and_new_session(tmp_path):
    captured: dict[str, Any] = {}

    class Process:
        pid = 4242

    def fake_popen(argv: list[str], **kwargs: Any) -> Process:
        captured["argv"] = argv
        captured.update(kwargs)
        stream = kwargs["stdout"]
        captured["log_mode"] = stat.S_IMODE(os.fstat(stream.fileno()).st_mode)
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
    assert captured["log_mode"] == 0o600
    assert captured["stdin"] is subprocess.DEVNULL
    assert captured["stderr"] is subprocess.STDOUT
    assert captured["close_fds"] is True


def test_create_job_fsyncs_around_atomic_replace(tmp_path, monkeypatch):
    events: list[str] = []
    real_replace = runner_module.os.replace

    def fake_fsync(descriptor: int) -> None:
        events.append("fsync")

    def fake_replace(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
        events.append("replace")
        real_replace(source, destination)

    monkeypatch.setattr(runner_module.os, "fsync", fake_fsync)
    monkeypatch.setattr(runner_module.os, "replace", fake_replace)

    create_job(
        logs_path=tmp_path / "second_brain" / "logs",
        workspace=tmp_path,
        mode="same",
        model="python",
        run_at=NOW,
        argv=["python", "-c", "print('ok')"],
        transition=None,
        now=lambda: NOW,
    )

    assert events == ["fsync", "replace", "fsync"]
