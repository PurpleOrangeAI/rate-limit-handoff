from __future__ import annotations

from pathlib import Path

import tomllib

from rate_limit_handoff import __version__
from rate_limit_handoff.cli import (
    _agy_skill,
    _codex_skill,
    _general_skill,
    _grok_skill,
    build_parser,
)

ROOT = Path(__file__).parents[1]


def test_runtime_and_project_versions_match_v021():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["version"] == "0.2.1"
    assert __version__ == "0.2.1"


def test_readme_documents_executable_v021_contract():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for phrase in (
        "--handoff",
        "--from",
        "--to",
        "--return-to",
        "--return-at",
        "--prefer",
        "--auto-run",
        "--command",
        "--return-command",
        "shell=False",
        "no live provider-availability detection",
        "PyPI release is pending",
    ):
        assert phrase in readme


def test_parser_help_mentions_all_continuity_modes():
    help_text = build_parser().format_help()
    assert "--handoff" in help_text
    assert "--return-command" in help_text
    assert "--prefer" in help_text


def test_tracked_and_embedded_skills_handle_each_continuity_route_explicitly():
    skills = {
        "codex-skill-rate-limit-handoff.md": (
            _codex_skill(),
            "--schedule --model codex",
            "--handoff --from codex --to claude",
            "--return-to codex",
        ),
        "grok-build-rule-rate-limit-handoff.md": (
            _grok_skill(),
            "--schedule --model grok-build",
            "--handoff --from grok-build --to codex",
            "--return-to grok-build",
        ),
        "antigravity-agy-skill-rate-limit-handoff.md": (
            _agy_skill(),
            "--schedule --model antigravity",
            "--handoff --from antigravity --to codex",
            "--return-to antigravity",
        ),
        "auto-detect-limits-general.md": (
            _general_skill(),
            "--schedule --model claude",
            "--handoff --from claude --to codex",
            "--return-to claude",
        ),
    }

    for filename, (embedded, schedule, handoff, return_to) in skills.items():
        tracked = ROOT / "second_brain" / "system" / "skills" / filename
        assert tracked.read_bytes() == embedded.encode("utf-8")

        assert "chooses **B**" not in embedded
        assert "On schedule (B)" not in embedded
        assert "On B" not in embedded

        _, remaining = embedded.split("### Route 1 — Same-model wait", maxsplit=1)
        route_1, remaining = remaining.split(
            "### Route 2 — Cross-model handoff", maxsplit=1
        )
        route_2, route_3 = remaining.split("### Route 3 — Return later", maxsplit=1)

        assert schedule in route_1
        assert "--auto-run" in route_1
        assert "--command" in route_1

        assert handoff in route_2
        assert "--auto-run" in route_2
        assert "--command" in route_2

        assert handoff in route_3
        assert return_to in route_3
        assert '--return-at "16:00"' in route_3
        assert "--auto-run" in route_3
        assert "--command" in route_3
        assert "--return-command" in route_3

        assert "guess provider commands or query providers to confirm availability" in embedded
