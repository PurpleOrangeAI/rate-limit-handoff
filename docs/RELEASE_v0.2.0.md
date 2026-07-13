# rate-limit-handoff v0.2.0 — Multi-Model Continuity Engine

**Released:** 2026-07-13  
**Tag:** v0.2.0

## Headline
Rate limits are no longer dead ends.  
They are now routing decisions.

## What’s new

### Three handoff modes
| Mode | What it does |
|------|--------------|
| **same** | Wait for the *same* model next window (max quality) |
| **cross** | Instant handoff to a different model so you keep moving *now* |
| **return** | Temporary switch + planned return to the original model |

### New CLI
```bash
# Same-model wait
rate-limit-handoff --schedule --model claude --reset-at "16:00" --summary "..."

# Cross-model
rate-limit-handoff --handoff --from claude --to codex --summary "..."

# Temporary + planned return
rate-limit-handoff --handoff --from claude --to codex \
  --return-to claude --return-at "16:00" --summary "..."

# Resume with preference
rate-limit-handoff --resume --prefer claude

