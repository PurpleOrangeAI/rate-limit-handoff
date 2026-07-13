from __future__ import annotations

import pytest

from rate_limit_handoff.cli import build_parser, main


def test_parser_exposes_v021_flags():
    args = build_parser().parse_args(
        [
            "--handoff",
            "--from",
            "claude",
            "--to",
            "codex",
            "--return-to",
            "claude",
            "--return-at",
            "16:00",
            "--summary",
            "Continue",
            "--auto-run",
            "--command",
            'codex exec "Read handoff.md"',
            "--return-command",
            'claude -p "Read handoff.md"',
        ]
    )
    assert args.handoff is True
    assert args.from_model == "claude"
    assert args.to_model == "codex"
    assert args.return_to == "claude"
    assert args.return_at == "16:00"
    assert args.auto_run is True


@pytest.mark.parametrize(
    "argv",
    [
        ["--handoff", "--from", "claude", "--summary", "Missing destination"],
        ["--handoff", "--to", "codex", "--summary", "Missing source"],
        ["--handoff", "--from", "claude", "--to", "codex"],
        [
            "--handoff",
            "--from",
            "claude",
            "--to",
            "codex",
            "--return-to",
            "claude",
            "--summary",
            "Missing return time",
        ],
        ["--schedule", "--auto-run", "--summary", "Missing command"],
        ["--schedule", "--command", "python -V"],
        ["--status", "--prefer", "claude"],
        [
            "--handoff",
            "--from",
            "claude",
            "--to",
            "codex",
            "--summary",
            "No return route",
            "--auto-run",
            "--command",
            "codex exec Continue",
            "--return-command",
            "claude -p Continue",
        ],
    ],
)
def test_invalid_combinations_fail_before_workspace_mutation(argv, tmp_path):
    with pytest.raises(SystemExit) as error:
        main([*argv, "--workspace", str(tmp_path)])
    assert error.value.code == 2
    assert not (tmp_path / "handoff.md").exists()
    assert not (tmp_path / "second_brain").exists()


def test_return_auto_run_requires_both_commands(tmp_path):
    argv = [
        "--handoff",
        "--from",
        "claude",
        "--to",
        "codex",
        "--return-to",
        "claude",
        "--return-at",
        "16:00",
        "--summary",
        "Return later",
        "--auto-run",
        "--command",
        "codex exec Continue",
        "--workspace",
        str(tmp_path),
    ]
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 2
    assert not (tmp_path / "handoff.md").exists()


@pytest.mark.parametrize(
    "argv",
    [
        [
            "--handoff",
            "--from",
            "claude",
            "--to",
            "codex",
            "--summary",
            "Conflicting action",
            "--schedule",
        ],
        ["--schedule", "--resume"],
    ],
)
def test_multiple_primary_actions_fail_before_workspace_mutation(argv, tmp_path):
    with pytest.raises(SystemExit) as error:
        main([*argv, "--workspace", str(tmp_path)])
    assert error.value.code == 2
    assert not (tmp_path / "handoff.md").exists()
    assert not (tmp_path / "second_brain").exists()


@pytest.mark.parametrize("command", ["   ", 'codex exec "unterminated'])
def test_invalid_command_fails_before_workspace_mutation(command, tmp_path):
    argv = [
        "--schedule",
        "--auto-run",
        "--command",
        command,
        "--workspace",
        str(tmp_path),
    ]
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 2
    assert not (tmp_path / "handoff.md").exists()
    assert not (tmp_path / "second_brain").exists()
