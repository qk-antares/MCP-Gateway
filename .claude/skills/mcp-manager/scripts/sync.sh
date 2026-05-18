#!/bin/sh
# 根据 mcp-manager.json 同步 bake 状态，然后刷新 CLAUDE.md。
# 用法: sh sync.sh <project_root>

set -eu

if [ $# -lt 1 ]; then
  echo "用法: sh sync.sh <project_root>" >&2
  exit 1
fi

PROJECT_ROOT="$1"
CONFIG="$PROJECT_ROOT/mcp-manager.json"
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

# 从 mcp-manager.json 获取声明的 server 列表（文件不存在则为空）
if [ -f "$CONFIG" ]; then
  declared=$(jq -r '.servers | keys[]' "$CONFIG" 2>/dev/null | sort)
else
  declared=""
fi

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
  type=$(jq -r --arg n "$name" '.servers[$n].type // "http"' "$CONFIG")
  auth=$(jq -r --arg n "$name" '.servers[$n].auth // "none"' "$CONFIG")

  if [ "$type" = "stdio" ]; then
    cmd=$(jq -r --arg n "$name" '.servers[$n].command // ""' "$CONFIG")
    if [ -z "$cmd" ]; then
      echo "[sync] 跳过 $name: stdio 类型缺少 command"
      continue
    fi
    create_cmd="mcp2cli bake create $name --mcp-stdio \"$cmd\""
    # 添加环境变量
    env_vars=$(jq -r --arg n "$name" '.servers[$n].env // {} | to_entries[] | "\(.key)=\(.value)"' "$CONFIG" 2>/dev/null)
    for ev in $env_vars; do
      create_cmd="$create_cmd --env $ev"
    done
  else
    url=$(jq -r --arg n "$name" '.servers[$n].url // ""' "$CONFIG")
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
      auth_header=$(jq -r --arg n "$name" '.servers[$n].auth_header // ""' "$CONFIG")
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
