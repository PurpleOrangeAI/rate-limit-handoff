"""Command-line interface for rate-limit-handoff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .runner import parse_command
from .scheduler import LimitScheduler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rate-limit-handoff",
        description=(
            "Turn AI rate limits into high-quality checkpoints.\n"
            "Schedule work across Claude Code • Codex • Grok Build • Antigravity • Cursor • Hermes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rate-limit-handoff --schedule --model claude --reset-at "16:00" \\
      --summary "Continue the verified release work" --auto-run \\
      --command 'claude -p "Read handoff.md and continue the exact next action"'

  rate-limit-handoff --handoff --from claude --to codex \\
      --summary "Continue from the active handoff chain" --auto-run \\
      --command 'codex exec "Read handoff.md and continue the exact next action"'

  rate-limit-handoff --handoff --from claude --to codex --return-to claude \\
      --return-at "16:00" --summary "Use Codex now, then return for final review" \\
      --auto-run --command 'codex exec "Read handoff.md and continue"' \\
      --return-command 'claude -p "Read handoff.md and perform the planned return"'

  rate-limit-handoff --resume

  rate-limit-handoff --status --model claude

  rate-limit-handoff --parse-usage "5h limit: 12% left (resets 04:00)"

  rate-limit-handoff --codex-status

  rate-limit-handoff --init   # bootstrap handoff.md + second_brain template
        """,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Commands
    parser.add_argument(
        "--handoff", action="store_true", help="Hand off work to another model"
    )
    parser.add_argument(
        "--schedule", action="store_true", help="Schedule remaining work for reset time"
    )
    parser.add_argument(
        "--resume", action="store_true", help="Show resume instructions from handoff.md"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show time, next reset, and model info"
    )
    parser.add_argument(
        "--update-only", action="store_true", help="Just update handoff + Second Brain"
    )
    parser.add_argument(
        "--codex-status", action="store_true", help="Best-effort local Codex usage hints"
    )
    parser.add_argument(
        "--parse-usage",
        type=str,
        metavar="TEXT",
        help="Paste /status or dashboard text to extract remaining %% and reset hint",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Bootstrap handoff.md + second_brain/ skeleton in current directory",
    )

    # Options
    parser.add_argument(
        "--reset-at",
        type=str,
        default=None,
        help='Reset time e.g. "04:00" or "2026-07-12 04:00"',
    )
    parser.add_argument(
        "--summary",
        type=str,
        default=None,
        help="Precise description of remaining work + key context",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model/tool: claude | codex | grok | grok-build | antigravity | cursor",
    )
    parser.add_argument(
        "--from", dest="from_model", help="Model currently holding the work"
    )
    parser.add_argument("--to", dest="to_model", help="Destination model for a handoff")
    parser.add_argument("--return-to", help="Original model for a planned return")
    parser.add_argument("--return-at", help="Time for the planned return")
    parser.add_argument("--prefer", help="Preferred model when resuming")
    parser.add_argument(
        "--auto-run",
        action="store_true",
        help="Execute only the explicit command supplied for the selected route",
    )
    parser.add_argument(
        "--command", help="Explicit destination command; parsed without a shell"
    )
    parser.add_argument(
        "--return-command",
        help="Explicit command to execute at the planned return time",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=None,
        help=(
            "Workspace root (default: current directory). Should contain or become home "
            "of handoff.md"
        ),
    )
    parser.add_argument(
        "--second-brain-root",
        type=str,
        default=None,
        help=(
            "Optional Second Brain root. Existing 00 Inbox + 10 Projects directories "
            "are detected as an Obsidian vault layout"
        ),
    )
    return parser


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    primary_actions = (
        args.handoff,
        args.schedule,
        args.resume,
        args.status,
        args.update_only,
        args.codex_status,
        args.parse_usage is not None,
        args.init,
    )
    if sum(primary_actions) > 1:
        parser.error("only one primary action may be supplied")

    if args.handoff:
        if not args.from_model:
            parser.error("--handoff requires --from")
        if not args.to_model:
            parser.error("--handoff requires --to")
        if not args.summary or not args.summary.strip():
            parser.error("--handoff requires a non-empty --summary")

    if bool(args.return_to) != bool(args.return_at):
        parser.error("--return-to and --return-at must be supplied together")
    if (args.return_to or args.return_at) and not args.handoff:
        parser.error("planned return options require --handoff")
    if (args.from_model or args.to_model) and not args.handoff:
        parser.error("--from and --to require --handoff")
    if args.return_command and not args.return_to:
        parser.error("--return-command requires --return-to")

    if args.prefer and not args.resume:
        parser.error("--prefer requires --resume")

    if (args.command or args.return_command) and not args.auto_run:
        parser.error("--command and --return-command require --auto-run")

    if args.auto_run:
        if args.schedule and not args.command:
            parser.error("--schedule --auto-run requires --command")
        if args.handoff and not args.command:
            parser.error("--handoff --auto-run requires --command")
        if args.return_to and not args.return_command:
            parser.error("planned return auto-run requires --return-command")
        if not args.schedule and not args.handoff:
            parser.error("--auto-run requires --schedule or --handoff")


