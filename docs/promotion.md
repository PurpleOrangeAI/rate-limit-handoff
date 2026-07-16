# Promotion & Launch Guide

How to get eyes on `rate-limit-handoff` and build reputation.

> **Version:** v0.2.1 — "Release-Truth Repair" (released 2026-07-14)
> **Canonical source:** Second Brain → `10 Projects/ai-rate-limit-handoff/Rate Limit Handoff v0.2 Social Strategy and Posts.md`
> **Repo:** https://github.com/PurpleOrangeAI/rate-limit-handoff

## Central story

> Rate limits aren't a scheduling problem. They're a **continuity** problem.

Message order:

1. A serious AI session contains operating state that chat history alone cannot reliably preserve.
2. Waiting, silently downgrading, and switching providers without a handoff all destroy momentum or quality.
3. The tool gives the operator three explicit choices: **same-model wait**, **cross-model handoff**, or **temporary switch with planned return**.
4. A living `handoff.md` and a dated Second Brain note preserve the exact next action, decisions, constraints, and evidence.
5. The overnight v0.1 → v0.2 evolution proves the real category is *multi-model continuity*, not merely scheduling.

**Outcome:** Context stops evaporating. Knowledge compounds.
**Principle:** Prefer schedule / handoff over silent fallback.

## Publication gate

**VERIFIED FOR PUBLICATION:** v0.2.1 is live at
https://github.com/PurpleOrangeAI/rate-limit-handoff/releases/tag/v0.2.1.

The live tag reports package version 0.2.1 and contains the same-model, cross-model,
planned-return, resume-preference, and explicit auto-run commands. Clean-wheel smoke
tests verified immediate handoff, scheduled same-model execution, and planned return.

Auto-run remains local and best-effort across machine uptime; it uses the supplied
reset time rather than live provider-availability detection.

> As of the v0.2.1 closeout, **no post below has been published or scheduled.** PyPI
> publication is still pending — do not claim `pip install rate-limit-handoff` works
> until that ships.

## Launch checklist

### 1. Repo polish
- [x] Clean README with badges, architecture diagram, multi-tool table
- [x] MIT license
- [x] `pyproject.toml` + installable CLI (reports `0.2.1`)
- [x] Skills for major tools
- [x] CHANGELOG
- [x] Tests (87 pytest passing, ruff + mypy clean)
- [x] `.gitignore` + CI (Python 3.10 & 3.13)

### 2. GitHub setup — done
Repo is public and tagged: `PurpleOrangeAI/rate-limit-handoff` @ `v0.2.1`.

### 3. Pending
- [ ] PyPI publish (see below) — until then, install is from source/wheel only
- [ ] Publish the posts (this doc) — fresh introduction, none live yet

---

## Posts (copy-paste ready)

Audience reality: treat this as a **first introduction**. v0.1 X/LinkedIn got little
traction, Substack reached five subscribers, and the r/ClaudeCode submission was
deleted under moderator review — so there's no meaningful public launch to build on.

### X — single post

```
Rate limits aren’t a scheduling problem. They’re a continuity problem.

rate-limit-handoff preserves the work so you can wait for your model, hand off to another provider, or switch and return.

v0.1 last night → v0.2 this morning.

github.com/PurpleOrangeAI/rate-limit-handoff
```

### X — thread (6 posts)

**1/6**
```
Rate limits aren’t really a scheduling problem. They’re a continuity problem.

When a strong AI session hits a limit, the hard part isn’t waiting. It’s preserving enough operating state for the next model—or the same model later—to continue correctly. 🧵
```

**2/6**
```
Chat history is not an operating system.

A serious session accumulates decisions, rejected paths, constraints, file state, test evidence, unresolved questions, and one exact next move.

A useful handoff must preserve that—not merely summarize the conversation.
```

**3/6**
```
rate-limit-handoff gives you three deliberate paths:

1. Wait for the same model and resume with full power.
2. Hand off now to a different provider or model.
3. Switch temporarily, then return to the original model.

No silent downgrade. No context reconstruction.
```

**4/6**
```
Every schedule or handoff updates a living handoff.md, writes a dated Second Brain note, and creates a clear resume path.

Context stops evaporating. Knowledge compounds.

The project state becomes the bridge between Claude, Codex, Grok, Antigravity, Cursor, and Hermes.
```

