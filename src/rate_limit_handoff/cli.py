"""Command-line interface for rate-limit-handoff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
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
  rate-limit-handoff --schedule --reset-at "04:00" --model codex \\
      --summary "Finish agent swarm + open PRs"

  rate-limit-handoff --resume

  rate-limit-handoff --status --model claude

  rate-limit-handoff --parse-usage "5h limit: 12% left (resets 04:00)"

  rate-limit-handoff --codex-status

  rate-limit-handoff --init   # bootstrap handoff.md + second_brain template
        """,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Commands (mutually exclusive group would be nicer but keep simple flags for UX)
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve() if args.workspace else Path.cwd()
    second_brain_root = Path(args.second_brain_root).resolve() if args.second_brain_root else None
    sched = LimitScheduler(workspace=workspace, second_brain_root=second_brain_root)

    if args.init:
        return cmd_init(sched)

    if args.schedule:
        summary = args.summary or "Continue previous work from handoff.md (no summary provided)"
        model = args.model or "unknown"
        sched.schedule(summary=summary, reset_at=args.reset_at, model=model)
        return 0

    if args.resume:
        sched.resume()
        return 0

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
    if not sched.handoff.exists():
        starter = textwrap_starter_handoff()
        sched.handoff.write_text(starter, encoding="utf-8")
        print(f"[ok] Created {sched.handoff}")
    else:
        print(f"[skip] {sched.handoff} already exists")

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
**Version:** 0.1.0  

## When to activate
- Remaining 5h usage is estimated < 20% (from `/status` or Settings → Usage)
- User says "almost out", "limit soon", "schedule it", "handoff", or similar
- You see a rate-limit / quota warning from Codex
- Long-running agent swarm or multi-file refactor that will exceed remaining budget

## Behavior (must follow)

1. **Stop** generating large new diffs or spawning more sub-agents.
2. Offer exactly this choice (adapt only slightly for tone):

   > We're approaching the Codex 5h (or weekly) limit.  
   > **A)** Fall back to a lighter model (GPT-5.4 / mini) and continue now.  
   > **B)** (recommended) Schedule the remaining work for the next reset. I will:
   > - Snapshot exact next action + context into `handoff.md`
   > - Write a permanent note into the Second Brain
   > - Create a resume reminder  
   > Which do you prefer?

3. If user chooses **B** (or any schedule/handoff language):
   - Run (or instruct the user/host to run):
     ```bash
     rate-limit-handoff --schedule --model codex \\
       --reset-at "HH:MM" \\
       --summary "<one precise sentence of remaining work + key files + acceptance criteria>"
     ```
   - Confirm: "Handoff + Second Brain updated. Resume after reset with
     `rate-limit-handoff --resume` or just open handoff.md."
   - Do **not** continue heavy work on a degraded model unless the user explicitly overrides.

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
**Version:** 0.1.0  

## Core instruction (add to Grok Build system prompt or project rules)

You are operating inside a multi-tool workflow that also uses Claude Code, Codex, and Antigravity.  
A living file `handoff.md` (and the Second Brain) is the single source of truth for continuity.

**Whenever remaining capacity looks low** (usage % high, SuperGrok weekly quota low,
API 429s, or user mentions limit / schedule / handoff):

1. Pause heavy generation.
2. Offer:

   > Capacity is getting low on Grok Build / current model.  
   > **A)** Switch to a lighter Grok variant or another tool and continue.  
   > **B)** (preferred) Schedule remaining work for the next available full-power window.  
   >   I will update `handoff.md` + Second Brain and create a resume point.  
   > Prefer B?

3. On schedule (B):
   ```bash
   rate-limit-handoff --schedule --model grok-build \\
     --reset-at "HH:MM" \\
     --summary "<precise remaining task + critical context>"
   ```
   Confirm the handoff was written, then stop.

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
**Version:** 0.1.0  

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

   > Antigravity quota is low / about to hit the 5h wall.  
   > **A)** Continue on a lighter Gemini model or switch tools now.  
   > **B)** (strongly recommended) Schedule the exact remaining work for after the reset.  
   >   I will write everything into `handoff.md` + Second Brain so you can resume
   >   cleanly in agy, Claude Code, Codex, or Grok.
   > Choose B?

3. On B:
   ```bash
   rate-limit-handoff --schedule --model antigravity \\
     --reset-at "HH:MM" \\
     --summary "<precise next steps + files that matter + acceptance criteria>"
   ```
   Confirm and stop. Do not keep burning the remaining quota on low-value loops.

4. Session start rule: if `handoff.md` exists, read it and surface Pending work before
   doing anything else.
"""


def _general_skill() -> str:
    return """# General Auto-Detect Limits Skill (any frontend)

**Name:** auto-detect-rate-limits  
**Version:** 0.1.0  
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

```
We're getting close to the limit on this model/tool.
Option A — Switch to the fallback / lighter model right now and keep going.
Option B (recommended) — Schedule the remaining work for the next 5-hour (or weekly) reset. I will:
- Snapshot everything into handoff.md
- Write a permanent note into the Second Brain
- Create a resume reminder for after the reset
Which do you prefer?
```

## On schedule (B)

Always run (or instruct host to run) the scheduler with the correct `--model` flag:

```bash
rate-limit-handoff --schedule \\
  --model <claude|codex|grok|grok-build|antigravity|cursor> \\
  --reset-at "HH:MM" \\
  --summary "<one precise sentence of what still needs to be done + key files + done-when criteria>"
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
