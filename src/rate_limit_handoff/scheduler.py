"""Core LimitScheduler – the heart of rate-limit-handoff."""

from __future__ import annotations

import datetime as dt
import json
import re
import shlex
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any

from .models import MODELS, resolve_model


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
        self.handoff = self.workspace / "handoff.md"
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
        for d in (self.inbox, self.projects, self.logs, self.handoff.parent, self.skills):
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

        with open(self.handoff, "a", encoding="utf-8") as f:
            f.write(block)

        if self.handoff.exists():
            content = self.handoff.read_text(encoding="utf-8")
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
            self.handoff.write_text(content, encoding="utf-8")
        print(f"[ok] Updated {self.handoff}")

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
        filename = self.inbox / f"{date_str}-{note_kind}-{model}-{time_str}.md"

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
            "handoff": str(self.handoff),
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
    ) -> None:
        reset_dt = self.next_reset(reset_at)
        model = model.lower()
        print(
            f"Scheduling for: {reset_dt.strftime('%Y-%m-%d %H:%M')}  "
            f"(in {(reset_dt - self.now()).total_seconds() / 60:.0f} min)  model={model}"
        )
        self.append_to_handoff(summary, reset_dt, model=model)
        self.write_second_brain_note(summary, reset_dt, model=model)
        self.try_schedule_system_job(reset_dt, summary)
        print("\n✅ Done. When the limit resets, just open handoff.md and continue.")
        print("   Or run:  rate-limit-handoff --resume")

    def resume(self) -> None:
        if not self.handoff.exists():
            print("No handoff.md found in current workspace.")
            print(f"Looked in: {self.handoff}")
            return
        print("=" * 60)
        print("HANDOFF RESUME")
        print("=" * 60)
        content = self.handoff.read_text(encoding="utf-8")
        print(content[:4000])
        if len(content) > 4000:
            print("\n... (truncated — open the full file)")
        print("\n" + "=" * 60)
        print("Paste the following into your AI after the reset:\n")
        print(
            '> Read handoff.md completely. Continue exactly from the "Pending / In-Progress Work"'
        )
        print(
            '> and "Next Exact Action" sections. Rate limits have reset. '
            "Do not fall back to weaker models."
        )
        print("=" * 60)

    def status(self, model: str | None = None) -> None:
        n = self.now()
        reset = self.next_reset(None)
        print(f"Local time      : {n.strftime('%Y-%m-%d %H:%M:%S')}")
        print(
            f"Next default reset: {reset.strftime('%Y-%m-%d %H:%M')}  "
            f"({(reset - n).total_seconds() / 3600:.1f} h)"
        )
        print(f"Workspace       : {self.workspace}")
        print(f"Handoff exists  : {self.handoff.exists()}")
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
