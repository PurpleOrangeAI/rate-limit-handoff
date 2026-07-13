# Codex Skill: Rate-Limit Aware Handoff

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
rate-limit-handoff --schedule --model codex \
  --reset-at "HH:MM" \
  --summary "<one precise sentence of remaining work + key files + acceptance criteria>"
```
Only auto-run when the user supplies the exact command:
```bash
rate-limit-handoff --schedule --model codex --reset-at "16:00" \
  --summary "Continue the verified work" --auto-run \
  --command 'codex exec "Read handoff.md and continue"'
```

### Route 2 — Cross-model handoff
Use the explicit source and destination. Only auto-run the exact command the user approved:
```bash
rate-limit-handoff --handoff --from codex --to claude \
  --summary "Continue now" --auto-run \
  --command 'claude -p "Read handoff.md and continue"'
```

### Route 3 — Return later
Name the temporary destination, original model, return time, and both approved commands:
```bash
rate-limit-handoff --handoff --from codex --to claude --return-to codex \
  --return-at "16:00" --summary "Continue now, then return" --auto-run \
  --command 'claude -p "Read handoff.md and continue"' \
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
