from __future__ import annotations

from pathlib import Path

import tomllib

from rate_limit_handoff import __version__
from rate_limit_handoff.cli import build_parser

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
