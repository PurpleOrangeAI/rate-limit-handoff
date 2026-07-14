"""Explicit local command jobs for rate-limit-handoff."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from .continuity import ContinuityStore, HandoffState

RunCallable = Callable[..., subprocess.CompletedProcess[Any]]
PopenCallable = Callable[..., Any]


def parse_command(command: str) -> list[str]:
    argv = shlex.split(command)
    if not argv:
        raise ValueError("command cannot be empty")
    return argv


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_job(path: Path, data: dict[str, object]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        raise


def _required_string(data: dict[str, object], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"job {field} must be a non-empty string")
    return value


def _required_datetime(data: dict[str, object], field: str) -> dt.datetime:
    value = data.get(field)
    if not isinstance(value, str):
        raise ValueError(f"job {field} must be an ISO-8601 datetime string")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"job {field} must be a valid ISO-8601 datetime") from error
    return _require_naive_datetime(parsed, field)


def _optional_datetime(data: dict[str, object], field: str) -> None:
    value = data.get(field)
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"job {field} must be an ISO-8601 datetime string or null")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"job {field} must be a valid ISO-8601 datetime") from error
    _require_naive_datetime(parsed, field)


def _require_naive_datetime(value: dt.datetime, field: str) -> dt.datetime:
    if value.tzinfo is not None and value.utcoffset() is not None:
        raise ValueError(f"job {field} must use local time without a UTC offset")
    return value


def _validate_job(
    decoded: object,
) -> tuple[dict[str, object], dt.datetime, Path, list[str], HandoffState | None]:
    if not isinstance(decoded, dict) or not all(
        isinstance(key, str) for key in decoded
    ):
        raise ValueError("job must be a JSON object with string keys")
    data = cast(dict[str, object], decoded)

    schema_version = data.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise ValueError("job schema_version must be 1")

    _required_string(data, "id")
    _required_string(data, "mode")
    _required_string(data, "model")
    workspace = Path(_required_string(data, "workspace")).resolve()
    run_at = _required_datetime(data, "run_at")
    _required_datetime(data, "created_at")
    _optional_datetime(data, "started_at")
    _optional_datetime(data, "finished_at")

    status = _required_string(data, "status")
    if status not in {"pending", "running", "succeeded", "failed"}:
        raise ValueError("job status is invalid")

    exit_code = data.get("exit_code")
    if exit_code is not None and type(exit_code) is not int:
        raise ValueError("job exit_code must be an integer or null")
    error = data.get("error")
    if error is not None and not isinstance(error, str):
        raise ValueError("job error must be a string or null")

    raw_argv = data.get("argv")
    if (
        not isinstance(raw_argv, list)
        or not raw_argv
        or not all(isinstance(item, str) for item in raw_argv)
    ):
        raise ValueError("job argv must be a non-empty list of strings")
    argv = cast(list[str], raw_argv)

    raw_transition = data.get("transition")
    transition: HandoffState | None = None
    if raw_transition is not None:
        if not isinstance(raw_transition, dict) or not all(
            isinstance(key, str) for key in raw_transition
        ):
            raise ValueError("job transition must be an object or null")
        transition = HandoffState.from_dict(
            cast(dict[str, object], raw_transition)
        )

    return data, run_at, workspace, argv, transition


def _load_job(
    path: Path,
) -> tuple[dict[str, object], dt.datetime, Path, list[str], HandoffState | None]:
    return _validate_job(_read_job_object(path))


def _read_job_object(path: Path) -> dict[str, object]:
    decoded: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict) or not all(isinstance(key, str) for key in decoded):
        raise ValueError("job must be a JSON object with string keys")
    return cast(dict[str, object], decoded)


def _persist_pre_execution_failure(
    path: Path,
    data: dict[str, object],
    error: Exception,
    clock: Callable[[], dt.datetime],
) -> int:
    exit_code = 1
    data["status"] = "failed"
    data["exit_code"] = exit_code
    data["error"] = str(error)
    data["finished_at"] = clock().isoformat()
    _write_job(path, data)
    return exit_code


def create_job(
    *,
    logs_path: Path,
    workspace: Path,
    mode: str,
    model: str,
    run_at: dt.datetime,
    argv: list[str],
    transition: HandoffState | None,
    now: Callable[[], dt.datetime] = dt.datetime.now,
) -> Path:
    if not argv:
        raise ValueError("command cannot be empty")
    _require_naive_datetime(run_at, "run_at")
    created_at = _require_naive_datetime(now(), "created_at")
    jobs_path = Path(logs_path).resolve() / "jobs"
    jobs_path.mkdir(parents=True, exist_ok=True)
    job_id = f"{created_at.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    path = jobs_path / f"{job_id}.json"
    data: dict[str, object] = {
        "schema_version": 1,
        "id": job_id,
        "mode": mode,
        "model": model,
        "workspace": str(Path(workspace).resolve()),
        "run_at": run_at.isoformat(),
        "argv": argv,
        "status": "pending",
        "created_at": created_at.isoformat(),
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "error": None,
        "transition": transition.to_dict() if transition else None,
    }
    _validate_job(data)
    _write_job(path, data)
    return path


def execute_job(
    job_path: Path,
    *,
    wait: bool = True,
    run: RunCallable = subprocess.run,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], dt.datetime] = dt.datetime.now,
) -> int:
    path = Path(job_path).resolve()
    data = _read_job_object(path)
    try:
        _, run_at, workspace, argv, transition = _validate_job(data)
    except ValueError as error:
        return _persist_pre_execution_failure(path, data, error, clock)
    delay = (run_at - clock()).total_seconds()
    if wait and delay > 0:
        sleeper(delay)

    data["status"] = "running"
    data["started_at"] = clock().isoformat()
    _write_job(path, data)

    if transition is not None:
        try:
            ContinuityStore(workspace).record(
                transition,
                event="scheduled_transition",
            )
        except Exception as error:
            exit_code = 1
            data["exit_code"] = exit_code
            data["status"] = "failed"
            data["error"] = str(error)
            data["finished_at"] = clock().isoformat()
            _write_job(path, data)
            return exit_code

    try:
        completed = run(argv, cwd=workspace, shell=False, check=False)
        exit_code = int(completed.returncode)
        data["exit_code"] = exit_code
        data["status"] = "succeeded" if exit_code == 0 else "failed"
    except OSError as error:
        exit_code = 127
        data["exit_code"] = exit_code
        data["status"] = "failed"
        data["error"] = str(error)

    data["finished_at"] = clock().isoformat()
    _write_job(path, data)
    return exit_code


def spawn_waiting_job(
    job_path: Path,
    *,
    popen: PopenCallable = subprocess.Popen,
) -> int:
    path = Path(job_path).resolve()
    _, _, workspace, _, _ = _load_job(path)
    log_path = path.with_suffix(".log")
    log_existed = log_path.exists()
    descriptor = os.open(
        log_path,
        os.O_APPEND | os.O_CREAT | os.O_WRONLY,
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        if not log_existed:
            _fsync_directory(log_path.parent)
        with os.fdopen(descriptor, "ab") as stream:
            descriptor = -1
            process = popen(
                [
                    sys.executable,
                    "-m",
                    "rate_limit_handoff.runner",
                    "--wait",
                    "--job",
                    str(path),
                ],
                cwd=workspace,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
                shell=False,
            )
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return int(process.pid)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m rate_limit_handoff.runner")
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args(argv)
    return execute_job(args.job, wait=args.wait)


if __name__ == "__main__":
    raise SystemExit(main())
