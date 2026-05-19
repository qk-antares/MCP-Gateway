#!/bin/sh
# 根据项目级 mcp-manager.json + 用户级 ~/.mcp-config.json 同步 bake 状态，然后刷新 CLAUDE.md。
# 两级配置取并集，同名 server 用户级优先。
# 用法: sh sync.sh <project_root>

set -eu

if [ $# -lt 1 ]; then
  echo "用法: sh sync.sh <project_root>" >&2
  exit 1
fi

PROJECT_ROOT="$1"
PROJECT_CONFIG="$PROJECT_ROOT/mcp-manager.json"
USER_CONFIG="$HOME/.mcp-config.json"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 环境检查：确认 mcp2cli 可用
if ! command -v mcp2cli >/dev/null 2>&1; then
  echo "[sync] mcp2cli 未安装，尝试安装..."
  if command -v uv >/dev/null 2>&1; then
    uv tool install mcp2cli
  elif command -v pip >/dev/null 2>&1; then
    pip install mcp2cli
  else
    echo "[sync] 无法安装 mcp2cli（uv 和 pip 均不可用），跳过同步" >&2
    exit 0
  fi
fi

# jq 不可用时降级：只刷新，不同步（避免误删）
if ! command -v jq >/dev/null 2>&1; then
  echo "[sync] jq 未安装，跳过同步，仅刷新工具摘要"
  sh "$SCRIPT_DIR/refresh.sh" "$PROJECT_ROOT"
  exit 0
fi

# 合并两级配置（用户级覆盖项目级）
merged=$(jq -n \
  --argjson p "$(cat "$PROJECT_CONFIG" 2>/dev/null || echo '{"mcpServers":{}}')" \
  --argjson u "$(cat "$USER_CONFIG" 2>/dev/null || echo '{"mcpServers":{}}')" \
  '$p.mcpServers * $u.mcpServers')

# 期望的 server 列表
declared=$(echo "$merged" | jq -r 'keys[]' | sort)

# 获取当前已 bake 的 server 列表
baked=$(mcp2cli bake list 2>/dev/null | awk '
  /^Name/ || /^---/ || /^$/ { next }
  $2 == "mcp" || $2 == "openapi" || $2 == "graphql" || $2 == "stdio" { print $1 }
' | sort)

# 需要添加的：在 declared 中但不在 baked 中
to_add=""
if [ -n "$declared" ]; then
  for name in $declared; do
    if ! echo "$baked" | grep -qx "$name"; then
      to_add="$to_add $name"
    fi
  done
fi

# 需要移除的：在 baked 中但不在 declared 中
to_remove=""
if [ -n "$baked" ]; then
  for name in $baked; do
    if [ -z "$declared" ] || ! echo "$declared" | grep -qx "$name"; then
      to_remove="$to_remove $name"
    fi
  done
fi

# 执行 bake create
for name in $to_add; do
  [ -z "$name" ] && continue
  type=$(echo "$merged" | jq -r --arg n "$name" '.[$n].type // "http"')
  auth=$(echo "$merged" | jq -r --arg n "$name" '.[$n].auth // "none"')

  if [ "$type" = "stdio" ]; then
    cmd=$(echo "$merged" | jq -r --arg n "$name" '.[$n].command // ""')
    if [ -z "$cmd" ]; then
      echo "[sync] 跳过 $name: stdio 类型缺少 command"
      continue
    fi
    create_cmd="mcp2cli bake create $name --mcp-stdio \"$cmd\""
    env_vars=$(echo "$merged" | jq -r --arg n "$name" '.[$n].env // {} | to_entries[] | "\(.key)=\(.value)"' 2>/dev/null)
    for ev in $env_vars; do
      create_cmd="$create_cmd --env $ev"
    done
  else
    url=$(echo "$merged" | jq -r --arg n "$name" '.[$n].url // ""')
    if [ -z "$url" ]; then
      echo "[sync] 跳过 $name: http 类型缺少 url"
      continue
    fi
    create_cmd="mcp2cli bake create $name --mcp $url"
  fi

  case "$auth" in
    oauth)
      create_cmd="$create_cmd --oauth"
      ;;
    bearer|apikey)
      auth_header=$(echo "$merged" | jq -r --arg n "$name" '.[$n].auth_header // ""')
      if [ -n "$auth_header" ]; then
        create_cmd="$create_cmd --auth-header \"$auth_header\""
      fi
      ;;
  esac

  echo "[sync] 添加: $name"
  eval "$create_cmd" 2>/dev/null || echo "[sync] 添加 $name 失败"
done

# 执行 bake remove
for name in $to_remove; do
  [ -z "$name" ] && continue
  echo "[sync] 移除: $name"
  mcp2cli bake remove "$name" 2>/dev/null || true
done

# 刷新 CLAUDE.md
sh "$SCRIPT_DIR/refresh.sh" "$PROJECT_ROOT"
