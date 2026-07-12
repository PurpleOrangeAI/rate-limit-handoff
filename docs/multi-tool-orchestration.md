# Project: AI Rate-Limit Aware Handoff System

**Goal:** Never lose flow or quality when a model's 5-hour (or weekly) limit is about to expire. Always have the option to schedule the exact next action for the reset time, while automatically updating the Second Brain and handoff.md.

**Owner:** Purple Orange AI  
**Started:** 2026-07-12  
**Status:** Core system + multi-tool support implemented (Claude Code • Codex • Grok Build • Antigravity/agy • Hermes • Cursor). Ready for integration & testing.

## Architecture

```
┌─────────────────┐     low capacity      ┌──────────────────────┐
│  Any AI Session │ ───────────────────►  │  Offer: Schedule?    │
│  Claude Code /  │                       │  or Fall back        │
│  Codex / Grok   │                       └──────────┬───────────┘
│  Build / agy /  │                                  │
│  Cursor / etc   │                                  │ yes
└─────────────────┘                                  ▼
┌─────────────────┐     update            ┌──────────────────────┐
│  handoff.md     │ ◄──────────────────── │  limit_scheduler.py  │
│  (living state) │                       │  + Second Brain note │
└─────────────────┘                       └──────────┬───────────┘
                                                     │
                                                     │ schedule
                                                     ▼
                                          ┌──────────────────────┐
                                          │  at / cron / timer / │
                                          │  desktop notif /     │
                                          │  Hermes auto-resume  │
                                          └──────────────────────┘
```

## Multi-Tool Orchestration (Claude Code + Codex + Grok Build + Antigravity/agy CLI)

This system is deliberately **model- and tool-agnostic**. The single `handoff.md` + Second Brain notes act as the universal bridge so you can freely move work between tools without losing context or quality.

### Supported tools (as of 2026-07-12)

| Tool | 5h / reset style | How to detect low remaining | Fallback | Notes |
|------|------------------|-----------------------------|----------|-------|
| **Claude Code** | 5h + weekly | UI countdown / % | lighter Claude / Haiku | Classic pain point; fixed-looking times for some users |
| **OpenAI Codex** | 5h + weekly (reasoning-minute heavy) | `/status` in CLI, Settings → Usage | GPT-5.4 / mini | Parallel agents, cloud tasks. Burn rate tied to reasoning time |
| **Grok Build** | Usage % (monthly-ish) + API | CLI usage command / console | lighter Grok | Hermes integration for xAI |
| **Antigravity (agy CLI)** | 5h refresh + weekly | `/context`, "quota reached. Resets in Xh" | Gemini Flash / classic Gemini CLI | Extremely heavy system+tools context → burns fast |
| **Cursor** | Backend-model dependent | Model switcher / usage indicators | cheaper model in settings | Real limiter is Claude/Codex/Grok under the hood |
| **Hermes + Grok** | SuperGrok weekly + RPS/TPM | Hermes /usage or xAI console | Grok-3 / mini | Your existing setup |

### Recommended orchestration pattern

1. **Primary deep work** → Claude Code or Codex (highest quality for hard problems).
2. When ~15-20% remaining or "approaching limit" message:
   - Run (or have the agent run):
     ```bash
     python scripts/limit_scheduler.py --schedule --reset-at "HH:MM" --model codex \
       --summary "Exact next action + files + acceptance criteria"
     ```
   - Or use the system instructions so the AI offers the choice automatically.
3. **During wait** → light tasks on Grok Build / Cursor / free tiers, or non-AI work.
4. **After reset** → open `handoff.md` (or `python ... --resume`) in whichever full-power tool is available. The note already says which model hit the wall.
5. **Cross-tool handoff**:
   - Codex plugin inside Claude Code (or reverse) can just point at `handoff.md`.
   - For Antigravity ↔ others: same single source of truth.
   - Always keep `handoff.md` in the synced Second Brain root so VPS ↔ local stays consistent.

### Codex-specific tips

- Inside Codex CLI: type `/status` to see live 5h % and reset.
- Paste the output:
  ```bash
  python scripts/limit_scheduler.py --parse-usage "5h limit: 12% left (resets 04:00)"
  ```
- Local session files often live under `~/.codex/sessions` (script can hint at them via `--codex-status`).
- Reasoning-heavy tasks burn the 5h window much faster than simple edits — schedule early on complex agent swarms.

### Antigravity (agy) notes

- Extremely high token overhead from system tools/context.
- Watch for "Individual quota reached. Resets in XhYmZs".
- Prefer scheduling over continuing on depleted accounts; switching Google accounts mid-project can cause consistency issues.

### Decision Log
- 2026-07-12: Prefer **schedule** over silent fallback. Quality > speed when the work is important.
- 2026-07-12: Always write to both handoff.md AND a dated Second Brain note (so knowledge compounds).
- 2026-07-12: Support both fixed reset times (user said 4:00am) and rolling 5h windows.
- 2026-07-12: Added Codex, Grok Build, Antigravity/agy, multi-tool orchestration section.
- 2026-07-12: Added best-effort usage parsers and skill templates for auto-detection.

## Open Questions / Next
- Wire Hermes tool that auto-calls the scheduler when x-codex-* or Anthropic rate-limit headers appear.
- Optional Telegram / Discord / desktop notify on schedule fire.
- Pure rolling-window estimator that doesn't rely on user-provided reset time.
- Skills for each frontend that inject the "offer schedule" behavior automatically.

## Files
- `../../handoff.md` — single source of truth for continuity
- `scripts/limit_scheduler.py` — core logic + Codex/Antigravity helpers
- `system/rate-limit-aware-ai-instructions.md` — master instructions
- `system/skills/` — generated sample skills/rules (Codex, Grok Build, Antigravity, etc.)
- This project folder for long-term notes, decisions, integrations
