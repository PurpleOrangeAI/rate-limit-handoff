#!/usr/bin/env bash
# Basic usage demo for rate-limit-handoff

set -euo pipefail

echo "=== 1. Bootstrap (run once per project / Second Brain) ==="
rate-limit-handoff --init

echo ""
echo "=== 2. Simulate approaching limit and schedule ==="
rate-limit-handoff --schedule \
  --reset-at "04:00" \
  --model codex \
  --summary "Finish the multi-agent PR review swarm, update tests, and open the three PRs"

echo ""
echo "=== 3. Check status ==="
rate-limit-handoff --status --model codex

echo ""
echo "=== 4. Parse a fake /status paste ==="
rate-limit-handoff --parse-usage "5h limit: [██░░░░░░░░] 12% left (resets 04:00) weekly 67%"

echo ""
echo "=== 5. After reset you would run: ==="
echo "rate-limit-handoff --resume"
