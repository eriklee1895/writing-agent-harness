#!/usr/bin/env bash
# precheck.sh — L1-minimal: only verify lark-cli binary is installed and runnable.
#
# This skill assumes the calling agent already has the lark-doc / lark-whiteboard /
# lark-shared skills available. We do NOT check for them because skill install paths
# vary by agent (Claude Code uses ~/.claude/skills/, others differ).
#
# If lark-cli is missing, we point the user at the upstream GitHub project and exit
# non-zero so the agent can decide whether to ask the user to install it manually.

set -euo pipefail

if ! command -v lark-cli >/dev/null 2>&1; then
  cat >&2 <<'EOF'
ERROR: lark-cli not found in PATH.

To use markdown-article-to-feishu-doc you need:

  1. lark-cli         — Lark/Feishu CLI (this binary)
       Install:  npm install -g @larksuite/cli
       Source:   https://github.com/larksuite/cli
       Verify:   lark-cli --version

  2. lark-cli auth login
       (interactive; agent cannot do this for you)

  3. lark-* skills installed in your agent
       Required: lark-doc, lark-whiteboard, lark-shared
       Install command varies by agent:
         - Claude Code:  npx skills add lark-doc lark-whiteboard lark-shared
         - other agents: see your agent's docs

Re-run this skill after lark-cli is on PATH.
EOF
  exit 1
fi

# Best-effort version probe. Do not fail hard if the --version flag shape changes
# in a future lark-cli release; just warn and continue.
if VERSION_LINE="$(lark-cli --version 2>&1)"; then
  echo "OK: ${VERSION_LINE}"
else
  echo "WARN: 'lark-cli --version' failed; binary present but may be misconfigured." >&2
fi

echo "NOTE: precheck does not verify lark-doc / lark-whiteboard / lark-shared skills."
echo "      The calling agent must ensure those are installed before invoking this skill."
