# Grok Build Rule / Skill: Rate-Limit Aware Handoff

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

3. On schedule (B):
   ```bash
   rate-limit-handoff --schedule --model grok-build \
     --reset-at "HH:MM" \
     --summary "<precise remaining task + critical context>"
   ```
   Explicit auto-run examples (Grok commands remain user-supplied):
   ```bash
   rate-limit-handoff --schedule --model grok-build --reset-at "16:00" \
     --summary "Continue the verified work" --auto-run \
     --command '<explicit user-supplied Grok command>'
   rate-limit-handoff --handoff --from grok-build --to codex \
     --summary "Continue now" --auto-run \
     --command 'codex exec "Read handoff.md and continue"'
   rate-limit-handoff --handoff --from grok-build --to codex --return-to grok-build \
     --return-at "16:00" --summary "Continue now, then return" --auto-run \
     --command 'codex exec "Read handoff.md and continue"' \
     --return-command '<explicit user-supplied Grok return command>'
   ```
   Confirm the handoff was written before any command runs.

4. On new session start: always check `handoff.md` first and continue from the Pending
   section if present.

## Notes for Hermes integration
- When Hermes surfaces xAI rate-limit headers or SuperGrok quota warnings, treat them
  as low-capacity signals and offer the schedule path.
- Prefer quality continuity over finishing on a degraded model.
