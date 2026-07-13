"""Durable state for same-model, cross-model, and planned-return continuity."""

from __future__ import annotations

import datetime as dt
import json
import os
import stat
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

ACTIVE_START = "<!-- rlh:active-chain:start -->"
ACTIVE_END = "<!-- rlh:active-chain:end -->"


@dataclass(frozen=True)
class HandoffState:
    mode: str
    source_model: str
    current_model: str
    summary: str
    status: str
    created_at: dt.datetime
    updated_at: dt.datetime
    reset_at: dt.datetime | None = None
    return_to: str | None = None
    return_at: dt.datetime | None = None
    preferred_model: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        for key in ("created_at", "updated_at", "reset_at", "return_at"):
            value = data[key]
            data[key] = value.isoformat() if isinstance(value, dt.datetime) else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> HandoffState:
        return cls(
            mode=_required_string(data, "mode"),
            source_model=_required_string(data, "source_model"),
            current_model=_required_string(data, "current_model"),
            summary=_required_string(data, "summary"),
            status=_required_string(data, "status"),
            created_at=_required_datetime(data, "created_at"),
            updated_at=_required_datetime(data, "updated_at"),
            reset_at=_optional_datetime(data, "reset_at"),
            return_to=_optional_string(data, "return_to"),
            return_at=_optional_datetime(data, "return_at"),
            preferred_model=_optional_string(data, "preferred_model"),
        )


def _required_string(data: dict[str, object], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _optional_string(data: dict[str, object], field: str) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string or null")
    return value


def _required_datetime(data: dict[str, object], field: str) -> dt.datetime:
    if field not in data:
        raise ValueError(f"{field} is required")
    parsed = _parse_datetime(data[field], field)
    if parsed is None:
        raise ValueError(f"{field} must be an ISO-8601 datetime string")
    return parsed


def _optional_datetime(data: dict[str, object], field: str) -> dt.datetime | None:
    return _parse_datetime(data.get(field), field)


def _parse_datetime(value: object, field: str) -> dt.datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 datetime string or null")
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be a valid ISO-8601 datetime") from error


class ContinuityStore:
    def __init__(
        self,
        workspace: Path,
        now: Callable[[], dt.datetime] | None = None,
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.handoff_path = self.workspace / "handoff.md"
        self.logs_path = self.workspace / "second_brain" / "logs"
        self.active_state_path = self.logs_path / "active_handoff.json"
        self.history_path = self.logs_path / "handoff_chain.jsonl"
        self._now = now or dt.datetime.now

    def load(self) -> HandoffState | None:
        if not self.active_state_path.exists():
            return None
        data = json.loads(self.active_state_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("active handoff state must be a JSON object")
        return HandoffState.from_dict(data)

    def record(self, state: HandoffState, event: str) -> None:
        state_data = state.to_dict()
        validated_state = HandoffState.from_dict(state_data)
        handoff_content, handoff_mode = self._prepare_active_chain(validated_state)
        active_content = json.dumps(state_data, indent=2, sort_keys=True) + "\n"
        transition_content = json.dumps(
            {
                "event": event,
                "recorded_at": self._now().isoformat(),
                "state": state_data,
            },
            sort_keys=True,
        ) + "\n"

        self.logs_path.mkdir(parents=True, exist_ok=True)
        self._write_text_atomic(self.active_state_path, active_content, mode=0o600)
        self._append_history(transition_content)
        self._write_text_atomic(self.handoff_path, handoff_content, mode=handoff_mode)

    def _prepare_active_chain(self, state: HandoffState) -> tuple[str, int]:
        content = (
            self.handoff_path.read_text(encoding="utf-8")
            if self.handoff_path.exists()
            else "# Session Handoff Document\n"
        )
        mode = (
            stat.S_IMODE(self.handoff_path.stat().st_mode)
            if self.handoff_path.exists()
            else 0o600
        )
        block = self._render_active_chain(state)
        content_without_blocks = self._remove_active_chain_blocks(content)
        return content_without_blocks.rstrip() + "\n\n" + block + "\n", mode

    def _remove_active_chain_blocks(self, content: str) -> str:
        start_count = content.count(ACTIVE_START)
        end_count = content.count(ACTIVE_END)
        if start_count != end_count:
            raise ValueError("active chain markers must have matching start and end markers")

        cursor = 0
        retained: list[str] = []
        for _ in range(start_count):
            start = content.find(ACTIVE_START, cursor)
            end = content.find(ACTIVE_END, cursor)
            if start < 0 or end < start:
                raise ValueError("active chain markers must be ordered start before end")
            nested_start = content.find(ACTIVE_START, start + len(ACTIVE_START), end)
            if nested_start >= 0:
                raise ValueError("active chain markers must not be nested")
            retained.append(content[cursor:start])
            cursor = end + len(ACTIVE_END)
        retained.append(content[cursor:])
        return "".join(retained)

    def _write_text_atomic(self, path: Path, content: str, *, mode: int) -> None:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, mode)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                descriptor = -1
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            self._fsync_directory(path.parent)
        except BaseException:
            if descriptor >= 0:
                os.close(descriptor)
            temporary.unlink(missing_ok=True)
            raise

    def _append_history(self, content: str) -> None:
        existed = self.history_path.exists()
        descriptor = os.open(
            self.history_path,
            os.O_APPEND | os.O_CREAT | os.O_WRONLY,
            0o600,
        )
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
                descriptor = -1
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if not existed:
            self._fsync_directory(self.history_path.parent)

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _render_active_chain(self, state: HandoffState) -> str:
        lines = [
            ACTIVE_START,
            "## Active Handoff Chain",
            f"- Mode: {state.mode}",
            f"- Source model: {state.source_model}",
            f"- Current model: {state.current_model}",
            f"- Status: {state.status}",
            f"- Summary: {state.summary}",
        ]
        if state.reset_at:
            lines.append(f"- Reset at: {state.reset_at.isoformat(timespec='minutes')}")
        if state.return_to:
            lines.append(f"- Return to: {state.return_to}")
        if state.return_at:
            lines.append(f"- Return at: {state.return_at.isoformat(timespec='minutes')}")
        if state.preferred_model:
            lines.append(f"- Preferred resume model: {state.preferred_model}")
        lines.extend(
            [
                f"- Updated: {state.updated_at.isoformat(timespec='minutes')}",
                ACTIVE_END,
            ]
        )
        return "\n".join(lines)
