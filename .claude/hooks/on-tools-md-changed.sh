#!/bin/sh
# FileChanged hook: 当 .claude/TOOLS.md 变更时，将最新内容注入模型上下文。

LOG="/tmp/claude-tools-md-hook.log"

input=$(cat)
file_path=$(echo "$input" | jq -r '.file_path // ""')
event=$(echo "$input" | jq -r '.event // ""')
content=$(cat "$file_path" 2>/dev/null || echo "")

echo "$(date) [on-tools-md-changed] event=$event file=$file_path" content=$content>> "$LOG"

echo "$content" | jq -Rs '{hookSpecificOutput: {hookEventName: "FileChanged", additionalContext: .}}'
