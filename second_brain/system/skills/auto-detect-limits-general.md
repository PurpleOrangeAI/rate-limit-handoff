# General Auto-Detect Limits Skill (any frontend)

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
rate-limit-handoff --schedule \
  --model <claude|codex|grok|grok-build|antigravity|cursor> \
  --reset-at "HH:MM" \
  --summary "<one precise sentence of what still needs to be done + key files + done-when criteria>"
```

Only auto-run when the user supplies the exact command:

```bash
rate-limit-handoff --schedule --model claude --reset-at "16:00" \
  --summary "Continue the verified release work" --auto-run \
  --command 'claude -p "Read handoff.md and continue the exact next action"'
```

### Route 2 — Cross-model handoff

Use the explicit source and destination. Only auto-run the exact command the user approved:

```bash
rate-limit-handoff --handoff --from claude --to codex \
  --summary "Continue from the active handoff chain" --auto-run \
  --command 'codex exec "Read handoff.md and continue the exact next action"'
```

### Route 3 — Return later

Name the temporary destination, original model, return time, and both approved commands:

```bash
rate-limit-handoff --handoff --from claude --to codex --return-to claude \
  --return-at "16:00" \
  --summary "Use Codex now, then return for the final review" --auto-run \
  --command 'codex exec "Read handoff.md and continue"' \
  --return-command 'claude -p "Read handoff.md and perform the planned return"'
```

Then confirm and **stop heavy work**.

## Session start rule (all tools)

If `handoff.md` exists in the workspace or Second Brain root → read it first and
continue from Pending / Next Exact Action. Prefer full-power model after reset.

## Why
Rate limits become high-quality forced checkpoints instead of quality-destroying
interruptions. Knowledge compounds in the Second Brain every time you schedule.
