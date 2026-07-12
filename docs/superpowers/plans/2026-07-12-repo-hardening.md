# Rate Limit Handoff Repository Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the CLI safe and truthful enough for continued use while preserving its portable default layout and supporting Max's existing Obsidian Second Brain without creating a nested `second_brain/` vault.

**Architecture:** Keep `workspace` as the owner of the living `handoff.md` and local scheduling artifacts. Add an optional Second Brain root; when it contains the established `00 Inbox` and `10 Projects` directories, route notes and the `ai-rate-limit-handoff` project there. Preserve the existing portable `second_brain/inbox` and `second_brain/projects` layout when no external root is supplied.

**Tech Stack:** Python 3.10+, argparse, pathlib, pytest, Ruff, mypy, Hatchling, GitHub Actions.

## Global Constraints

- Preserve all existing CLI command names and the default portable workspace behavior.
- Do not add runtime dependencies.
- Do not write to the live Second Brain during tests; use temporary directories.
- Do not publish, push, tag, release, or modify STARLING.
- Preserve unrelated user files, especially `assets/banner1.png`.

---

### Task 1: Checkpoint status regression

**Files:**
- Modify: `tests/test_basic.py`
- Modify: `src/rate_limit_handoff/scheduler.py`

**Interfaces:**
- Consumes: `LimitScheduler.update_only(summary, reset_at, model)`.
- Produces: an active checkpoint block and note that are not labeled as scheduled work.

- [x] **Step 1: Write the failing test**

```python
def test_update_only_records_active_checkpoint():
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        sched = LimitScheduler(workspace=workspace)
        sched.update_only("Capture current state", reset_at="23:59", model="codex")

        handoff = (workspace / "handoff.md").read_text(encoding="utf-8")
        assert "## Handoff Update" in handoff
        assert "**Status:** ACTIVE" in handoff
        assert "SCHEDULED" not in handoff
```

- [x] **Step 2: Verify RED**

Run: `pytest tests/test_basic.py::test_update_only_records_active_checkpoint -v`

Expected: FAIL because `scheduled=False` is currently ignored.

- [x] **Step 3: Implement the minimal behavior distinction**

Use the existing `scheduled` argument to select the block title, status text, note filename, note heading, and trigger description. Pass `scheduled=False` through `write_second_brain_note` from `update_only`.

- [x] **Step 4: Verify GREEN**

Run: `pytest tests/test_basic.py::test_update_only_records_active_checkpoint -v`

Expected: PASS.

---

### Task 2: Existing Obsidian vault routing

**Files:**
- Modify: `tests/test_basic.py`
- Modify: `src/rate_limit_handoff/scheduler.py`
- Modify: `src/rate_limit_handoff/cli.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `LimitScheduler(workspace=..., second_brain_root=...)` and CLI `--second-brain-root PATH`.
- Produces: portable routing by default and Obsidian routing to `00 Inbox` plus `10 Projects/ai-rate-limit-handoff` when those canonical vault directories exist.

- [x] **Step 1: Write the failing test**

```python
def test_existing_obsidian_vault_uses_canonical_directories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        workspace = root / "artifact"
        vault = root / "vault"
        (vault / "00 Inbox").mkdir(parents=True)
        (vault / "10 Projects").mkdir()

        sched = LimitScheduler(workspace=workspace, second_brain_root=vault)

        assert sched.handoff == workspace / "handoff.md"
        assert sched.inbox == vault / "00 Inbox"
        assert sched.projects == vault / "10 Projects" / "ai-rate-limit-handoff"
        assert sched.second_brain_link == "10 Projects/ai-rate-limit-handoff/README"
```

- [x] **Step 2: Verify RED**

Run: `pytest tests/test_basic.py::test_existing_obsidian_vault_uses_canonical_directories -v`

Expected: FAIL because `second_brain_root` is not accepted.

- [x] **Step 3: Implement routing and CLI wiring**

Add an optional `second_brain_root` constructor parameter. Detect the established vault layout only when both `00 Inbox` and `10 Projects` already exist. Add `--second-brain-root` to argparse and pass the resolved path to `LimitScheduler`.

- [x] **Step 4: Verify GREEN and default compatibility**

Run: `pytest tests/test_basic.py -v`

Expected: all tests pass, including the original portable layout test.

---

### Task 3: Safe `at` scheduling

**Files:**
- Modify: `tests/test_basic.py`
- Modify: `src/rate_limit_handoff/scheduler.py`

**Interfaces:**
- Consumes: a user-provided summary string.
- Produces: `subprocess.run(["at", timestamp], input=quoted_command, shell=False, ...)`.

- [x] **Step 1: Write the failing test**

```python
def test_at_scheduler_does_not_invoke_a_shell(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/at")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    sched = LimitScheduler(workspace=tmp_path)
    sched.try_schedule_system_job(sched.next_reset("23:59"), '$(touch /tmp/unsafe)')

    args, kwargs = calls[0]
    assert args[0][0] == "at"
    assert kwargs.get("shell") is not True
    assert "'$(touch /tmp/unsafe)'" in kwargs["input"]
```

- [x] **Step 2: Verify RED**

Run: `pytest tests/test_basic.py::test_at_scheduler_does_not_invoke_a_shell -v`

Expected: FAIL because the current implementation uses `shell=True`.

- [x] **Step 3: Implement safe subprocess invocation**

Quote notification arguments with `shlex.quote`, pass the script over stdin, and invoke `at` using an argument list with `text=True`, `check=True`, and no shell.

- [x] **Step 4: Verify GREEN**

Run: `pytest tests/test_basic.py::test_at_scheduler_does_not_invoke_a_shell -v`

Expected: PASS.

---

### Task 4: Release truth, repository hygiene, and CI

**Files:**
- Create: `.gitignore`
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `SHIP.md`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `src/rate_limit_handoff/cli.py`
- Modify: `src/rate_limit_handoff/models.py`
- Modify: `src/rate_limit_handoff/scheduler.py`

**Interfaces:**
- Consumes: repository checks declared in `pyproject.toml`.
- Produces: truthful install/release copy and a CI gate for tests, Ruff, mypy, and wheel/sdist builds.

- [x] **Step 1: Add ignore rules and CI**

Ignore `.DS_Store`, `__pycache__/`, `*.py[cod]`, test/type/lint caches, virtual environments, and build artifacts. Configure CI on Python 3.10 and 3.13.

- [x] **Step 2: Align release documentation**

State that PyPI publishing is pending; recommend GitHub installation until a release exists. Replace the stale “create public repo” checklist with the real remaining release steps. Remove the placeholder author email rather than inventing an address.

- [x] **Step 3: Bring Ruff green**

Run: `ruff check . --fix`

Then wrap remaining long lines without changing CLI behavior.

- [x] **Step 4: Run the full deterministic gate**

Run:

```bash
pytest -q
ruff check .
mypy src
python -m build
```

Expected: every command exits 0.

---

### Task 5: End-to-end verification and review

**Files:**
- Verify: all changed files

**Interfaces:**
- Consumes: the finished repository state.
- Produces: evidence-backed handoff with residual user-owned work clearly separated.

- [x] **Step 1: Exercise both layouts**

Run `--init` and `--update-only` in a temporary portable workspace, then repeat with a temporary vault containing `00 Inbox` and `10 Projects`.

- [x] **Step 2: Review the diff**

Confirm every changed line traces to the audit findings. Verify `assets/banner1.png` remains untouched.

- [x] **Step 3: Report remaining external actions**

List PyPI publish, Git tag/release, and push as explicit unperformed actions. Record the
completed live Second Brain initialization and refresh as verification evidence.
