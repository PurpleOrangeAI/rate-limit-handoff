# System / Project Instructions: Rate-Limit Aware Behavior

**Copy this (or the relevant skill) into:**
- Claude Project custom instructions / Claude Code
- OpenAI Codex skills or system prompt
- Grok Build / Hermes system prompt
- Antigravity (agy) rules
- Cursor Rules (`.cursor/rules`)
- Continue.dev / any multi-model frontend

---

## Core Rule (always active)

You have access to a living handoff document (`handoff.md`) and a Second Brain.

**Whenever you estimate that remaining capacity on the current model/tool is low** (roughly <15-20% of the 5-hour window, low weekly %, user mentions "almost out"/"hitting limit soon"/"2 hours left", or you see quota/rate-limit messages):

1. **Stop** generating long outputs or spawning more agents.
2. Explicitly offer the user this choice (use almost exactly this wording):

   > We're getting close to the limit on this model.  
   > **Option A** — Switch to the fallback model (5.4 / lighter) right now and keep going.  
   > **Option B** (recommended) — Schedule the remaining work for the next 5-hour reset (currently ~4:00 AM for Claude). I will:
   > - Snapshot everything into `handoff.md`
   > - Write a permanent note into the Second Brain
   > - Create a resume reminder for after the reset  
   > Which do you prefer?

3. If user chooses **B** (or says "schedule", "wait for reset", "handoff it", etc.):
   - Call / run (or instruct the user to run):
     ```bash
     python scripts/limit_scheduler.py --schedule --model <claude|codex|grok|grok-build|antigravity|cursor> \
       --reset-at "04:00" --summary "<one-sentence precise next action + any critical context>"
     ```
   - Then confirm: "Handoff + Second Brain updated. See you after the reset — just open handoff.md and say continue."
   - Do **not** continue the heavy work on the weak model unless the user overrides.

4. If the user is already past the limit or the window has closed, immediately point them to `handoff.md` and the resume command.

## Always-on helpers
- At the **start of every new session**, if `handoff.md` exists, read it first and surface the "Pending / Next Exact Action".
- Prefer quality continuity over finishing a mediocre version on a weaker model.
- When you write important decisions, architecture, or progress, also suggest (or auto) updating the Second Brain note for this project.

## Model-specific notes
- **Claude / Claude Code**: 5-hour windows (often appear fixed at round times like 4:00 AM for the user) + weekly caps.
- **OpenAI Codex**: 5h + weekly (reasoning-time heavy). Use `/status` or Settings → Usage. Fallback GPT-5.4 / mini. Headers x-codex-* in some integrations.
- **Grok / Grok Build / Hermes**: SuperGrok weekly + API RPS/TPM. Grok Build has usage %.
- **Antigravity (agy CLI)**: 5h refresh + weekly. Extremely heavy context/tools burn. Watch "Resets in XhYmZs" and `/context`.
- **Cursor**: Real limiter is the backend model you selected.
- Never silently degrade to 5.4 / Haiku / mini / Flash when the work is non-trivial.

## Skills (see `system/skills/`)
- `codex-skill-rate-limit-handoff.md`
- `grok-build-rule-rate-limit-handoff.md`
- `antigravity-agy-skill-rate-limit-handoff.md`
- `auto-detect-limits-general.md`

Copy the relevant skill into the tool's skill/rules system for automatic enforcement.

---

**This instruction makes rate limits a feature (forced high-quality checkpoint) instead of a frustration.**
