# Shipping Checklist for Purple Orange AI

## Ready to go live

The package is polished and installable:

```bash
cd /home/workdir/artifacts/rate-limit-handoff
# (already tested: pip install -e . works, CLI works, tests pass)
```

### Create the public repo

```bash
cd /home/workdir/artifacts/rate-limit-handoff
git init
git add .
git commit -m "feat: initial public release of rate-limit-handoff v0.1.0

Turn AI rate limits into high-quality checkpoints.
Multi-tool support for Claude Code, Codex, Grok Build, Antigravity, Cursor, Hermes.
Living handoff.md + automatic Second Brain updates. MIT."

# Create on GitHub (adjust username if needed)
gh repo create PurpleOrangeAI/rate-limit-handoff --public \
  --description "Turn AI rate limits into high-quality checkpoints. Schedule across Claude Code, Codex, Grok Build, Antigravity & more." \
  --source=. --remote=origin --push
```

### Then

1. Edit `pyproject.toml` email / GitHub URLs if you want a different handle.
2. Add topics on GitHub: `ai`, `claude`, `codex`, `rate-limit`, `second-brain`, `productivity`, `claude-code`, `cursor`
3. Use the posts in `docs/promotion.md`
4. Pin the repo on your GitHub profile

### Local install for yourself

```bash
pip install -e /home/workdir/artifacts/rate-limit-handoff
# or after push:
pip install git+https://github.com/PurpleOrangeAI/rate-limit-handoff.git
```

### Next polish (optional, after launch)

- Add a simple GIF / screenshot of the flow
- `python -m build` + upload to PyPI when ready (`twine`)
- More skills as new tools appear

You're good. This is legitimately useful and well packaged.
