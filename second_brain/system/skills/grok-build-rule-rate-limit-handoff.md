# Grok Build Rule / Skill: Rate-Limit Aware Handoff

**Name:** rate-limit-handoff  
**For:** Grok Build CLI / xAI Grok Build surfaces + Hermes  
**Version:** 0.1.0  

## Core instruction (add to Grok Build system prompt or project rules)

You are operating inside a multi-tool workflow that also uses Claude Code, Codex, and Antigravity.  
A living file `handoff.md` (and the Second Brain) is the single source of truth for continuity.

**Whenever remaining capacity looks low** (usage % high, SuperGrok weekly quota low, API 429s, or user mentions limit / schedule / handoff):

1. Pause heavy generation.
2. Offer:

   > Capacity is getting low on Grok Build / current model.  
   > **A)** Switch to a lighter Grok variant or another tool and continue.  
   > **B)** (preferred) Schedule remaining work for the next available full-power window.  
   >   I will update `handoff.md` + Second Brain and create a resume point.  
   > Prefer B?

3. On schedule (B):
   ```bash
   rate-limit-handoff --schedule --model grok-build \
     --reset-at "HH:MM" \
     --summary "<precise remaining task + critical context>"
   ```
   Confirm the handoff was written, then stop.

4. On new session start: always check `handoff.md` first and continue from the Pending section if present.

## Notes for Hermes integration
- When Hermes surfaces xAI rate-limit headers or SuperGrok quota warnings, treat them as low-capacity signals and offer the schedule path.
- Prefer quality continuity over finishing on a degraded model.
