from __future__ import annotations

import datetime as dt
import json
import stat

import pytest

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


def test_record_collapses_duplicate_complete_active_chain_blocks(tmp_path):
    old_block = (
        f"{ACTIVE_START}\n"
        "## Active Handoff Chain\n"
        "- Status: stale\n"
        f"{ACTIVE_END}"
    )
    handoff = tmp_path / "handoff.md"
    handoff.write_text(
        f"# Handoff\n\nBefore.\n\n{old_block}\n\nBetween.\n\n{old_block}\n\nAfter.\n",
        encoding="utf-8",
    )

    ContinuityStore(tmp_path, now=lambda: NOW).record(
        make_state(), event="cross_handoff"
    )

    content = handoff.read_text(encoding="utf-8")
    assert content.count(ACTIVE_START) == 1
    assert content.count(ACTIVE_END) == 1
    assert "Before." in content
    assert "Between." in content
    assert "After." in content
    assert "- Status: handed_off" in content


@pytest.mark.parametrize(
    "markers",
    [
        ACTIVE_START,
        ACTIVE_END,
        f"{ACTIVE_END}\n{ACTIVE_START}",
        f"{ACTIVE_START}\n{ACTIVE_START}\n{ACTIVE_END}\n{ACTIVE_END}",
    ],
    ids=["missing-end", "missing-start", "reversed", "nested"],
)
def test_record_rejects_malformed_markers_without_partial_mutation(
    tmp_path, markers
):
    handoff = tmp_path / "handoff.md"
    original_handoff = f"# Handoff\n\n{markers}\n"
    handoff.write_text(original_handoff, encoding="utf-8")
    logs = tmp_path / "second_brain" / "logs"
    logs.mkdir(parents=True)
    active = logs / "active_handoff.json"
    history = logs / "handoff_chain.jsonl"
    original_active = b'{"sentinel": "active"}\n'
    original_history = b'{"sentinel": "history"}\n'
    active.write_bytes(original_active)
    history.write_bytes(original_history)

    with pytest.raises(ValueError, match="active chain markers"):
        ContinuityStore(tmp_path, now=lambda: NOW).record(
            make_state(), event="cross_handoff"
        )

    assert handoff.read_text(encoding="utf-8") == original_handoff
    assert active.read_bytes() == original_active
    assert history.read_bytes() == original_history


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


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mode", None),
        ("source_model", 7),
        ("current_model", False),
        ("summary", ["invalid"]),
        ("status", {"invalid": True}),
    ],
)
def test_state_from_dict_rejects_invalid_required_strings(field, value):
    data = make_state().to_dict()
    data[field] = value

    with pytest.raises(ValueError, match=field):
        HandoffState.from_dict(data)


@pytest.mark.parametrize("field", ["mode", "created_at", "updated_at"])
def test_state_from_dict_rejects_missing_required_fields(field):
    data = make_state().to_dict()
    del data[field]

    with pytest.raises(ValueError, match=field):
        HandoffState.from_dict(data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("created_at", None),
        ("updated_at", 7),
        ("created_at", "not-a-timestamp"),
        ("updated_at", "2026-99-99T00:00:00"),
        ("return_to", 7),
        ("preferred_model", False),
        ("reset_at", 7),
        ("return_at", "not-a-timestamp"),
    ],
)
def test_state_from_dict_rejects_invalid_typed_fields(field, value):
    data = make_state().to_dict()
    data[field] = value

    with pytest.raises(ValueError, match=field):
        HandoffState.from_dict(data)


def test_load_returns_current_state_or_none(tmp_path):
    store = ContinuityStore(tmp_path, now=lambda: NOW)
    assert store.load() is None

    state = make_state(preferred_model="claude")
    store.record(state, event="resume_preference")

    assert store.load() == state


def test_load_rejects_corrupt_object_shaped_active_state(tmp_path):
    store = ContinuityStore(tmp_path, now=lambda: NOW)
    store.logs_path.mkdir(parents=True)
    corrupt = make_state().to_dict()
    corrupt["mode"] = None
    store.active_state_path.write_text(json.dumps(corrupt), encoding="utf-8")

    with pytest.raises(ValueError, match="mode"):
        store.load()


def test_record_keeps_private_permissions_and_append_only_history(tmp_path):
    store = ContinuityStore(tmp_path, now=lambda: NOW)

    store.record(make_state(status="first"), event="first")
    store.record(make_state(status="second"), event="second")

    assert stat.S_IMODE(store.active_state_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.history_path.stat().st_mode) == 0o600
    transitions = [
        json.loads(line)
        for line in store.history_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [transition["event"] for transition in transitions] == ["first", "second"]
    assert [transition["state"]["status"] for transition in transitions] == [
        "first",
        "second",
    ]
