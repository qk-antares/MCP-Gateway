#!/bin/sh
# SessionStart hook: 检查环境、同步 MCP Server 状态、输出工具摘要到 Claude 上下文。

set -eu

PROJECT_ROOT="$(pwd)"
PROJECT_CONFIG="$PROJECT_ROOT/mcp-manager.json"
USER_CONFIG="$HOME/.mcp-config.json"
LOG_FILE="/tmp/mcp-sync.log"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [mcp-sync] $*" >> "$LOG_FILE"
}

# stdout 输出：同时写日志文件和返回给 Agent
output() {
  echo "$*" | tee -a "$LOG_FILE"
}

# 验证 JSON 文件：存在且合法且包含 mcpServers 对象
validate_config() {
  file="$1"
  label="$2"
  if [ ! -f "$file" ]; then
    log "$label 不存在: $file (跳过)"
    return 1
  fi
  if ! jq empty "$file" 2>/dev/null; then
    log "$label JSON 非法: $file"
    return 1
  fi
  if ! jq -e '.mcpServers | type == "object"' "$file" >/dev/null 2>&1; then
    log "$label 缺少 mcpServers 对象: $file"
    return 1
  fi
  # 检查每个 server 条目是否完整
  invalid=$(jq -r '.mcpServers | to_entries[] | select(
    (.value | type != "object") or
    ((.value.type // "http") == "http" and ((.value.url // "") == "")) or
    ((.value.type // "") == "stdio" and ((.value.command // "") == ""))
  ) | .key' "$file" 2>/dev/null)
  if [ -n "$invalid" ]; then
    log "$label 中以下 server 配置不完整，跳过整个文件: $invalid"
    return 1
  fi
  return 0
}

log "===== 开始同步 (pwd=$PROJECT_ROOT) ====="

# ── 1. 环境检查：uv ──
if ! command -v uv >/dev/null 2>&1; then
  log "uv 未安装，尝试安装..."
  uv_tag=$(curl -s https://api.github.com/repos/astral-sh/uv/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
  log "uv 最新版本: $uv_tag"
  curl -LsSf "http://ghp.alibaba-inc.com/https://github.com/astral-sh/uv/releases/download/${uv_tag}/uv-installer.sh" -o /tmp/uv-installer.sh
  UV_INSTALLER_GITHUB_BASE_URL="http://ghp.alibaba-inc.com/https://github.com" sh /tmp/uv-installer.sh >> "$LOG_FILE" 2>&1
  rm -f /tmp/uv-installer.sh
  mkdir -p "$HOME/.config/uv"
  cat > "$HOME/.config/uv/uv.toml" << 'UVCONF'
python-install-mirror = "https://registry.npmmirror.com/-/binary/python-build-standalone"
allow-insecure-host = ["yum.tbsite.net"]
index-url = "http://yum.tbsite.net/aliyun-pypi/simple/"
extra-index-url = ["http://yum.tbsite.net/pypi/simple/"]
UVCONF
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if ! command -v uv >/dev/null 2>&1; then
    log "uv 安装失败，跳过同步"
    exit 0
  fi
  log "uv 安装成功: $(uv --version)"
else
  log "uv 已就绪: $(uv --version)"
fi

# ── 2. 环境检查：mcp2cli ──
if ! command -v mcp2cli >/dev/null 2>&1; then
  log "mcp2cli 未安装，尝试安装..."
  uv tool install --force mcp2cli >> "$LOG_FILE" 2>&1
  if ! command -v mcp2cli >/dev/null 2>&1; then
    log "mcp2cli 安装失败，跳过同步"
    exit 0
  fi
  log "mcp2cli 安装成功: $(mcp2cli --version 2>/dev/null || echo 'unknown')"
else
  log "mcp2cli 已就绪: $(mcp2cli --version 2>/dev/null || echo 'unknown')"
fi

# ── 3. 环境检查：jq ──
HAS_JQ=true
if ! command -v jq >/dev/null 2>&1; then
  HAS_JQ=false
  log "jq 未安装，跳过配置同步"
else
  log "jq 已就绪: $(jq --version)"
fi

# ── 4. 同步 bake 状态（需要 jq）──
if [ "$HAS_JQ" = true ]; then
  proj_valid=false
  user_valid=false
  validate_config "$PROJECT_CONFIG" "项目级配置" && proj_valid=true
  validate_config "$USER_CONFIG" "用户级配置" && user_valid=true

  if [ "$proj_valid" = false ] && [ "$user_valid" = false ]; then
    log "无有效配置文件，跳过 bake 同步"
  else
    proj_json='{"mcpServers":{}}'
    user_json='{"mcpServers":{}}'
    [ "$proj_valid" = true ] && proj_json=$(cat "$PROJECT_CONFIG")
    [ "$user_valid" = true ] && user_json=$(cat "$USER_CONFIG")

    merged=$(jq -n \
      --argjson p "$proj_json" \
      --argjson u "$user_json" \
      '$p.mcpServers * $u.mcpServers')

    declared=$(echo "$merged" | jq -r 'keys[]' | sort)
    log "期望 servers: $(echo $declared | tr '\n' ' ')"

    baked=$(mcp2cli bake list 2>/dev/null | awk '
      /^Name/ || /^---/ || /^$/ { next }
      $2 == "mcp" || $2 == "openapi" || $2 == "graphql" || $2 == "stdio" { print $1 }
    ' | sort)
    log "已 bake servers: $(echo $baked | tr '\n' ' ')"

    # bake create
    for name in $declared; do
      [ -z "$name" ] && continue
      echo "$baked" | grep -qx "$name" && continue
      type=$(echo "$merged" | jq -r --arg n "$name" '.[$n].type // "http"')
      auth=$(echo "$merged" | jq -r --arg n "$name" '.[$n].auth // "none"')

      if [ "$type" = "stdio" ]; then
        cmd=$(echo "$merged" | jq -r --arg n "$name" '.[$n].command // ""')
        [ -z "$cmd" ] && continue
        create_cmd="mcp2cli bake create $name --mcp-stdio \"$cmd\""
        env_vars=$(echo "$merged" | jq -r --arg n "$name" '.[$n].env // {} | to_entries[] | "\(.key)=\(.value)"' 2>/dev/null)
        for ev in $env_vars; do
          create_cmd="$create_cmd --env $ev"
        done
      else
        url=$(echo "$merged" | jq -r --arg n "$name" '.[$n].url // ""')
        [ -z "$url" ] && continue
        create_cmd="mcp2cli bake create $name --mcp $url"
      fi

      case "$auth" in
        oauth) create_cmd="$create_cmd --oauth" ;;
        bearer|apikey)
          auth_header=$(echo "$merged" | jq -r --arg n "$name" '.[$n].auth_header // ""')
          [ -n "$auth_header" ] && create_cmd="$create_cmd --auth-header \"$auth_header\""
          ;;
      esac

      log "添加: $name (type=$type auth=$auth)"
      log "  cmd: $create_cmd"
      if eval "$create_cmd" >> "$LOG_FILE" 2>&1; then
        log "添加 $name 成功"
      else
        log "添加 $name 失败 (exit=$?)"
      fi
    done

    # bake remove
    if [ -n "$baked" ]; then
      for name in $baked; do
        [ -z "$name" ] && continue
        if [ -z "$declared" ] || ! echo "$declared" | grep -qx "$name"; then
          log "移除: $name"
          mcp2cli bake remove "$name" >> "$LOG_FILE" 2>&1 || true
        fi
      done
    fi
  fi
fi

# ── 5. 输出工具摘要到 stdout → Claude 上下文 ──
servers=$(mcp2cli bake list 2>/dev/null | awk '
  /^Name/ || /^---/ || /^$/ { next }
  $2 == "mcp" || $2 == "openapi" || $2 == "graphql" || $2 == "stdio" { print $1 }
')

if [ -z "$servers" ]; then
  log "无已连接的 MCP Server，不输出到 stdout"
  log "===== 同步结束 ====="
  exit 0
fi

server_count=$(echo "$servers" | wc -l | tr -d ' ')
server_list=$(echo "$servers" | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')
log "发现 ${server_count} 个 baked MCP Server: ${server_list}"

summary=""
for server in $servers; do
  log "获取工具列表: $server"
  tools=$(mcp2cli "@${server}" --list 2>/dev/null | sed -n 's/^  \([a-z][a-z0-9_-]*\)  \{1,\}/  \1: /p')
  if [ -n "$tools" ]; then
    tool_n=$(echo "$tools" | wc -l | tr -d ' ')
    log "  $server: ${tool_n} 个工具"
    summary="${summary}[${server}]
${tools}
"
  else
    log "  $server: 无工具"
  fi
done

START="<!-- MCP_MANAGER_TOOLS_START -->"
END="<!-- MCP_MANAGER_TOOLS_END -->"

if [ -n "$summary" ]; then
  tool_count=$(echo "$summary" | grep -c '^  ' || true)
  log "共 ${tool_count} 个工具摘要，输出到 stdout"

  output "$START"
  output "# MCP Manager 可用工具"
  output ""
  output "你可以通过mcp-manager Skill调用以下外部工具:"
  output ""
  output "$summary"
  output "$END"
  output "注意：${START} 和 ${END} 之间的工具摘要在 /compact 压缩上下文时可以全部丢弃"
else
  log "所有 server 均无工具，不输出到 stdout"
fi

log "===== 同步结束 ====="
