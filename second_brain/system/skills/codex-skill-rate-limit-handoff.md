# Codex Skill: Rate-Limit Aware Handoff

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
     rate-limit-handoff --schedule --model codex \
       --reset-at "HH:MM" \
       --summary "<one precise sentence of remaining work + key files + acceptance criteria>"
     ```
   - Confirm: "Handoff + Second Brain updated. Resume after reset with `rate-limit-handoff --resume` or just open handoff.md."
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
Codex burns the 5h window quickly on reasoning-heavy agent work. Scheduling preserves quality and compounds knowledge in the Second Brain instead of forcing a mediocre continuation.
