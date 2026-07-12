"""Basic smoke tests for rate-limit-handoff."""

from __future__ import annotations

import tempfile
from pathlib import Path

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
