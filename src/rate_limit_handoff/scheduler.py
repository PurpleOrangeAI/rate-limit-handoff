"""Core LimitScheduler – the heart of rate-limit-handoff."""

from __future__ import annotations

import datetime as dt
import json
import re
import shlex
import shutil
import subprocess
import textwrap
from dataclasses import replace
from pathlib import Path
from typing import Any

from .continuity import ContinuityStore, HandoffState
from .models import MODELS, resolve_model
from .runner import create_job, execute_job, spawn_waiting_job


class LimitScheduler:
    """
    Schedule remaining AI work for the next rate-limit window.

    Creates / updates:
    - living handoff.md
    - Second Brain inbox note
    - optional system job / resume script
    """

    def __init__(
        self,
        workspace: Path | None = None,
        second_brain_root: Path | None = None,
        default_reset_hour: int = 4,
        default_reset_minute: int = 0,
    ) -> None:
        self.workspace = Path(workspace).resolve() if workspace else Path.cwd()
        self.handoff_path = self.workspace / "handoff.md"
        local_second_brain = self.workspace / "second_brain"
        self.second_brain = (
            Path(second_brain_root).resolve() if second_brain_root else local_second_brain
        )
        uses_obsidian_layout = all(
            (self.second_brain / directory).is_dir() for directory in ("00 Inbox", "10 Projects")
        )
        if uses_obsidian_layout:
            self.inbox = self.second_brain / "00 Inbox"
            self.projects = self.second_brain / "10 Projects" / "ai-rate-limit-handoff"
            self.second_brain_link = "10 Projects/ai-rate-limit-handoff/README"
        else:
            self.inbox = self.second_brain / "inbox"
            self.projects = self.second_brain / "projects" / "ai-rate-limit-handoff"
            self.second_brain_link = "projects/ai-rate-limit-handoff/README"
        self.logs = local_second_brain / "logs"
        self.skills = local_second_brain / "system" / "skills"
        self.default_reset_hour = default_reset_hour
        self.default_reset_minute = default_reset_minute
        self.continuity = ContinuityStore(self.workspace, now=self.now)

    # ── Time helpers ──────────────────────────────────────────────────────────

    def now(self) -> dt.datetime:
        return dt.datetime.now()

    def next_reset(self, at_str: str | None = None) -> dt.datetime:
        n = self.now()
        if at_str is None:
            target = n.replace(
                hour=self.default_reset_hour,
                minute=self.default_reset_minute,
                second=0,
                microsecond=0,
            )
            if target <= n:
                target += dt.timedelta(days=1)
            return target

        at_str = at_str.strip()
        try:
            if len(at_str) <= 5 and ":" in at_str:  # HH:MM
                h, m = map(int, at_str.split(":"))
                target = n.replace(hour=h, minute=m, second=0, microsecond=0)
                if target <= n:
                    target += dt.timedelta(days=1)
                return target
            return dt.datetime.fromisoformat(at_str)
        except Exception as e:
            print(f"[warn] Could not parse --reset-at '{at_str}': {e}. Falling back to default.")
            return self.next_reset(None)

    def ensure_dirs(self) -> None:
        for d in (self.inbox, self.projects, self.logs, self.handoff_path.parent, self.skills):
            d.mkdir(parents=True, exist_ok=True)

    # ── Usage parsing ─────────────────────────────────────────────────────────

    def parse_usage_text(self, text: str) -> dict[str, Any]:
        """
        Best-effort parser for pasted /status, dashboard, or quota messages.
        Handles common patterns from Codex, Claude Code, Antigravity, etc.
        """
        result: dict[str, Any] = {
            "raw": text.strip(),
            "5h_remaining_pct": None,
            "weekly_remaining_pct": None,
            "reset_hint": None,
            "source": None,
        }

        pct_matches = re.findall(r"(\d{1,3})\s*%\s*(?:left|remaining|avail)", text, re.I)
        if pct_matches:
            result["5h_remaining_pct"] = int(pct_matches[0])
            if len(pct_matches) > 1:
                result["weekly_remaining_pct"] = int(pct_matches[1])

        reset_m = re.search(r"resets?\s+(?:in\s+)?([\d:hm\s]+|[\d]{1,2}:[\d]{2})", text, re.I)
        if reset_m:
            result["reset_hint"] = reset_m.group(1).strip()

        agy_m = re.search(r"Resets in\s+([\dhms\s]+)", text, re.I)
        if agy_m:
            result["reset_hint"] = agy_m.group(1).strip()
            result["source"] = "antigravity"

        codex_m = re.search(
            r"5h\s*(?:limit)?[:\s].*?(\d+)%\s*left\s*\(resets?\s*([\d:]+)\)", text, re.I
        )
        if codex_m:
            result["5h_remaining_pct"] = int(codex_m.group(1))
            result["reset_hint"] = codex_m.group(2)
            result["source"] = "codex"

        return result

    # ── Handoff + Second Brain writers ────────────────────────────────────────

    def append_to_handoff(
        self,
        summary: str,
        reset_dt: dt.datetime,
        scheduled: bool = True,
        model: str = "unknown",
    ) -> None:
        self.ensure_dirs()
        ts = self.now().strftime("%Y-%m-%d %H:%M")
        reset_str = reset_dt.strftime("%Y-%m-%d %H:%M")
        block_title = "Scheduled Continuation" if scheduled else "Handoff Update"
        reset_label = "Reset time" if scheduled else "Reference time"
        action_heading = "Exact next action after reset" if scheduled else "Continuation"
        action_prompt = (
            'Or paste into AI: "Continue exactly from the Pending section of handoff.md. '
            'Limits have reset. Prefer full-power model."'
            if scheduled
            else 'Or paste into AI: "Continue from the latest Handoff Update in handoff.md."'
        )

        block = textwrap.dedent(f"""
        ---
        ## {block_title} ({ts}) — model: {model}
        **{reset_label}:** {reset_str}
        **Summary of remaining work:**
        {summary}

        **{action_heading}:**
        1. Open this handoff.md
        2. Run: `rate-limit-handoff --resume`  (or `python -m rate_limit_handoff --resume`)
        3. {action_prompt}

        **Second Brain note created:** yes (see the configured Second Brain inbox)
        """)

        with open(self.handoff_path, "a", encoding="utf-8") as f:
            f.write(block)

        if self.handoff_path.exists():
            content = self.handoff_path.read_text(encoding="utf-8")
            status = (
                f"SCHEDULED for {reset_str} ({model}) – resume after reset."
                if scheduled
                else f"ACTIVE – checkpoint updated {ts} ({model})."
            )
            content = re.sub(
                r"\*\*Status:\*\*.*",
                f"**Status:** {status}",
                content,
                count=1,
            )
            if "**Last Updated:**" in content:
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if line.startswith("**Last Updated:**"):
                        lines[i] = f"**Last Updated:** {ts}"
                        break
                content = "\n".join(lines)
            self.handoff_path.write_text(content, encoding="utf-8")
        print(f"[ok] Updated {self.handoff_path}")

    def write_second_brain_note(
        self,
        summary: str,
        reset_dt: dt.datetime,
        model: str = "unknown",
        scheduled: bool = True,
    ) -> Path:
        self.ensure_dirs()
        ts = self.now()
        date_str = ts.strftime("%Y-%m-%d")
        time_str = ts.strftime("%H%M")
        note_kind = "scheduled-handoff" if scheduled else "handoff-update"
        note_title = "Scheduled Handoff" if scheduled else "Handoff Update"
        trigger = (
            "approaching model limit (tokens / 5h window / reasoning minutes)"
            if scheduled
            else "manual checkpoint update"
        )
        time_label = "Reset at" if scheduled else "Reference time"
        command_heading = "Resume Command" if scheduled else "Continuation Command"
        command_hint = (
            f"# or just open handoff.md in your preferred model after {reset_dt.strftime('%H:%M')}"
            if scheduled
            else "# or open handoff.md in your preferred model and continue from the checkpoint"
        )
        safe_model = self._model_filename_component(model)
        filename = self.inbox / f"{date_str}-{note_kind}-{safe_model}-{time_str}.md"

        content = textwrap.dedent(f"""\
        # {note_title} – {ts.strftime("%Y-%m-%d %H:%M")} ({model})

        **{time_label}:** {reset_dt.strftime("%Y-%m-%d %H:%M")}
        **Triggered by:** {trigger}

        ## Remaining Work
        {summary}

        ## Context Snapshot
        - See root `handoff.md` for full living state
        - Project: [[{self.second_brain_link}]]
        - Model that hit limit: **{model}**

        ## {command_heading}
        ```bash
        rate-limit-handoff --resume
        {command_hint}
        ```

        ---
        *Auto-written by rate-limit-handoff so knowledge never evaporates when a limit hits.*
        """)
        filename.write_text(content, encoding="utf-8")
        print(f"[ok] Second Brain note → {filename}")
        return filename

    @staticmethod
    def _model_filename_component(model: str) -> str:
        """Return a bounded filename component without changing the recorded model."""
        safe_model = re.sub(r"[^A-Za-z0-9_-]+", "-", model).strip("-_")
        return safe_model[:80] or "unknown"

    def write_continuity_note(self, state: HandoffState) -> Path:
        self.ensure_dirs()
        timestamp = self.now()
        safe_model = self._model_filename_component(state.current_model)
        filename = self.inbox / (
            f"{timestamp.strftime('%Y-%m-%d')}-handoff-{state.mode}-"
            f"{safe_model}-{timestamp.strftime('%H%M')}.md"
        )
        lines = [
            f"# {state.mode.title()} Handoff – {timestamp.strftime('%Y-%m-%d %H:%M')}",
            "",
            f"**Status:** {state.status}",
            f"**From:** {state.source_model}",
            f"**Current model:** {state.current_model}",
            f"**Summary:** {state.summary}",
        ]
        if state.reset_at:
            lines.append(f"**Reset at:** {state.reset_at.isoformat(timespec='minutes')}")
        if state.return_to:
            lines.append(f"**Return to:** {state.return_to}")
        if state.return_at:
            lines.append(f"**Return at:** {state.return_at.isoformat(timespec='minutes')}")
        lines.extend(
            [
                "",
                "## Continue",
                "",
                "Read the workspace handoff.md and follow its Active Handoff Chain.",
                "",
                f"Project: [[{self.second_brain_link}]]",
                "",
                "---",
                "*Written by rate-limit-handoff v0.2.1.*",
                "",
            ]
        )
        filename.write_text("\n".join(lines), encoding="utf-8")
        print(f"[ok] Second Brain note → {filename}")
        return filename

    def try_schedule_system_job(self, reset_dt: dt.datetime, summary: str) -> None:
        """Best-effort local scheduler (at / cron / script)."""
        self.ensure_dirs()
        delay = (reset_dt - self.now()).total_seconds()
        if delay < 30:
            print("[info] Reset is almost now — no need to schedule far ahead.")
            return

        if shutil.which("at"):
            message = f"Resume handoff: {summary[:60]}..."
            job = (
                f"notify-send {shlex.quote('AI Limit Reset')} {shlex.quote(message)} "
                f"|| echo {shlex.quote('Reset time')}\n"
            )
            try:
                subprocess.run(
                    ["at", reset_dt.strftime("%H:%M"), reset_dt.strftime("%Y-%m-%d")],
                    input=job,
                    text=True,
                    check=True,
                )
                print(f"[ok] Scheduled via `at` for {reset_dt}")
                return
            except Exception as e:
                print(f"[warn] `at` failed: {e}")

        script = self.logs / f"resume_at_{reset_dt.strftime('%Y%m%d_%H%M')}.sh"
        script.write_text(
            textwrap.dedent(f"""\
            #!/bin/bash
            # Auto-generated by rate-limit-handoff
            # Run this (or have cron run it) at or after {reset_dt}
            cd "{self.workspace}"
            echo "=== Rate limit reset — resuming handoff ==="
            head -n 80 handoff.md
            echo ""
            echo "Open handoff.md in your AI and continue."
            notify-send "AI Limit Reset (Claude/Codex/Grok/Antigravity)" \
              "Continue from handoff.md" 2>/dev/null || true
            """)
        )
        script.chmod(0o755)
        print(f"[ok] Wrote resume script: {script}")
        print(f"     You can:  at {reset_dt.strftime('%H:%M')} -f {script}")
        print(f"     Or add to crontab:  {reset_dt.minute} {reset_dt.hour} * * * {script}")

        log_entry = {
            "scheduled_at": self.now().isoformat(),
            "resume_at": reset_dt.isoformat(),
            "summary": summary,
            "handoff": str(self.handoff_path),
        }
        log_file = self.logs / "schedule_log.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        print(f"[ok] Logged to {log_file}")

    # ── Public commands ───────────────────────────────────────────────────────

    def schedule(
        self,
        summary: str,
        reset_at: str | None = None,
        model: str = "unknown",
        *,
        auto_run: bool = False,
        command_argv: list[str] | None = None,
    ) -> int:
        if auto_run:
            self._validate_explicit_command(
                command_argv,
                "same-model auto-run requires an explicit command",
            )

        reset_dt = self.next_reset(reset_at)
        print(
            f"Scheduling for: {reset_dt.strftime('%Y-%m-%d %H:%M')}  "
            f"(in {(reset_dt - self.now()).total_seconds() / 60:.0f} min)  model={model}"
        )
        self.append_to_handoff(summary, reset_dt, model=model)
        self.write_second_brain_note(summary, reset_dt, model=model)

        created_at = self.now()
        waiting = HandoffState(
            mode="same",
            source_model=model,
            current_model=model,
            summary=summary,
            status="waiting",
            created_at=created_at,
            updated_at=created_at,
            reset_at=reset_dt,
        )
        self.continuity.record(waiting, event="same_model_wait")

        if not auto_run:
            self.try_schedule_system_job(reset_dt, summary)
            print("\nDone. Open handoff.md or run rate-limit-handoff --resume after reset.")
            return 0

        assert command_argv is not None
        resumed = replace(waiting, status="resumed", updated_at=reset_dt)
        job_path = create_job(
            logs_path=self.logs,
            workspace=self.workspace,
            mode="same",
            model=model,
            run_at=reset_dt,
            argv=command_argv,
            transition=resumed,
            now=self.now,
        )
        pid = spawn_waiting_job(job_path)
        print(f"[ok] Auto-run job: {job_path} (pid {pid})")
        print("[info] Detached local jobs are best-effort and are not reboot durable.")
        return 0

    def handoff(
        self,
        *,
        summary: str,
        from_model: str,
        to_model: str,
        return_to: str | None = None,
        return_at: str | None = None,
        auto_run: bool = False,
        command_argv: list[str] | None = None,
        return_command_argv: list[str] | None = None,
    ) -> int:
        if bool(return_to) != bool(return_at):
            raise ValueError("return_to and return_at must be supplied together")
        if auto_run:
            self._validate_explicit_command(
                command_argv,
                "cross-model auto-run requires an explicit command",
            )
            if return_to:
                self._validate_explicit_command(
                    return_command_argv,
                    "planned return auto-run requires an explicit return command",
                )

        return_dt = self.next_reset(return_at) if return_at else None
        created_at = self.now()
        state = HandoffState(
            mode="return" if return_to else "cross",
            source_model=from_model,
            current_model=to_model,
            summary=summary,
            status="temporary" if return_to else "handed_off",
            created_at=created_at,
            updated_at=created_at,
            return_to=return_to,
            return_at=return_dt,
        )
        self.continuity.record(
            state,
            event="planned_return" if return_to else "cross_handoff",
        )
        self.write_continuity_note(state)

        if not auto_run:
            print("[ok] Handoff recorded. Open handoff.md in the destination model.")
            return 0

        assert command_argv is not None
        if return_to and return_dt:
            assert return_command_argv is not None
            returned = replace(
                state,
                current_model=return_to,
                status="returned",
                updated_at=return_dt,
            )
            return_job = create_job(
                logs_path=self.logs,
                workspace=self.workspace,
                mode="return",
                model=return_to,
                run_at=return_dt,
                argv=return_command_argv,
                transition=returned,
                now=self.now,
            )
            pid = spawn_waiting_job(return_job)
            print(f"[ok] Planned return job: {return_job} (pid {pid})")
            print("[info] Detached local jobs are best-effort and are not reboot durable.")

        immediate_job = create_job(
            logs_path=self.logs,
            workspace=self.workspace,
            mode="cross",
            model=to_model,
            run_at=created_at,
            argv=command_argv,
            transition=None,
            now=self.now,
        )
        return execute_job(immediate_job, wait=False)

    @staticmethod
    def _validate_explicit_command(command_argv: list[str] | None, message: str) -> None:
        if (
            not isinstance(command_argv, list)
            or not command_argv
            or not all(isinstance(argument, str) for argument in command_argv)
            or not command_argv[0].strip()
        ):
            raise ValueError(message)

    def resume(self, prefer: str | None = None) -> int:
        if not self.handoff_path.exists():
            print("No handoff.md found in current workspace.")
            print(f"Looked in: {self.handoff_path}")
            return 0

        if prefer:
            current = self.continuity.load()
            if current:
                preferred = replace(
                    current,
                    preferred_model=prefer.lower(),
                    updated_at=self.now(),
                )
                self.continuity.record(preferred, event="resume_preference")

        print("=" * 60)
        print("HANDOFF RESUME")
        print("=" * 60)
        if prefer:
            print(f"Preferred model: {prefer.lower()}")
        content = self.handoff_path.read_text(encoding="utf-8")
        print(content[:4000])
        if len(content) > 4000:
            print("\n... (truncated — open the full file)")
        print("\n" + "=" * 60)
        preferred_text = f" Prefer {prefer.lower()}." if prefer else ""
        print("Paste the following into your AI:\n")
        print(
            '> Read handoff.md completely. Continue exactly from the "Pending / In-Progress Work"'
        )
        print(f'> and "Next Exact Action" sections.{preferred_text}')
        print("=" * 60)
        return 0

    def status(self, model: str | None = None) -> None:
        n = self.now()
        reset = self.next_reset(None)
        print(f"Local time      : {n.strftime('%Y-%m-%d %H:%M:%S')}")
        print(
            f"Next default reset: {reset.strftime('%Y-%m-%d %H:%M')}  "
            f"({(reset - n).total_seconds() / 3600:.1f} h)"
        )
        print(f"Workspace       : {self.workspace}")
        print(f"Handoff exists  : {self.handoff_path.exists()}")
        print(f"Second Brain    : {self.second_brain}")
        if model:
            info = resolve_model(model)
            if info:
                print(f"\nModel / tool info ({info.name}):")
                for k, v in info.to_dict().items():
                    print(f"  {k}: {v}")
            else:
                print(f"\nUnknown model '{model}'. Known: {', '.join(MODELS.keys())}")
        else:
            print("\nKnown tools/models:")
            for name in sorted(MODELS.keys()):
                print(f"  - {name}")

    def update_only(
        self,
        summary: str,
        reset_at: str | None = None,
        model: str = "unknown",
    ) -> None:
        reset_dt = self.next_reset(reset_at)
        self.append_to_handoff(summary, reset_dt, scheduled=False, model=model)
        self.write_second_brain_note(summary, reset_dt, model=model, scheduled=False)
        print("Updated handoff + Second Brain (no system job scheduled).")

    def codex_status(self) -> None:
        """Best-effort local Codex usage hints."""
        print("=== Codex usage (best-effort local detection) ===")
        print(
            "Note: Full live % is only available inside an active Codex CLI session via `/status`"
        )
        print("      or in the Codex app Settings → Usage panel.\n")

        candidates = [
            Path.home() / ".codex" / "sessions",
            Path.home() / ".openai" / "codex",
            Path("/tmp") / "codex",
        ]
        found = False
        for p in candidates:
            if p.exists():
                print(f"[info] Found possible Codex data: {p}")
                try:
                    files = sorted(p.glob("**/*"), key=lambda x: x.stat().st_mtime, reverse=True)[
                        :5
                    ]
                    for f in files:
                        if f.is_file():
                            mtime = dt.datetime.fromtimestamp(f.stat().st_mtime)
                            print(f"  recent: {f.name} ({mtime})")
                    found = True
                except Exception as e:
                    print(f"  (could not list: {e})")

        if not found:
            print("[info] No local ~/.codex sessions found (normal if using web/app only).")

        print("\nRecommended:")
        print("  1. Inside Codex CLI run:  /status")
        print("  2. Copy the output and run:")
        print('     rate-limit-handoff --parse-usage "PASTE HERE"')
        print('  3. Or just use --schedule --model codex --reset-at "HH:MM" when you see low %')
