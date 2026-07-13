# Shipping Checklist for Purple Orange AI

## Current state

- Public repository: <https://github.com/PurpleOrangeAI/rate-limit-handoff>
- Package version: `0.2.1`
- Local CLI entry points: `rate-limit-handoff`, `rlh`, `limit-handoff`
- PyPI release: pending
- Git tag and GitHub release: pending

## Required before the v0.2.1 GitHub release

```bash
.venv/bin/pytest tests/test_release_metadata.py -q
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/mypy src
git diff --check
.venv/bin/python -m build
```

- [ ] Confirm the full validation commands pass from a clean checkout.
- [ ] Review wheel and source distribution contents under `dist/`.
- [ ] Confirm wheel metadata and the installed CLI both report `0.2.1`.
- [ ] Run clean-wheel same-model, cross-model, planned-return, and scheduled-command
  smoke tests.
- [ ] Create and push tag `v0.2.1` only after validation succeeds.
- [ ] Create the matching GitHub release from `docs/RELEASE_v0.2.1.md`.
- [ ] Confirm the live tag, GitHub release, and GitHub Actions run point to the same
  verified commit.

PyPI publication is a separate pending action. Do not add or advertise a PyPI install
command until that publication is verified.

## Repository promotion

- [x] Public GitHub repository created.
- [x] Repository description and topics configured.
- [ ] Confirm the CI workflow passes on both Python versions for the release commit.
- [ ] Add a short terminal recording or GIF of init → checkpoint → resume.
- [ ] Pin the repository on the Purple Orange AI GitHub profile.
- [ ] Use the reviewed social copy only after v0.2.1 is live and verified.

## Local installation

Until PyPI is live:

```bash
pip install git+https://github.com/PurpleOrangeAI/rate-limit-handoff.git
```

For development:

```bash
git clone https://github.com/PurpleOrangeAI/rate-limit-handoff.git
cd rate-limit-handoff
pip install -e ".[dev]"
```
