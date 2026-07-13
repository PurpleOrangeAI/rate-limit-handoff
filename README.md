# rate-limit-handoff

<p align="center">
  <img src="assets/banner.png" alt="rate-limit-handoff banner" width="100%">
</p>

<p align="center">
  <strong>Rate limits are a continuity problem.</strong><br>
  Wait for the same model, continue now in another model, or switch and return later.<br>
  Preserve the exact next action in a living <code>handoff.md</code> so context never evaporates.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/PyPI-pending-lightgrey.svg" alt="PyPI pending">
  <a href="https://github.com/PurpleOrangeAI/rate-limit-handoff/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT"></a>
  <a href="https://github.com/PurpleOrangeAI/rate-limit-handoff"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python"></a>
  <img src="https://img.shields.io/badge/status-beta-yellow.svg" alt="Status">
</p>

---

## Why this exists

A serious AI session accumulates decisions, rejected paths, repository state, test
evidence, constraints, and one exact next action. When the current model hits a limit,
chat history alone is not a reliable operating state.

**rate-limit-handoff** gives you three explicit continuity routes:

1. **Same-model wait** — preserve the work and wait for the supplied reset time, with
   optional explicit auto-run when the same model is expected to be available.
2. **Cross-model handoff** — preserve the context and continue immediately in another
   provider or model.
3. **Return later** — switch temporarily, then schedule a return to the original model.

Every route writes the durable context first. Context stops evaporating; knowledge
compounds.

---

## Features

- **Multi-tool by design** — Claude Code, OpenAI Codex, Grok Build, Antigravity (agy), Cursor, Hermes
- **Proactive offer** — skills/rules that present the three continuity routes when capacity is low
- **One living handoff.md** — single source of truth that works across tools and machines
- **Second Brain integration** — every schedule automatically writes a dated note so knowledge compounds
- **Usage parsers** — paste `/status` or dashboard text; extracts remaining % and reset hint
- **Explicit local auto-run** — executes only user-supplied commands, parsed into arguments with `shell=False`
- **Best-effort local jobs** — detached runners and reminder artifacts are local, not reboot-durable services
- **Zero heavy deps** — pure Python stdlib, works offline
- **MIT licensed** — use it, fork it, ship it inside your company

---

## Quick Start

```bash
# Install from GitHub
pip install git+https://github.com/PurpleOrangeAI/rate-limit-handoff.git

# Or install from source for development
git clone https://github.com/PurpleOrangeAI/rate-limit-handoff.git
cd rate-limit-handoff
pip install -e .
```

The first PyPI release is pending. There is no PyPI installation command yet.

### 1. Bootstrap a workspace (once)
```bash
cd /path/to/your/project-or-second-brain
rate-limit-handoff --init
```

This creates:
- `handoff.md` (living session state)
- `second_brain/` skeleton with skills + project notes

To write checkpoint notes into an existing Obsidian vault while keeping `handoff.md`
in the project root:

```bash
rate-limit-handoff --workspace /path/to/project \
  --second-brain-root /path/to/MySecondBrain \
  --init
```

When the supplied root already contains `00 Inbox/` and `10 Projects/`, the CLI writes
notes to `00 Inbox/` and uses `10 Projects/ai-rate-limit-handoff/` for the project entry.
Otherwise it preserves the portable `inbox/` and `projects/` layout.

### 2. Choose a continuity route

#### Same-model wait

```bash
rate-limit-handoff --schedule \
  --model claude \
  --reset-at "16:00" \
  --summary "Continue the verified release work" \
  --auto-run \
  --command 'claude -p "Read handoff.md and continue the exact next action"'
```

Omit `--auto-run` and `--command` to create the durable handoff and best-effort local
reminder/resume artifact without executing a model command.

#### Immediate cross-model handoff

```bash
rate-limit-handoff --handoff \
  --from claude \
  --to codex \
  --summary "Continue from the active handoff chain" \
  --auto-run \
  --command 'codex exec "Read handoff.md and continue the exact next action"'
```

#### Temporary switch with planned return

```bash
rate-limit-handoff --handoff \
  --from claude \
  --to codex \
  --return-to claude \
  --return-at "16:00" \
  --summary "Use Codex now, then return for the final review" \
  --auto-run \
  --command 'codex exec "Read handoff.md and continue"' \
  --return-command 'claude -p "Read handoff.md and perform the planned return"'
```

#### Resume with a preference

```bash
rate-limit-handoff --resume --prefer claude
```

`--prefer` changes the continuation instruction. It does not launch that model.

### Auto-run truth boundary

Auto-run is opt-in. rate-limit-handoff executes only the explicit command you supply,
parses it into arguments, and launches it with shell=False.

The supplied reset time is the availability signal. v0.2.1 does not query provider
APIs to confirm that capacity has returned, does not guess provider CLI syntax, and
does not guarantee that a detached local job survives a machine reboot. This means
there is no live provider-availability detection.

Without --auto-run, scheduling remains a durable handoff plus a best-effort local
reminder/resume artifact.

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

| Tool | Window style | Operator-supplied capacity signal | Possible destination |
|------|--------------|-----------------------------------|----------------------|
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

They make the AI respond to low-capacity signals by offering the three continuity
routes. They do not add live provider-availability detection.

---

## Architecture (mental model)

```
┌─────────────────┐     low capacity      ┌──────────────────────┐
│  Any AI Session │ ───────────────────►  │ Wait / hand off /    │
│  Claude / Codex │                       │ switch and return    │
│  Grok / agy /   │                       └──────────┬───────────┘
│  Cursor / etc   │                                  │ yes
└─────────────────┘                                  ▼
┌─────────────────┐     update            ┌──────────────────────┐
│  handoff.md     │ ◄──────────────────── │  rate-limit-handoff  │
│  (living state) │                       │  + Second Brain note │
└─────────────────┘                       └──────────┬───────────┘
                                                     │
                                                     │ explicit command
                                                     ▼
                                          ┌──────────────────────┐
                                          │ best-effort local job│
                                          │ or reminder artifact │
                                          └──────────────────────┘
```

---

## Design Philosophy

1. **Prefer schedule / handoff over silent fallback** — make the routing decision explicit.
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
mypy src
python -m build
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
