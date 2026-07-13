# Antigravity (agy CLI) Skill: Rate-Limit Aware Handoff

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
rate-limit-handoff --schedule --model antigravity \
  --reset-at "HH:MM" \
  --summary "<precise next steps + files that matter + acceptance criteria>"
```
Only auto-run when the user supplies the exact Antigravity command:
```bash
rate-limit-handoff --schedule --model antigravity --reset-at "16:00" \
  --summary "Continue the verified work" --auto-run \
  --command '<explicit user-supplied Antigravity command>'
```

### Route 2 — Cross-model handoff
Use the explicit source and destination. Only auto-run the exact command the user approved:
```bash
rate-limit-handoff --handoff --from antigravity --to codex \
  --summary "Continue now" --auto-run \
  --command 'codex exec "Read handoff.md and continue"'
```

### Route 3 — Return later
Name the temporary destination, original model, return time, and both approved commands:
```bash
rate-limit-handoff --handoff --from antigravity --to codex \
  --return-to antigravity --return-at "16:00" \
  --summary "Continue now, then return" --auto-run \
  --command 'codex exec "Read handoff.md and continue"' \
  --return-command '<explicit user-supplied Antigravity return command>'
```

Confirm and stop. Do not keep burning the remaining quota on low-value loops.

4. Session start rule: if `handoff.md` exists, read it and surface Pending work before
   doing anything else.
