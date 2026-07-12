# rate-limit-handoff

<p align="center">
  <strong>Turn AI rate limits into high-quality checkpoints.</strong><br>
  Schedule remaining work across Claude Code • Codex • Grok Build • Antigravity • Cursor • Hermes.<br>
  Auto-update your Second Brain + living <code>handoff.md</code> so context never evaporates.
</p>

<p align="center">
  <a href="https://pypi.org/project/rate-limit-handoff/"><img src="https://img.shields.io/pypi/v/rate-limit-handoff.svg" alt="PyPI"></a>
  <a href="https://github.com/PurpleOrangeAI/rate-limit-handoff/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT"></a>
  <a href="https://github.com/PurpleOrangeAI/rate-limit-handoff"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python"></a>
  <img src="https://img.shields.io/badge/status-beta-yellow.svg" alt="Status">
</p>

---

## Why this exists

You hit the 5-hour wall on Claude Code or Codex at 1:50 AM.  
Reset is at 4:00 AM.  

Most people either:
- Wait idle (lose flow), or  
- Drop to a weaker model (5.4 / mini / Flash) and produce lower-quality work.

**rate-limit-handoff** gives you a third option:

> **Schedule** the exact remaining work for the moment the limit re-opens.  
> Snapshot everything into a living `handoff.md` + a permanent Second Brain note.  
> Resume cleanly with full power.

Rate limits stop being interruptions and become **forced high-quality checkpoints** that compound knowledge.

---

## Features

- **Multi-tool by design** — Claude Code, OpenAI Codex, Grok Build, Antigravity (agy), Cursor, Hermes
- **Proactive offer** — skills/rules that make the AI itself offer the schedule choice when capacity is low
- **One living handoff.md** — single source of truth that works across tools and machines
- **Second Brain integration** — every schedule automatically writes a dated note so knowledge compounds
- **Usage parsers** — paste `/status` or dashboard text; extracts remaining % and reset hint
- **Best-effort local jobs** — creates `at`/cron-friendly resume scripts + desktop notifications
- **Zero heavy deps** — pure Python stdlib, works offline
- **MIT licensed** — use it, fork it, ship it inside your company

---

## Quick Start

```bash
# Install (recommended)
pip install rate-limit-handoff

# Or from source
git clone https://github.com/PurpleOrangeAI/rate-limit-handoff.git
cd rate-limit-handoff
pip install -e .
```

### 1. Bootstrap a workspace (once)
```bash
cd /path/to/your/project-or-second-brain
rate-limit-handoff --init
```

This creates:
- `handoff.md` (living session state)
- `second_brain/` skeleton with skills + project notes

### 2. When you are about to hit a limit
```bash
rate-limit-handoff --schedule \
  --reset-at "04:00" \
  --model codex \
  --summary "Finish agent swarm on feature X, open PRs, update tests"
```

### 3. After the reset
```bash
rate-limit-handoff --resume
# or just open handoff.md in Claude/Codex/Grok/agy and say "continue from handoff"
```

### Extra power
```bash
# Parse Codex /status or any dashboard paste
rate-limit-handoff --parse-usage "5h limit: 12% left (resets 04:00)"

# Local Codex hints
rate-limit-handoff --codex-status

# Status + model info
rate-limit-handoff --status --model antigravity
```

---

## Supported Tools

| Tool | Window style | Detection | Fallback |
|------|--------------|-----------|----------|
| **Claude Code** | 5h + weekly | UI countdown / % | lighter Claude / Haiku |
| **OpenAI Codex** | 5h + weekly (reasoning heavy) | `/status`, Settings → Usage | GPT-5.4 / mini |
| **Grok Build** | Usage % + API | CLI / console | lighter Grok |
| **Antigravity (agy)** | 5h refresh + weekly | `/context`, "Resets in Xh" | Gemini Flash |
| **Cursor** | Backend-model dependent | Model switcher | cheaper model |
| **Hermes + Grok** | SuperGrok weekly + RPS/TPM | Hermes /usage | Grok-3 / mini |

The single `handoff.md` is the universal bridge. Start in Claude Code, hit limit, schedule, resume in Codex (or vice-versa). Your Second Brain stays coherent.

---

## Skills & Instructions (copy these)

After `--init` you get ready-to-use skills in `second_brain/system/skills/`:

- `codex-skill-rate-limit-handoff.md`
- `grok-build-rule-rate-limit-handoff.md`
- `antigravity-agy-skill-rate-limit-handoff.md`
- `auto-detect-limits-general.md`

**Copy the relevant skill** into:
- Claude Project custom instructions / Claude Code
- Codex skills or system prompt
- Grok Build / Hermes system prompt
- Antigravity (agy) rules
- Cursor Rules (`.cursor/rules`)
- Continue.dev / any multi-model frontend

They make the AI itself detect low capacity and offer the schedule choice automatically.

---

## Architecture (mental model)

```
┌─────────────────┐     low capacity      ┌──────────────────────┐
│  Any AI Session │ ───────────────────►  │  Offer: Schedule?    │
│  Claude / Codex │                       │  or Fall back        │
│  Grok / agy /   │                       └──────────┬───────────┘
│  Cursor / etc   │                                  │ yes
└─────────────────┘                                  ▼
┌─────────────────┐     update            ┌──────────────────────┐
│  handoff.md     │ ◄──────────────────── │  rate-limit-handoff  │
│  (living state) │                       │  + Second Brain note │
└─────────────────┘                       └──────────┬───────────┘
                                                     │
                                                     │ schedule
                                                     ▼
                                          ┌──────────────────────┐
                                          │  at / cron / script  │
                                          │  desktop notif       │
                                          └──────────────────────┘
```

---

## Design Philosophy

1. **Prefer schedule over silent fallback** — quality > speed when the work matters.
2. **Always write to both** handoff.md **and** a dated Second Brain note — knowledge compounds.
3. **Model-agnostic** — the same workflow works whether you live in Claude Code, Codex, or rotate between them.
4. **Zero magic, full control** — pure Python, no telemetry, no cloud, no accounts.
5. **Forced checkpoints are a feature** — every time you schedule you leave a clean, resumable trail.

---

## Development

```bash
git clone https://github.com/PurpleOrangeAI/rate-limit-handoff.git
cd rate-limit-handoff
pip install -e ".[dev]"
ruff check .
pytest
```

---

## Roadmap (community welcome)

- [ ] Pure rolling-window estimator that does not require user-provided reset time
- [ ] Hermes / xAI header watcher that auto-triggers schedule
- [ ] Telegram / Discord / desktop toast on schedule fire
- [ ] Obsidian / Logseq plugin for richer Second Brain integration
- [ ] More tools (Kilo, Cline, Roo, etc.) as they mature

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
