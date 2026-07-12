# Shipping Checklist for Purple Orange AI

## Current state

- Public repository: <https://github.com/PurpleOrangeAI/rate-limit-handoff>
- Package version: `0.1.0`
- Local CLI entry points: `rate-limit-handoff`, `rlh`, `limit-handoff`
- PyPI release: pending
- Git tag and GitHub release: pending

## Required before the first package release

```bash
python -m pytest -q
python -m ruff check .
python -m mypy src
python -m build
```

- [ ] Confirm all four validation commands pass from a clean checkout.
- [ ] Review wheel and source distribution contents under `dist/`.
- [ ] Publish to TestPyPI and install the uploaded artifact in a clean environment.
- [ ] Publish version `0.1.0` to PyPI.
- [ ] Create and push tag `v0.1.0`.
- [ ] Create the matching GitHub release from `CHANGELOG.md`.
- [ ] Replace the pending PyPI badge with the live version badge.

## Repository promotion

- [x] Public GitHub repository created.
- [x] Repository description and topics configured.
- [ ] Enable the CI workflow and confirm both Python versions pass.
- [ ] Add a short terminal recording or GIF of init → checkpoint → resume.
- [ ] Pin the repository on the Purple Orange AI GitHub profile.
- [ ] Use the reviewed copy in `docs/promotion.md` after the package release is live.

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
