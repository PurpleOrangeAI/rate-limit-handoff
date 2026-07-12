# Contributing to rate-limit-handoff

Thank you for helping make AI rate limits less painful.

## Philosophy (please keep)

1. **Prefer schedule over silent fallback** — quality continuity first.
2. **Always write both** `handoff.md` and a Second Brain note.
3. Stay **offline-first**, zero runtime deps if possible.
4. Keep the CLI simple and the skills copy-paste friendly.

## How to contribute

1. Fork + clone
2. `pip install -e ".[dev]"`
3. Create a branch
4. Make changes + add tests if possible
5. `ruff check . && pytest`
6. Open a PR with a clear description

## High-value contributions

- New model/tool definitions in `models.py`
- Better usage parsers (especially for new CLIs)
- Skills for additional frontends (Kilo, Cline, Roo, Continue, etc.)
- Documentation, demos, or real-world examples
- Windows / macOS notification improvements
- Rolling-window estimators that don't need a manual reset time

## Code style

- Python 3.10+
- Type hints preferred
- `ruff` for linting
- Keep functions focused and the public CLI stable

## Questions?

Open an issue. We read them.
