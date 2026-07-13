"""Durable state for same-model, cross-model, and planned-return continuity."""

from __future__ import annotations

import datetime as dt
import json
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
        values = dict(data)
        for key in ("created_at", "updated_at", "reset_at", "return_at"):
            value = values.get(key)
            values[key] = dt.datetime.fromisoformat(value) if isinstance(value, str) else None
        return cls(
            mode=str(values["mode"]),
            source_model=str(values["source_model"]),
            current_model=str(values["current_model"]),
            summary=str(values["summary"]),
            status=str(values["status"]),
            created_at=values["created_at"],  # type: ignore[arg-type]
            updated_at=values["updated_at"],  # type: ignore[arg-type]
            reset_at=values["reset_at"],  # type: ignore[arg-type]
            return_to=str(values["return_to"]) if values.get("return_to") else None,
            return_at=values["return_at"],  # type: ignore[arg-type]
            preferred_model=(
                str(values["preferred_model"]) if values.get("preferred_model") else None
            ),
        )


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
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self._write_json_atomic(self.active_state_path, state.to_dict())
        self.active_state_path.chmod(0o600)

        transition = {
            "event": event,
            "recorded_at": self._now().isoformat(),
            "state": state.to_dict(),
        }
        with self.history_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(transition, sort_keys=True) + "\n")
        self.history_path.chmod(0o600)
        self._write_active_chain(state)

    def _write_json_atomic(self, path: Path, data: dict[str, object]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)

    def _write_active_chain(self, state: HandoffState) -> None:
        content = (
            self.handoff_path.read_text(encoding="utf-8")
            if self.handoff_path.exists()
            else "# Session Handoff Document\n"
        )
        block = self._render_active_chain(state)

        if ACTIVE_START in content and ACTIVE_END in content:
            start = content.index(ACTIVE_START)
            end = content.index(ACTIVE_END, start) + len(ACTIVE_END)
            content = content[:start].rstrip() + "\n\n" + block + content[end:]
        else:
            content = content.rstrip() + "\n\n" + block + "\n"

        self.handoff_path.write_text(content, encoding="utf-8")

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
