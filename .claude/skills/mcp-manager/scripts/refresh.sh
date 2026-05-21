#!/bin/sh
# 从 mcp2cli bake 获取所有已连接 MCP Server 的工具摘要，写入 CLAUDE.md。
# 用法: sh refresh.sh <project_root>

set -eu

START="<!-- MCP_MANAGER_TOOLS_START -->"
END="<!-- MCP_MANAGER_TOOLS_END -->"

if [ $# -lt 1 ]; then
  echo "用法: bash refresh.sh <project_root>" >&2
  exit 1
fi

PROJECT_ROOT="$1"
CLAUDE_MD="$PROJECT_ROOT/.claude/TOOLS.md"

# 获取所有 baked server 名称（每行一个）
get_baked_servers() {
  mcp2cli bake list 2>/dev/null | awk '
    /^Name/ || /^---/ || /^$/ { next }
    $2 == "mcp" || $2 == "openapi" || $2 == "graphql" || $2 == "stdio" { print $1 }
  '
}

# 获取某个 server 的工具列表，输出 "  tool-name: description" 格式
get_server_tools() {
  server="$1"
  mcp2cli "@${server}" --list 2>/dev/null | sed -n 's/^  \([a-z][a-z0-9_-]*\)  \{1,\}/  \1: /p'
}

# 构建摘要
build_summary() {
  echo "$1" | while read -r server; do
    [ -z "$server" ] && continue
    tools=$(get_server_tools "$server")
    if [ -n "$tools" ]; then
      echo "[$server]"
      echo "$tools"
    fi
  done
}

# 写入 CLAUDE.md
update_claude_md() {
  summary="$1"

  if [ -n "$summary" ]; then
    block="${START}

# MCP Manager 可用工具

你可以通过mcp-manager Skill调用以下外部工具:

${summary}

${END}"
  else
    block="${START}

暂无已连接的 MCP Server。

${END}"
  fi

  if [ ! -f "$CLAUDE_MD" ]; then
    printf '\n%s\n' "$block" > "$CLAUDE_MD"
    return
  fi

  if grep -qF "$START" "$CLAUDE_MD"; then
    # 替换已有区块：用 sed 删除 START 到 END 之间的内容，再插入新块
    # 先取 START 之前的内容
    before=$(sed "/$START/,\$d" "$CLAUDE_MD")
    # 取 END 之后的内容
    after=$(sed "1,/$END/d" "$CLAUDE_MD")
    printf '%s\n%s\n%s' "$before" "$block" "$after" > "$CLAUDE_MD"
  else
    # 追加到末尾
    printf '%s\n\n%s\n' "$(cat "$CLAUDE_MD")" "$block" > "$CLAUDE_MD"
  fi
}

# 主流程
servers=$(get_baked_servers)

if [ -z "$servers" ]; then
  echo "未发现已 bake 的 MCP Server"
  update_claude_md ""
  exit 0
fi

server_count=$(echo "$servers" | wc -l | tr -d ' ')
server_list=$(echo "$servers" | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')
echo "发现 ${server_count} 个 baked MCP Server: ${server_list}"

summary=$(build_summary "$servers")
update_claude_md "$summary"

tool_count=$(echo "$summary" | grep -c '^  ' || true)
echo "已刷新 ${tool_count} 个工具摘要到 ${CLAUDE_MD}"
