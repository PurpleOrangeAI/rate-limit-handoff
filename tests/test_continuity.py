from __future__ import annotations

import datetime as dt
import json

from rate_limit_handoff.continuity import (
    ACTIVE_END,
    ACTIVE_START,
    ContinuityStore,
    HandoffState,
)

NOW = dt.datetime(2026, 7, 13, 16, 0)


def make_state(**overrides: object) -> HandoffState:
    values: dict[str, object] = {
        "mode": "cross",
        "source_model": "claude",
        "current_model": "codex",
        "summary": "Finish the v0.2.1 release",
        "status": "handed_off",
        "created_at": NOW,
        "updated_at": NOW,
        "reset_at": None,
        "return_to": None,
        "return_at": None,
        "preferred_model": None,
    }
    values.update(overrides)
    return HandoffState(**values)  # type: ignore[arg-type]


def test_record_writes_active_state_and_transition(tmp_path):
    store = ContinuityStore(tmp_path, now=lambda: NOW)
    state = make_state()

    store.record(state, event="cross_handoff")

    active = json.loads(store.active_state_path.read_text(encoding="utf-8"))
    assert active["mode"] == "cross"
    assert active["current_model"] == "codex"

    entries = store.history_path.read_text(encoding="utf-8").splitlines()
    assert len(entries) == 1
    transition = json.loads(entries[0])
    assert transition["event"] == "cross_handoff"
    assert transition["state"]["summary"] == "Finish the v0.2.1 release"


def test_record_replaces_one_active_chain_block(tmp_path):
    handoff = tmp_path / "handoff.md"
    handoff.write_text("# Handoff\n\nExisting history.\n", encoding="utf-8")
    store = ContinuityStore(tmp_path, now=lambda: NOW)

    store.record(make_state(), event="cross_handoff")
    store.record(
        make_state(
            mode="return",
            current_model="claude",
            status="returned",
            return_to="claude",
            return_at=NOW + dt.timedelta(hours=1),
        ),
        event="planned_return_completed",
    )

    content = handoff.read_text(encoding="utf-8")
    assert content.count(ACTIVE_START) == 1
    assert content.count(ACTIVE_END) == 1
    assert "Existing history." in content
    assert "- Mode: return" in content
    assert "- Current model: claude" in content
    assert "- Status: returned" in content
    assert "Finish the v0.2.1 release" in content


def test_state_round_trip_preserves_optional_times():
    state = make_state(
        mode="return",
        reset_at=NOW + dt.timedelta(minutes=30),
        return_to="claude",
        return_at=NOW + dt.timedelta(hours=1),
        preferred_model="claude",
    )

    restored = HandoffState.from_dict(state.to_dict())

    assert restored == state


def test_load_returns_current_state_or_none(tmp_path):
    store = ContinuityStore(tmp_path, now=lambda: NOW)
    assert store.load() is None

    state = make_state(preferred_model="claude")
    store.record(state, event="resume_preference")

    assert store.load() == state
