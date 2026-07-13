# rate-limit-handoff

<p align="center">
  <img src="assets/banner.png" alt="rate-limit-handoff banner" width="100%">
</p>

<p align="center">
  <strong>Turn AI rate limits into high-quality checkpoints<br>and real multi-model continuity.</strong><br>
  Same-model wait • Cross-model handoff • Planned return<br>
  Claude Code • Codex • Grok Build • Antigravity • Cursor • Hermes
</p>

<p align="center">
  <a href="https://github.com/PurpleOrangeAI/rate-limit-handoff/releases/tag/v0.2.0"><img src="https://img.shields.io/badge/version-0.2.0-blue.svg" alt="Version"></a>
  <a href="https://github.com/PurpleOrangeAI/rate-limit-handoff/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT"></a>
  <a href="https://github.com/PurpleOrangeAI/rate-limit-handoff"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python"></a>
  <img src="https://img.shields.io/badge/status-public%20beta-yellow.svg" alt="Status">
</p>

---

## The real problem

You are deep in a complex task on Claude Code (or Codex, Antigravity, Grok Build…).

The bar is almost empty. The 5-hour window is about to close.

What do most people actually do?

1. Sit and wait (sometimes hours).
2. Drop to a weaker model *on the same tool* and accept lower quality.
3. **Switch to a completely different provider** (Claude → Codex, Codex → Claude, Antigravity → Claude, etc.) and try to reconstruct context from memory or chat history.

Option 3 is the most common in practice. It is also the most expensive in lost context and architectural continuity.

**rate-limit-handoff** turns that painful context switch into a clean, deliberate handoff.

---

## What this tool actually does

It gives you three powerful modes instead of chaos:

| Mode | What it does | When you use it |
|------|--------------|-----------------|
| **Same-model wait** | Park the work cleanly and resume on the *same* model when its next window opens | Maximum quality continuity |
| **Cross-model handoff** | Instantly hand the exact next action + critical context to a *different* model | Keep moving *right now* |
| **Return later** | Temporary switch to another model + planned return to the original one | e.g. Claude → Codex for implementation → back to Claude for final review |

Every time you schedule or hand off, it:

- Updates a living `handoff.md` (single source of truth)
- Writes a permanent dated note into your Second Brain
- Creates a clear resume path

Context stops evaporating. Knowledge compounds.

---

## Why this matters more than it sounds

High-compute models will always have rate limits (or temporary “unlimited” promotions that later change).  
The teams that win are not the ones who never hit limits.  
They are the ones who treat limits as **routing decisions** instead of quality drops or lost sessions.

This tool makes that routing clean, deliberate, and knowledge-preserving.

> **Note on Codex (July 2026):**  
> OpenAI temporarily removed the hard 5-hour limit for many users. The tool still works perfectly for Codex (and becomes even more useful the moment any limit or weekly cap reappears, or when you simply want to rotate to Claude / Antigravity / Grok for a different strength).

---

## Quick Start

```bash
pip install rate-limit-handoff

# Bootstrap a workspace (once)
cd /path/to/your/project-or-second-brain
rate-limit-handoff --init
```

### 1. Same-model wait (classic high-quality path)
```bash
rate-limit-handoff --schedule \
  --model claude \
  --reset-at "16:00" \
  --summary "Finish architecture decisions + open PRs with tests"
```

### 2. Immediate cross-model handoff (most common real-world use)
```bash
rate-limit-handoff --handoff \
  --from claude \
  --to codex \
  --summary "Continue agent swarm implementation from the current state"
```

### 3. Temporary switch + planned return
```bash
rate-limit-handoff --handoff \
  --from claude \
  --to codex \
  --return-to claude \
  --return-at "16:00" \
  --summary "Codex does the heavy implementation, then return to Claude for final architecture review"
```

### 4. Resume
```bash
rate-limit-handoff --resume --prefer claude
# or simply
rate-limit-handoff --resume
```

---

## The skill makes the AI offer the choice

When capacity is low, any agent using the skill now offers:

```
A) Fall back to a lighter model *on the same tool* and keep going right now.
B) Wait for the *same model*’s next window and resume with full power.
C) Hand off *now* to a different model (and optionally plan a return later).
```

This is the UX that turns rate limits into routing decisions instead of silent quality degradation.

---

## What gets written every time

- **Living `handoff.md`** – Active Handoff Chain table + full event history + exact next action
- **Second Brain note** – permanent dated capture so knowledge never dies in chat history
- Optional local resume scripts / notifications

One source of truth that works across Claude Code, Codex, Antigravity, Grok Build, Cursor, and Hermes.

---

## Supported tools

| Tool | Notes |
|------|-------|
| Claude Code / Claude Projects | Full support |
| OpenAI Codex | Full support (including periods with relaxed limits) |
| Grok Build + Hermes | Full support |
| Antigravity (agy) | Especially useful — burns quotas extremely fast |
| Cursor | Works via underlying model limits |
| Any tool that can load a skill / system prompt | Works |

---

## Philosophy

**Prefer schedule / handoff over silent fallback.**

Quality continuity + knowledge compounding is almost always more valuable than finishing a mediocre version on a weaker model or losing context while switching providers.

---

## Install / Upgrade

```bash
pip install -U rate-limit-handoff

# or from source
pip install -U git+https://github.com/PurpleOrangeAI/rate-limit-handoff.git
```

Requires Python 3.10+.

---

## Status

Public beta · MIT · Pure Python · Zero heavy dependencies · No telemetry · No cloud account required

Built by [Purple Orange AI](https://purpleorange.ai) for operators who refuse to lose flow or quality.

---

## Links

- **Release notes (v0.2.0):** https://github.com/PurpleOrangeAI/rate-limit-handoff/releases/tag/v0.2.0
- **Landing page:** https://purpleorangeai.github.io/rate-limit-handoff/
- **Changelog:** [CHANGELOG.md](./CHANGELOG.md)

---

**Rate limits are not the enemy.**  
Lost context and quality drops are.

This tool fixes both.

---

## Roadmap (community welcome)

- [ ] Pure rolling-window estimator that does not require user-provided reset time
- [ ] Hermes / xAI header watcher that auto-triggers schedule
- [ ] Telegram / Discord / desktop toast on schedule fire
- [ ] Obsidian / Logseq plugin for richer Second Brain integration
- [ ] More tools (Kilo, Cline, Roo, etc.) as they mature
- [ ] Smarter model routing suggestions based on available plans / remaining quota (future)

---

## Contributing

PRs welcome. Especially:

- New model/tool definitions
- Better usage parsers
- Skills for additional frontends
- Documentation & examples

Please keep the spirit: **simple, offline-first, opinionated toward quality continuity**.

---

## License

MIT © 2026 Purple Orange AI

---

## Inspiration & Related Work

- Community `HANDOFF.md` patterns that many of us already use manually
- Cross-tool handoff tools such as `cli-continues`
- The daily reality of 5-hour windows on Claude Code and Codex

This project exists because the best solution is the one that also grows your Second Brain.

---

<p align="center">
  Made with ❤️ for builders who refuse to lose flow.<br>
  <a href="https://github.com/PurpleOrangeAI">@PurpleOrangeAI</a>
</p>

