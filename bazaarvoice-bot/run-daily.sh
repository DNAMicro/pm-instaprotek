#!/usr/bin/env bash
# Scheduled entry point for Sarah's bazaarvoice-bot.js.
#
# cron gets almost no environment, so PATH and HOME are set explicitly here rather than
# relying on a login shell. Flags passed to this script are forwarded to the bot, so a manual
# `./run-daily.sh --rehearse` overrides the daily behaviour without editing the crontab.
#
# --post      the bot is dry run by default; without this nothing is ever published
# --headless  config.json sets headless:false for desktop use, and cron has no display
# --limit     paces the backlog. See SCHEDULE-AND-ACCOUNT.md for why this is not unlimited.
set -uo pipefail

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export HOME="${HOME:-/home/farsheed}"
export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/v24.15.0/bin:/usr/local/bin:/usr/bin:/bin"

DAILY_LIMIT="${BV_DAILY_LIMIT:-25}"

# The bot reads the FIRST --limit it sees, so only supply the default when the caller has not
# passed one of their own. Otherwise `./run-daily.sh --limit 2` would be silently ignored.
LIMIT_ARGS=(--limit "$DAILY_LIMIT")
for arg in "$@"; do
  if [[ "$arg" == "--limit" ]]; then LIMIT_ARGS=(); break; fi
done

LOG_DIR="$BOT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date +%Y-%m-%d).log"

{
  echo "=============================================================="
  echo "run start $(date -Iseconds)"
  node "$BOT_DIR/bazaarvoice-bot.js" --post --headless "${LIMIT_ARGS[@]}" "$@"
  echo "run end $(date -Iseconds) exit=$?"
} >> "$LOG_FILE" 2>&1

# Keep 30 days of logs and run folders.
find "$LOG_DIR" -name '*.log' -mtime +30 -delete 2>/dev/null
find "$BOT_DIR/runs" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} + 2>/dev/null
