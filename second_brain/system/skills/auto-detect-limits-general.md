# General Auto-Detect Limits Skill (any frontend)

**Name:** auto-detect-rate-limits  
**Version:** 0.1.0  
**Applies to:** Claude Code, Codex, Cursor, Hermes, Grok Build, Antigravity, custom agents

## Detection heuristics (proactive)

Trigger the schedule offer when **any** of these are true:

- Remaining capacity estimates < 15–20% of current window
- Explicit user language: "almost out", "hitting limit", "2 hours left", "schedule for later", "handoff", "don't want to drop to 5.4"
- Tool/UI messages containing: "rate limit", "usage limit", "quota reached", "resets in", "5h limit", "weekly limit"
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
rate-limit-handoff --schedule \
  --model <claude|codex|grok|grok-build|antigravity|cursor> \
  --reset-at "HH:MM" \
  --summary "<one precise sentence of what still needs to be done + key files + done-when criteria>"
```

Then confirm and **stop heavy work**.

## Session start rule (all tools)

If `handoff.md` exists in the workspace or Second Brain root → read it first and continue from Pending / Next Exact Action. Prefer full-power model after reset.

## Why
Rate limits become high-quality forced checkpoints instead of quality-destroying interruptions. Knowledge compounds in the Second Brain every time you schedule.
