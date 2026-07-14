# Final Review Fix Report

Date: 2026-07-13

## Scope

Fixed the two Important final-review regressions from clean base `90b665d`:

1. User-controlled handoff scalars could inject active-chain sentinels and newlines,
   creating duplicate or nested marker pairs.
2. Offset-aware schedules were accepted into a local-time workflow, causing aware/naive
   datetime subtraction failures and leaving executable jobs pending.

Fix commit: `8a30c5d` (`fix(core): harden handoff and schedule inputs`)

## Reproduction and RED

Added focused regression coverage before changing production code, then ran:

```text
PYTHONPATH=src pytest -q \
  tests/test_continuity.py::test_record_escapes_multiline_marker_fields_without_changing_state \
  tests/test_basic.py::test_schedule_and_update_escape_marker_fields_in_handoff \
  tests/test_basic.py::test_offset_reset_time_raises_without_workspace_mutation \
  tests/test_basic.py::test_offset_return_time_raises_without_workspace_mutation \
  tests/test_runner.py::test_create_job_rejects_aware_run_at_before_writing \
  tests/test_runner.py::test_execute_job_persists_aware_run_at_validation_failure
```

RED result: `6 failed`.

- A second continuity record raised `ValueError: active chain markers must not be nested`.
- The scheduler schedule/update flow left six raw active-start markers in `handoff.md`.
- An offset-aware reset raised `TypeError: can't subtract offset-naive and offset-aware datetimes`.
- An offset-aware planned return was accepted and mutated the workspace.
- `create_job` wrote an offset-aware `run_at` instead of rejecting it.
- `execute_job` raised the same subtraction `TypeError` before persisting a terminal state.

## Fix

- Added one handoff-scalar renderer that collapses CR/LF sequences to spaces and HTML-escapes
  markup while preserving exact source values in JSON.
- Applied the renderer to every scalar in the active chain and to the legacy scheduler block's
  summary/model/status rendering.
- Added a pre-write invariant requiring the rendered active block to contain exactly one ordered
  active marker pair.
- Rejected explicit offset-aware scheduler timestamps before workspace mutation.
- Rejected aware runner datetimes, including `create_job` inputs, before the jobs directory is
  created.
- Split object loading from job validation so object-shaped validation failures can be written
  back as `failed` with exit code, error, and `finished_at`. Malformed or non-object JSON remains
  unrecoverable and raises.

## GREEN and Validation

Focused GREEN:

```text
6 passed in 0.09s
```

Focused continuity/runner/scheduler suite:

```text
69 passed in 0.30s
```

Full repository gates from `.venv`:

```text
.venv/bin/pytest -q       -> 87 passed in 0.25s
.venv/bin/ruff check .    -> All checks passed
.venv/bin/mypy src        -> Success: no issues found in 7 source files
.venv/bin/python -m build -> built sdist and wheel successfully
git diff --check          -> clean
```

Fresh installed-wheel smoke:

- Installed `dist/rate_limit_handoff-0.2.1-py3-none-any.whl` into a new temporary virtualenv.
- Same-model schedule with local `2099-07-13 16:00` preserved an unknown provider/model and wrote
  a single active marker pair.
- Planned return with local `2099-07-13 17:00` wrote mode `return`, destination `codex`, return
  model `claude`, the exact offset-free timestamp, and a single active marker pair.
- Result: `installed-wheel local-time smokes passed`.

## Residual Risk

The scheduling contract remains intentionally local-time and offset-free. Callers that require
cross-timezone scheduling must convert to the workspace machine's local wall-clock time before
calling the scheduler.
