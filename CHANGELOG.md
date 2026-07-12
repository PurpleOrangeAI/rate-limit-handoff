# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- `--update-only` now records an active checkpoint instead of falsely marking it scheduled.
- `at` jobs are submitted without invoking a parent shell, with notification text quoted.

### Added
- Optional `--second-brain-root` routing for existing Obsidian vaults using `00 Inbox/`
  and `10 Projects/`.
- CI coverage for tests, Ruff, mypy, and package builds on Python 3.10 and 3.13.

### Changed
- Installation docs now reflect that the first PyPI release is still pending.

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