**5/6**
```
The product changed overnight.

v0.1 scheduled work for the next model window. By morning, v0.2 had become a multi-model continuity system: same-model wait, cross-model handoff, and planned return.

The real problem was bigger than scheduling.
```

**6/6**
```
The principle is simple:

Prefer schedule / handoff over silent fallback.

Rate limits become routing decisions instead of quality drops or lost sessions.

Open source, MIT:
github.com/PurpleOrangeAI/rate-limit-handoff
```

### LinkedIn — personal

```
Rate limits are not really a scheduling problem. They are a continuity problem.

When a long Claude Code, Codex, Grok, or Antigravity session is finally coherent, it contains much more than chat history.

It contains decisions and rejected paths. Temporary constraints. File and repository state. Test evidence. Unresolved questions. One very specific next move.

Then the model hits a limit.

Most people do one of three things:

1. Stop and lose momentum.
2. Continue on a weaker model and accept lower-quality reasoning.
3. Switch providers and try to reconstruct the operating state from memory or a transcript.

None of those is a good continuity system.

rate-limit-handoff is designed to give the operator three explicit paths:

• Same-model wait — park the work cleanly and resume on the same model when its next window opens.
• Cross-model handoff — instantly hand the exact next action and critical context to a different model.
• Return later — switch temporarily, then return to the original model for the work it does best.

Every schedule or handoff updates a living handoff.md, writes a permanent dated note into the Second Brain, and creates a clear resume path.

A summary is not enough. A useful handoff tells the next capable agent exactly what to do, what not to repeat, and how to verify the continuation.

The product itself changed overnight.

I released v0.1 last night as a way to schedule work for the next model window. By morning, the idea had become larger and more useful than I initially imagined. People do not only wait for one model. They move constantly between Claude, Codex, Grok, Antigravity, Cursor, and other systems.

That is why v0.2 became a multi-model continuity system rather than just a scheduler.

The larger principle is simple:

Prefer schedule / handoff over silent fallback.

Context stops evaporating. Knowledge compounds.

https://github.com/PurpleOrangeAI/rate-limit-handoff
```

### LinkedIn — company

```
AI rate limits are not merely a scheduling problem. They are a continuity problem.

When a model becomes unavailable, teams usually wait, silently downgrade, or switch providers and reconstruct the work from chat history.

rate-limit-handoff is designed around three explicit continuity modes:

• Same-model wait — preserve the work and resume with the same model.
• Cross-model handoff — move the exact next action and critical context to another provider or model.
• Planned return — switch temporarily, then return to the original model.

The continuity layer is deliberately simple: one living handoff.md, one dated Second Brain record, and one clear resume path.

v0.1 began last night as a rate-limit scheduler. By morning, v0.2 had evolved into a broader multi-model continuity system.

The teams that win will not be the ones that never hit limits. They will be the ones that treat limits as routing decisions instead of quality drops or lost sessions.

Open source and MIT licensed:
https://github.com/PurpleOrangeAI/rate-limit-handoff
```

### Substack

**Title:** Rate Limits Are a Continuity Problem
**Subtitle:** How rate-limit-handoff evolved overnight from a scheduler into a multi-model continuity system.