def _parse_command_arg(
    parser: argparse.ArgumentParser, option: str, command: str | None
) -> list[str] | None:
    if command is None:
        return None
    try:
        return parse_command(command)
    except ValueError as error:
        parser.error(f"{option}: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    command_argv = _parse_command_arg(parser, "--command", args.command)
    return_command_argv = _parse_command_arg(
        parser, "--return-command", args.return_command
    )

    workspace = Path(args.workspace).resolve() if args.workspace else Path.cwd()
    second_brain_root = Path(args.second_brain_root).resolve() if args.second_brain_root else None
    sched = LimitScheduler(workspace=workspace, second_brain_root=second_brain_root)

    if args.init:
        return cmd_init(sched)

    if args.handoff:
        return sched.handoff(
            summary=args.summary,
            from_model=args.from_model,
            to_model=args.to_model,
            return_to=args.return_to,
            return_at=args.return_at,
            auto_run=args.auto_run,
            command_argv=command_argv,
            return_command_argv=return_command_argv,
        )

    if args.schedule:
        summary = args.summary or "Continue previous work from handoff.md (no summary provided)"
        return sched.schedule(
            summary=summary,
            reset_at=args.reset_at,
            model=args.model or "unknown",
            auto_run=args.auto_run,
            command_argv=command_argv,
        )

    if args.resume:
        return sched.resume(prefer=args.prefer)

    if args.status:
        sched.status(model=args.model)
        return 0

    if args.update_only:
        summary = args.summary or "Manual update / checkpoint"
        model = args.model or "unknown"
        sched.update_only(summary=summary, reset_at=args.reset_at, model=model)
        return 0

    if args.codex_status:
        sched.codex_status()
        return 0

    if args.parse_usage is not None:
        text = args.parse_usage
        if not text.strip() and not sys.stdin.isatty():
            text = sys.stdin.read()
        if not text.strip():
            print('Provide text via --parse-usage "..." or pipe it.')
            return 1
        parsed = sched.parse_usage_text(text)
        print("Parsed usage:")
        for k, v in parsed.items():
            if k != "raw":
                print(f"  {k}: {v}")
        if parsed.get("reset_hint"):
            print(
                f'\nTip: you can now run --schedule --reset-at "{parsed["reset_hint"]}" '
                "(adjust format if needed)"
            )
        return 0

    # No command → help
    parser.print_help()
    print("\nQuick start:")
    print("  rate-limit-handoff --init")
    print('  rate-limit-handoff --schedule --reset-at "04:00" --model codex --summary "Your task"')
    print("  rate-limit-handoff --resume")
    return 0


def cmd_init(sched: LimitScheduler) -> int:
    """Bootstrap a ready-to-use workspace."""

    print(f"Initializing rate-limit-handoff workspace in: {sched.workspace}")

    # Create directories
    sched.ensure_dirs()

    # Create a starter handoff.md if missing
    if not sched.handoff_path.exists():
        starter = textwrap_starter_handoff()
        sched.handoff_path.write_text(starter, encoding="utf-8")
        print(f"[ok] Created {sched.handoff_path}")
    else:
        print(f"[skip] {sched.handoff_path} already exists")

    # Copy skills from package templates if we ship them
    # For now create them from embedded content
    _write_skills(sched)

    # Project README
    project_readme = sched.projects / "README.md"
    if not project_readme.exists():
        project_readme.write_text(_project_readme_content(), encoding="utf-8")
        print(f"[ok] Created {project_readme}")

    print("\n✅ Workspace ready.")
    print("Next steps:")
    print("  1. Copy the skills from second_brain/system/skills/ into your AI tools")
    print("     (Claude Project instructions, Codex skills, Cursor rules, etc.)")
    print("  2. When approaching a limit:")
    print('       rate-limit-handoff --schedule --reset-at "04:00" --model codex \\')
    print('           --summary "Precise next action"')
    print("  3. After reset: rate-limit-handoff --resume")
    return 0


def textwrap_starter_handoff() -> str:
    return """# Session Handoff Document
**Last Updated:** (auto)
**Current Session Context:** (fill me)
**Preferred Action on Limit Approaching:** Schedule continuation instead of falling back
to a weaker model

---

## Current Goal
(Describe the high-level goal of this workstream)

---

## Pending / In-Progress Work
- [ ] (first concrete next step)
- [ ] (second)

---

## Next Exact Action (to run after next rate-limit reset)
```bash
rate-limit-handoff --resume
# or open this file in your AI of choice and say:
# "Continue from handoff.md — rate limits have reset"
```

---

## Progress Log
| Time | Event | Model | Notes |
|------|-------|-------|-------|
|      |       |       |       |

---

## How to Use This Handoff
1. At the start of any new session: read this file first.
2. When a limit is ~10-15% remaining, offer the schedule choice.
3. On schedule: `rate-limit-handoff --schedule ...`

---

**Status:** Active  
**Owner:** (you)  
**Sync note:** Keep this file in the root of your Second Brain / project so it syncs
across machines.
"""


def _write_skills(sched: LimitScheduler) -> None:
    """Write the four sample skills into the workspace."""
    skills = {
        "codex-skill-rate-limit-handoff.md": _codex_skill(),
        "grok-build-rule-rate-limit-handoff.md": _grok_skill(),
        "antigravity-agy-skill-rate-limit-handoff.md": _agy_skill(),
        "auto-detect-limits-general.md": _general_skill(),
    }
    for name, content in skills.items():
        path = sched.skills / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            print(f"[ok] Skill → {path}")


def _project_readme_content() -> str:
    return """# Project: AI Rate-Limit Aware Handoff

See the main repository README for full documentation.

This folder lives inside your Second Brain so that every scheduled handoff
automatically compounds knowledge.
"""


def _codex_skill() -> str:
    return """# Codex Skill: Rate-Limit Aware Handoff

**Name:** rate-limit-handoff  
**For:** OpenAI Codex (CLI, app, or VS Code extension)  
**Version:** 0.2.1

## When to activate
- Remaining 5h usage is estimated < 20% (from `/status` or Settings → Usage)
- User says "almost out", "limit soon", "schedule it", "handoff", or similar
- You see a rate-limit / quota warning from Codex
- Long-running agent swarm or multi-file refactor that will exceed remaining budget

## Behavior (must follow)

1. **Stop** generating large new diffs or spawning more sub-agents.
2. Offer these routes:

   The current model is approaching its limit. Choose a continuity route:

   1. Same-model wait — preserve the exact next action and resume after the supplied
      reset time.
   2. Cross-model handoff — preserve the context and continue now in another provider
      or model.
   3. Return later — switch temporarily and schedule a return to the original model.

   Auto-run is optional and requires an explicit command. rate-limit-handoff does not
   guess provider commands or query providers to confirm availability.

3. Handle the selected route explicitly. If the user's wording does not identify route
   1, 2, or 3, ask which route they want instead of defaulting to a schedule.

### Route 1 — Same-model wait
Run (or instruct the user/host to run):
```bash
rate-limit-handoff --schedule --model codex \\
  --reset-at "HH:MM" \\
  --summary "<one precise sentence of remaining work + key files + acceptance criteria>"
```
Only auto-run when the user supplies the exact command:
```bash
rate-limit-handoff --schedule --model codex --reset-at "16:00" \\
  --summary "Continue the verified work" --auto-run \\
  --command 'codex exec "Read handoff.md and continue"'
```

### Route 2 — Cross-model handoff
Use the explicit source and destination. Only auto-run the exact command the user approved:
```bash
rate-limit-handoff --handoff --from codex --to claude \\
  --summary "Continue now" --auto-run \\
  --command 'claude -p "Read handoff.md and continue"'
```

### Route 3 — Return later
Name the temporary destination, original model, return time, and both approved commands:
```bash
rate-limit-handoff --handoff --from codex --to claude --return-to codex \\
  --return-at "16:00" --summary "Continue now, then return" --auto-run \\
  --command 'claude -p "Read handoff.md and continue"' \\
  --return-command 'codex exec "Read handoff.md and perform the planned return"'
```

Confirm: "Handoff + Second Brain updated. Resume after reset with
`rate-limit-handoff --resume` or just open handoff.md." Do **not** continue heavy work
on a degraded model unless the user explicitly overrides.

4. At the **start of every new Codex session** after a known reset:
   - Check for `handoff.md` in the workspace root (or Second Brain root).
   - If present, surface the Pending / Next Exact Action section first.

## Detection helpers
- Prefer live `/status` output. Paste it into the scheduler if needed:
  ```bash
  rate-limit-handoff --parse-usage "$(cat /tmp/codex-status.txt)"
  ```
- Local sessions often under `~/.codex/sessions`.

## Why this skill exists
Codex burns the 5h window quickly on reasoning-heavy agent work. Scheduling preserves
quality and compounds knowledge in the Second Brain instead of forcing a mediocre
continuation.
"""


def _grok_skill() -> str:
    return """# Grok Build Rule / Skill: Rate-Limit Aware Handoff

**Name:** rate-limit-handoff  
**For:** Grok Build CLI / xAI Grok Build surfaces + Hermes  
**Version:** 0.2.1

## Core instruction (add to Grok Build system prompt or project rules)

You are operating inside a multi-tool workflow that also uses Claude Code, Codex, and Antigravity.  
A living file `handoff.md` (and the Second Brain) is the single source of truth for continuity.

**Whenever remaining capacity looks low** (usage % high, SuperGrok weekly quota low,
API 429s, or user mentions limit / schedule / handoff):

1. Pause heavy generation.
2. Offer:

   The current model is approaching its limit. Choose a continuity route:

   1. Same-model wait — preserve the exact next action and resume after the supplied
      reset time.
   2. Cross-model handoff — preserve the context and continue now in another provider
      or model.
   3. Return later — switch temporarily and schedule a return to the original model.

   Auto-run is optional and requires an explicit command. rate-limit-handoff does not
   guess provider commands or query providers to confirm availability.

3. Handle the selected route explicitly. If the user's wording does not identify route
   1, 2, or 3, ask which route they want instead of defaulting to a schedule.

### Route 1 — Same-model wait
Run (or instruct the user/host to run):
```bash
rate-limit-handoff --schedule --model grok-build \\
  --reset-at "HH:MM" \\
  --summary "<precise remaining task + critical context>"
```
Only auto-run when the user supplies the exact Grok command:
```bash
rate-limit-handoff --schedule --model grok-build --reset-at "16:00" \\
  --summary "Continue the verified work" --auto-run \\
  --command '<explicit user-supplied Grok command>'
```

### Route 2 — Cross-model handoff
Use the explicit source and destination. Only auto-run the exact command the user approved:
```bash
rate-limit-handoff --handoff --from grok-build --to codex \\
  --summary "Continue now" --auto-run \\
  --command 'codex exec "Read handoff.md and continue"'
```

### Route 3 — Return later
Name the temporary destination, original model, return time, and both approved commands:
```bash
rate-limit-handoff --handoff --from grok-build --to codex --return-to grok-build \\
  --return-at "16:00" --summary "Continue now, then return" --auto-run \\
  --command 'codex exec "Read handoff.md and continue"' \\
  --return-command '<explicit user-supplied Grok return command>'
```

Confirm the handoff was written before any command runs.

4. On new session start: always check `handoff.md` first and continue from the Pending
   section if present.

## Notes for Hermes integration
- When Hermes surfaces xAI rate-limit headers or SuperGrok quota warnings, treat them
  as low-capacity signals and offer the schedule path.
- Prefer quality continuity over finishing on a degraded model.
"""


def _agy_skill() -> str:
    return """# Antigravity (agy CLI) Skill: Rate-Limit Aware Handoff

**Name:** rate-limit-handoff  
**For:** Google Antigravity / agy CLI  
**Version:** 0.2.1

## Why this is critical for Antigravity
agy has extremely high token overhead from system prompts + tools. Quotas (5h refresh
+ weekly) can disappear in 1–2 hours of real work. Silent degradation or account
switching mid-project is painful. Prefer an explicit schedule + handoff.

## Behavior

1. Watch for signals:
   - "Individual quota reached. Resets in XhYmZs"
   - `/context` showing high % used after few turns
   - User saying they are about to hit limit

2. Immediately offer:

   The current model is approaching its limit. Choose a continuity route:

   1. Same-model wait — preserve the exact next action and resume after the supplied
      reset time.
   2. Cross-model handoff — preserve the context and continue now in another provider
      or model.
   3. Return later — switch temporarily and schedule a return to the original model.

   Auto-run is optional and requires an explicit command. rate-limit-handoff does not
   guess provider commands or query providers to confirm availability.

3. Handle the selected route explicitly. If the user's wording does not identify route
   1, 2, or 3, ask which route they want instead of defaulting to a schedule.

### Route 1 — Same-model wait
Run (or instruct the user/host to run):
```bash
rate-limit-handoff --schedule --model antigravity \\
  --reset-at "HH:MM" \\
  --summary "<precise next steps + files that matter + acceptance criteria>"
```
Only auto-run when the user supplies the exact Antigravity command:
```bash
rate-limit-handoff --schedule --model antigravity --reset-at "16:00" \\
  --summary "Continue the verified work" --auto-run \\
  --command '<explicit user-supplied Antigravity command>'
```

### Route 2 — Cross-model handoff
Use the explicit source and destination. Only auto-run the exact command the user approved:
```bash
rate-limit-handoff --handoff --from antigravity --to codex \\
  --summary "Continue now" --auto-run \\
  --command 'codex exec "Read handoff.md and continue"'
```

### Route 3 — Return later
Name the temporary destination, original model, return time, and both approved commands:
```bash
rate-limit-handoff --handoff --from antigravity --to codex \\
  --return-to antigravity --return-at "16:00" \\
  --summary "Continue now, then return" --auto-run \\
  --command 'codex exec "Read handoff.md and continue"' \\
  --return-command '<explicit user-supplied Antigravity return command>'
```

Confirm and stop. Do not keep burning the remaining quota on low-value loops.

4. Session start rule: if `handoff.md` exists, read it and surface Pending work before
   doing anything else.
"""


def _general_skill() -> str:
    return """# General Auto-Detect Limits Skill (any frontend)

**Name:** auto-detect-rate-limits  
**Version:** 0.2.1
**Applies to:** Claude Code, Codex, Cursor, Hermes, Grok Build, Antigravity, custom agents

## Detection heuristics (proactive)

Trigger the schedule offer when **any** of these are true:

- Remaining capacity estimates < 15–20% of current window
- Explicit user language: "almost out", "hitting limit", "2 hours left",
  "schedule for later", "handoff", "don't want to drop to 5.4"
- Tool/UI messages containing: "rate limit", "usage limit", "quota reached",
  "resets in", "5h limit", "weekly limit"
- For Codex: after seeing `/status` with low %
- For Antigravity: after `/context` or "Resets in XhYmZs"
- For API/Hermes: 429 responses or remaining-token headers approaching zero
- Long-running agent/swarm that has already consumed significant reasoning time

## Canonical offer text (copy-paste ready)

The current model is approaching its limit. Choose a continuity route:

1. Same-model wait — preserve the exact next action and resume after the supplied
   reset time.
2. Cross-model handoff — preserve the context and continue now in another provider
   or model.
3. Return later — switch temporarily and schedule a return to the original model.

Auto-run is optional and requires an explicit command. rate-limit-handoff does not
guess provider commands or query providers to confirm availability.

## Route handling

Handle the selected route explicitly. If the user's wording does not identify route 1,
2, or 3, ask which route they want instead of defaulting to a schedule.

### Route 1 — Same-model wait

Run (or instruct the host to run) the scheduler with the correct `--model` flag:

```bash
rate-limit-handoff --schedule \\
  --model <claude|codex|grok|grok-build|antigravity|cursor> \\
  --reset-at "HH:MM" \\
  --summary "<one precise sentence of what still needs to be done + key files + done-when criteria>"
```

Only auto-run when the user supplies the exact command:

```bash
rate-limit-handoff --schedule --model claude --reset-at "16:00" \\
  --summary "Continue the verified release work" --auto-run \\
  --command 'claude -p "Read handoff.md and continue the exact next action"'
```

### Route 2 — Cross-model handoff

Use the explicit source and destination. Only auto-run the exact command the user approved:

```bash
rate-limit-handoff --handoff --from claude --to codex \\
  --summary "Continue from the active handoff chain" --auto-run \\
  --command 'codex exec "Read handoff.md and continue the exact next action"'
```

### Route 3 — Return later

Name the temporary destination, original model, return time, and both approved commands:

```bash
rate-limit-handoff --handoff --from claude --to codex --return-to claude \\
  --return-at "16:00" \\
  --summary "Use Codex now, then return for the final review" --auto-run \\
  --command 'codex exec "Read handoff.md and continue"' \\
  --return-command 'claude -p "Read handoff.md and perform the planned return"'
```

Then confirm and **stop heavy work**.

## Session start rule (all tools)

If `handoff.md` exists in the workspace or Second Brain root → read it first and
continue from Pending / Next Exact Action. Prefer full-power model after reset.

## Why
Rate limits become high-quality forced checkpoints instead of quality-destroying
interruptions. Knowledge compounds in the Second Brain every time you schedule.
"""


if __name__ == "__main__":
    raise SystemExit(main())
