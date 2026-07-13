# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-07-13

v0.1 began as a same-model scheduler and evolved overnight into the v0.2 multi-model
continuity design. v0.2.1 makes that design truthful, executable behavior.

### Added
- Three explicit continuity routes: same-model wait, immediate cross-model handoff,
  and a temporary switch with planned return.
- Optional local auto-run for user-supplied destination and return commands.
- `--handoff`, `--from`, `--to`, `--return-to`, `--return-at`, `--prefer`,
  `--auto-run`, `--command`, and `--return-command`.
- One canonical Active Handoff Chain with durable state, transition history, private
  job records, and result logs.
- Optional `--second-brain-root` routing for existing Obsidian vaults using `00 Inbox/`
  and `10 Projects/`.
- CI coverage for tests, Ruff, mypy, and package builds on Python 3.10 and 3.13.

### Fixed
- Source, runtime, package, and skill version metadata now agree on `0.2.1`.
- The shipped CLI now matches the multi-model interface described by v0.2.0.
- `--update-only` now records an active checkpoint instead of falsely marking it scheduled.
- `at` jobs are submitted without invoking a parent shell, with notification text quoted.

### Changed
- Commands are parsed into argument vectors and executed with `shell=False`; provider
  commands are never inferred.
- The supplied reset time is the availability proxy. Local detached jobs remain
  best-effort across machine uptime and are not represented as reboot durable.
- Installation remains GitHub-first because the first PyPI release is pending.

## [0.1.0] - 2026-07-12

### Added
- Initial public release
- Core CLI: `--schedule`, `--resume`, `--status`, `--update-only`, `--parse-usage`, `--codex-status`, `--init`
- Multi-tool support: Claude Code, OpenAI Codex, Grok Build, Antigravity (agy), Cursor, Hermes
- Living `handoff.md` + automatic Second Brain inbox notes
- Ready-to-copy skills for Codex, Grok Build, Antigravity, and general auto-detect
- Best-effort local job scheduling (`at` / resume scripts / notify-send)
- Pure stdlib, zero runtime dependencies
- MIT license

### Design
- Prefer schedule over silent fallback to weaker models
- Always write both handoff.md and a permanent Second Brain note
- Model-agnostic single source of truth
