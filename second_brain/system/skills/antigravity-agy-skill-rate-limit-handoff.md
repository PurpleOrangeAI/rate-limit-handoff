# Antigravity (agy CLI) Skill: Rate-Limit Aware Handoff

**Name:** rate-limit-handoff  
**For:** Google Antigravity / agy CLI  
**Version:** 0.1.0  

## Why this is critical for Antigravity
agy has extremely high token overhead from system prompts + tools. Quotas (5h refresh + weekly) can disappear in 1–2 hours of real work. Silent degradation or account switching mid-project is painful. Prefer an explicit schedule + handoff.

## Behavior

1. Watch for signals:
   - "Individual quota reached. Resets in XhYmZs"
   - `/context` showing high % used after few turns
   - User saying they are about to hit limit

2. Immediately offer:

   > Antigravity quota is low / about to hit the 5h wall.  
   > **A)** Continue on a lighter Gemini model or switch tools now.  
   > **B)** (strongly recommended) Schedule the exact remaining work for after the reset.  
   >   I will write everything into `handoff.md` + Second Brain so you can resume cleanly in agy, Claude Code, Codex, or Grok.  
   > Choose B?

3. On B:
   ```bash
   rate-limit-handoff --schedule --model antigravity \
     --reset-at "HH:MM" \
     --summary "<precise next steps + files that matter + acceptance criteria>"
   ```
   Confirm and stop. Do not keep burning the remaining quota on low-value loops.

4. Session start rule: if `handoff.md` exists, read it and surface Pending work before doing anything else.
