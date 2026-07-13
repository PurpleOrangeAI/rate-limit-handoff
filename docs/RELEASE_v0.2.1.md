# rate-limit-handoff v0.2.1 — Release-Truth Repair

v0.1 began as a scheduler and evolved overnight into the broader v0.2 multi-model
continuity design. v0.2.1 turns that design into shipped, tested behavior.

## Shipped

- Same-model waiting with optional explicit auto-run at the supplied reset time.
- Immediate cross-model handoff with an optional explicit destination command.
- Temporary switching with a planned return and optional explicit return command.
- One canonical Active Handoff Chain in handoff.md.
- Durable active state, JSONL transition history, private job records, and result logs.
- --handoff, --from, --to, --return-to, --return-at, --prefer, --auto-run,
  --command, and --return-command.
- Consistent 0.2.1 source, package, wheel, and CLI version metadata.

## Safety and truth boundary

- Commands are user-supplied and run with shell=False.
- Provider commands are never inferred.
- The supplied reset time is the availability proxy; there is no live provider-
  availability detection.
- Detached scheduled jobs are local and best-effort across machine uptime, not reboot
  durable.
- PyPI publication is not included in this release; the first PyPI release is pending.

## Verification

Release verification requires pytest, Ruff, mypy, package build, clean wheel install,
same/cross/return CLI smoke tests, a near-future scheduled command, live tag inspection,
and a green GitHub Actions run.
