# Promotion & Launch Guide

How to get eyes on `rate-limit-handoff` and build reputation.

## Launch checklist

### 1. Repo polish (done in 0.1.0)
- [x] Clean README with badges, architecture diagram, multi-tool table
- [x] MIT license
- [x] pyproject.toml + installable CLI
- [x] Skills for major tools
- [x] CHANGELOG
- [x] Basic tests
- [x] `.gitignore`

### 2. GitHub setup
```bash
cd rate-limit-handoff
git init
git add .
git commit -m "Initial release: rate-limit-handoff v0.1.0

Turn AI rate limits into high-quality checkpoints.
Supports Claude Code, Codex, Grok Build, Antigravity, Cursor, Hermes."
gh repo create PurpleOrangeAI/rate-limit-handoff --public --source=. --remote=origin --push
```

(Replace username if different.)

### 3. First posts (copy-paste ready)

**X / Twitter**
```
I got tired of hitting Claude Code / Codex 5h limits and losing flow (or dropping to weaker models).

So I built rate-limit-handoff:

• Schedule remaining work for the exact reset time
• Auto-update living handoff.md + Second Brain
• Multi-tool (Claude, Codex, Grok Build, Antigravity, Cursor…)
• Pure Python, MIT, zero deps

https://github.com/PurpleOrangeAI/rate-limit-handoff

Rate limits become high-quality checkpoints instead of interruptions.
```

**r/ClaudeCode / r/codex / r/Cursor**
Title: I built a rate-limit scheduler that also grows your Second Brain (Claude Code + Codex + more)

Body:
You know the pain: 1–2 hours left until the 5h window resets, deep in a complex task.

Options used to be:
1. Wait idle
2. Drop to 5.4 / mini and ship mediocre work

I built a third path: **schedule** the exact remaining work, snapshot everything into a living `handoff.md` + a permanent Second Brain note, and resume cleanly after reset.

Repo: https://github.com/PurpleOrangeAI/rate-limit-handoff

Features:
- Works with Claude Code, Codex, Grok Build, Antigravity (agy), Cursor, Hermes
- Ready-to-copy skills that make the AI itself offer the schedule choice
- `--parse-usage` for Codex /status pastes
- Zero dependencies, MIT

Would love feedback / PRs for more tools.
```

### 4. Longer form
- Short demo video / Loom: show hitting a fake limit → schedule → resume
- Blog post: "How I stopped losing flow to 5-hour rate limits"
- Mention in any "Claude Code tips" or "Codex tips" threads

### 5. Ongoing
- Reply to every issue/PR quickly (reputation signal)
- Add new tools as they appear
- Keep README sharp

## Positioning

**Not** "another AI wrapper".  
**Yes** "the missing continuity layer that turns rate limits into Second Brain growth".

That's differentiated and useful.