```
You know the moment.

A long AI session is finally coherent. The model understands the architecture. It knows which approaches were rejected and why. The tests are beginning to expose the real problem. The next move is precise.

Then the usage window closes.

The visible problem is the rate limit. The durable problem is what happens to the work next.

Most operators choose between three bad defaults:

1. Stop and wait, losing momentum.
2. Fall back to a weaker model, even when the remaining work still requires strong reasoning.
3. Switch to another provider and reconstruct the operating state from memory or chat history.

The third option is increasingly common. Builders move between Claude Code, Codex, Grok, Antigravity, Cursor, Hermes, and other systems according to availability and task fit.

But chat history is not an operating system.

A serious session accumulates more than conversation. It accumulates decisions and rejected paths, temporary constraints, file and repository state, test evidence, unresolved questions, and a very specific next move.

A summary is not enough. A summary explains what happened. A useful handoff tells the next capable agent exactly what to do, what not to repeat, and how to verify that the continuation is correct.

That is the problem rate-limit-handoff is designed to solve.

Three continuity modes

The system gives the operator three deliberate paths instead of an improvised model switch.

Same-model wait

Park the work cleanly and resume on the same model when its next window opens. This is the maximum-quality path when the task still benefits from that model’s reasoning and the delay is acceptable.

Cross-model handoff

Move the exact next action and critical context to a different provider or model immediately. The work continues without asking the next system to reverse-engineer the session.

Return later

Switch temporarily for the work another model can handle, then return to the original model for review, architecture, or another high-value stage.

The mechanism stays deliberately boring.

Every schedule or handoff updates a living handoff.md, writes a permanent dated note into the Second Brain, and creates a clear resume path.

The project state—not the transcript—becomes the bridge.

Context stops evaporating. Knowledge compounds.

What changed overnight

I released v0.1 last night with a narrower idea: when a model’s capacity is low, preserve the work and schedule it for the next full-power window.

That solved a real problem, but it was not the whole problem.

The same night, the product became better than I had originally imagined. The real operating pattern was not simply “wait for Claude” or “wait for Codex.” Builders constantly route work across models. One model may be unavailable. Another may be better for implementation. The original model may still be the right choice for final review.

By morning, v0.2 had evolved around that reality: same-model wait, cross-model handoff, and planned return.

The evolution matters because it changed the category. This is not only a rate-limit scheduler. It is a small, model-agnostic continuity layer for serious AI work.

The larger principle

High-compute models will continue to have windows, quotas, temporary promotions, and changing economics. Trying to build a workflow that never encounters a limit is the wrong objective.

The teams that win will not be the ones that never hit limits. They will be the ones that treat limits as routing decisions instead of quality drops or lost sessions.

Prefer schedule / handoff over silent fallback.

rate-limit-handoff is open source and MIT licensed:

https://github.com/PurpleOrangeAI/rate-limit-handoff

Try it, inspect it, break it, or contribute a better continuity pattern.
```

### Reddit — r/ClaudeCode

**Title:** Open source: preserve project context when Claude Code hits a limit or work moves to another model

```
I built a small open-source tool called rate-limit-handoff for a recurring Claude Code problem: a session is finally coherent, the limit arrives, and the next session or model has to reconstruct the work from chat history.

The core idea is that chat history is evidence, not operating state.

A useful handoff should preserve:

- the objective and exact next action
- decisions and rejected approaches
- files changed and commands already run
- test and verification evidence
- constraints, risks, and unresolved questions

The intended v0.2 workflow has three modes:

1. Same-model wait: park the work and resume with Claude when the next window opens.
2. Cross-model handoff: move the exact next action and critical context to Codex, Grok, Antigravity, or another available model.
3. Planned return: use another model temporarily, then return to Claude for review or higher-value reasoning.

The tool keeps one living handoff.md as the source of truth and can also write a dated note into an existing Obsidian-style Second Brain.

The first version was only a scheduler. Overnight, the design evolved into a broader multi-model continuity layer because the real problem was not waiting—it was preserving state while routing work.

It is pure Python, offline-first, and MIT licensed.

Repository:
https://github.com/PurpleOrangeAI/rate-limit-handoff

I would value technical feedback on the handoff format, failure modes, and the minimum state you would want preserved before moving a real Claude Code task to another model.
```

---

## Distribution record

| Channel | v0.1 status | Audience signal | v0.2 treatment |
|---|---|---|---|
| X | Posted 2026-07-12 | Little traction | Fresh introduction |
| LinkedIn | Personal + company published | Little traction | Fresh introduction |
| Substack | Published | Five subscribers | New v0.2 article |
| Reddit r/ClaudeCode | Under review, then deleted | No meaningful launch | First real Reddit launch; ready, not submitted |

## Link & tracking rule

Canonical link: https://github.com/PurpleOrangeAI/rate-limit-handoff

Before publication, use a verified Starling short link **only if** the campaign is live.
Do not invent a short link. If tracking is unavailable, use the canonical repository URL
and record that limitation.

## Ongoing

- Reply to every issue/PR quickly (reputation signal)
- Add new tools as they appear
- Keep README sharp

## Positioning

**Not** "another AI wrapper".
**Yes** "the missing continuity layer that turns rate limits into Second Brain growth".
