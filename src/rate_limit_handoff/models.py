"""Model / tool definitions and metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelInfo:
    """Metadata for a supported AI coding tool / model family."""

    name: str
    window: str
    fallback: str
    notes: str
    detect: str
    cli: str | None = None
    aliases: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "window": self.window,
            "fallback": self.fallback,
            "notes": self.notes,
            "detect": self.detect,
            "cli": self.cli,
        }


# Canonical registry – extend this list as new tools appear
MODELS: dict[str, ModelInfo] = {
    "claude": ModelInfo(
        name="claude",
        window="5h rolling or fixed + weekly caps",
        fallback="5.4 / Haiku / Sonnet-light / Claude Code lighter",
        notes="Often fixed-looking at 4:00 AM for some users. Claude Code sessions show countdown.",
        detect="UI percentage / countdown timer / 'limit reached' message",
        cli=None,
        aliases=("claude-code", "anthropic", "sonnet", "opus"),
    ),
    "codex": ModelInfo(
        name="codex",
        window="5h + weekly agentic quotas (reasoning-time heavy)",
        fallback="GPT-5.4 / GPT-5.4 mini / lighter reasoning",
        notes=(
            "CLI has /status. Dashboard in settings → Usage shows % remaining + reset. "
            "Reasoning minutes burn fast. Headers: x-codex-* family in some integrations."
        ),
        detect=(
            "/status in Codex CLI, Settings → Usage panel, or session files under "
            "~/.codex/sessions"
        ),
        cli="codex",
        aliases=("openai-codex", "gpt-codex"),
    ),
    "grok": ModelInfo(
        name="grok",
        window="SuperGrok weekly + API RPS/TPM",
        fallback="Grok-3 / mini / Build lighter",
        notes="Hermes + xAI. Grok Build has its own usage % (often monthly feel).",
        detect="xAI console rate-limits page or Hermes /usage",
        cli="hermes",
        aliases=("xai", "grok-4", "grok-build"),
    ),
    "grok-build": ModelInfo(
        name="grok-build",
        window="Usage % (monthly-ish) + underlying API limits",
        fallback="lighter Grok models",
        notes="Grok Build CLI shows usage %. Unlimited marketing but practical caps exist.",
        detect="CLI usage command or console",
        cli="grok-build",
        aliases=("build",),
    ),
    "antigravity": ModelInfo(
        name="antigravity",
        window="5h refresh + weekly (heavy system prompt burn)",
        fallback="Gemini Flash / classic Gemini CLI",
        notes=(
            "agy CLI. /context shows token overhead. Extremely heavy context/tools → burns "
            "quotas fast. "
            "Resets every 5h."
        ),
        detect="agy /context or quota messages ('Individual quota reached. Resets in XhYmZs')",
        cli="agy",
        aliases=("agy", "gemini", "google-antigravity"),
    ),
    "cursor": ModelInfo(
        name="cursor",
        window="Depends on underlying model (Claude/Codex/Grok)",
        fallback="cheaper model in Cursor settings",
        notes="Cursor itself has request limits; real limiter is the backend model.",
        detect="Cursor usage indicators or model switcher",
        cli=None,
        aliases=("cursor-ai",),
    ),
}


def resolve_model(name: str) -> ModelInfo | None:
    """Resolve a model name or alias to ModelInfo."""
    key = name.lower().strip()
    if key in MODELS:
        return MODELS[key]
    for info in MODELS.values():
        if key in info.aliases:
            return info
    return None


def list_models() -> list[str]:
    return sorted(MODELS.keys())
