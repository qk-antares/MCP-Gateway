#!/bin/sh
# SessionStart hook: 检查环境、同步 MCP Server 状态、输出工具摘要到 Claude 上下文。

set -eu

PROJECT_ROOT="$(pwd)"
PROJECT_CONFIG="$PROJECT_ROOT/mcp-manager.json"
USER_CONFIG="$HOME/.mcp-manager.json"

# 验证 JSON 文件：存在且合法且包含 mcpServers 对象，且每个条目完整
validate_config() {
  file="$1"
  [ ! -f "$file" ] && return 1
  jq empty "$file" 2>/dev/null || return 1
  jq -e '.mcpServers | type == "object"' "$file" >/dev/null 2>&1 || return 1
  invalid=$(jq -r '.mcpServers | to_entries[] | select(
    (.value | type != "object") or
    ((.value.type // "http") == "http" and ((.value.url // "") == "")) or
    ((.value.type // "") == "stdio" and ((.value.command // "") == ""))
  ) | .key' "$file" 2>/dev/null)
  [ -n "$invalid" ] && return 1
  return 0
}

# 移除 settings.json 中的 allowedMcpServers 配置
remove_allowed_mcp_servers() {
  settings_file="$PROJECT_ROOT/.claude/settings.json"
  if [ -f "$settings_file" ] && command -v jq >/dev/null 2>&1; then
    tmp_file=$(mktemp)
    jq 'del(.allowedMcpServers)' "$settings_file" > "$tmp_file" && mv "$tmp_file" "$settings_file"
  fi
}

# 提前将 uv 及相关工具的默认安装路径加入 PATH
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# ── 1. 环境检查：uv ──
if ! command -v uv >/dev/null 2>&1; then
  uv_tag=$(curl -s https://api.github.com/repos/astral-sh/uv/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
  curl -LsSf "http://ghp.alibaba-inc.com/https://github.com/astral-sh/uv/releases/download/${uv_tag}/uv-installer.sh" -o /tmp/uv-installer.sh
  UV_INSTALLER_GITHUB_BASE_URL="http://ghp.alibaba-inc.com/https://github.com" sh /tmp/uv-installer.sh >/dev/null 2>&1
  rm -f /tmp/uv-installer.sh
  mkdir -p "$HOME/.config/uv"
  cat > "$HOME/.config/uv/uv.toml" << 'UVCONF'
python-install-mirror = "https://registry.npmmirror.com/-/binary/python-build-standalone"
allow-insecure-host = ["yum.tbsite.net"]
index-url = "http://yum.tbsite.net/aliyun-pypi/simple/"
extra-index-url = ["http://yum.tbsite.net/pypi/simple/"]
UVCONF
  command -v uv >/dev/null 2>&1 || exit 0
fi

uv tool update-shell >/dev/null 2>&1 || true

# ── 2. 环境检查：mcp2cli ──
if ! command -v mcp2cli >/dev/null 2>&1; then
  uv tool install --force mcp2cli >/dev/null 2>&1
  if ! command -v mcp2cli >/dev/null 2>&1; then
    remove_allowed_mcp_servers
    exit 0
  fi
fi

# ── 3. 环境检查：jq ──
command -v jq >/dev/null 2>&1 || HAS_JQ=false
HAS_JQ=${HAS_JQ:-true}

# ── 4. 同步 bake 状态（需要 jq）──
if [ "$HAS_JQ" = true ]; then
  proj_valid=false
  user_valid=false
  validate_config "$PROJECT_CONFIG" && proj_valid=true
  validate_config "$USER_CONFIG" && user_valid=true

  if [ "$proj_valid" = true ] || [ "$user_valid" = true ]; then
    proj_json='{"mcpServers":{}}'
    user_json='{"mcpServers":{}}'
    [ "$proj_valid" = true ] && proj_json=$(cat "$PROJECT_CONFIG")
    [ "$user_valid" = true ] && user_json=$(cat "$USER_CONFIG")

    merged=$(jq -n \
      --argjson p "$proj_json" \
      --argjson u "$user_json" \
      '$p.mcpServers * $u.mcpServers')

    declared=$(echo "$merged" | jq -r 'keys[]' | sort)

    baked=$(mcp2cli bake list 2>/dev/null | awk '
      /^Name/ || /^---/ || /^$/ { next }
      $2 == "mcp" || $2 == "openapi" || $2 == "graphql" || $2 == "stdio" { print $1 }
    ' | sort)

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

      eval "$create_cmd" >/dev/null 2>&1 || true
    done

    # bake remove
    if [ -n "$baked" ]; then
      for name in $baked; do
        [ -z "$name" ] && continue
        if [ -z "$declared" ] || ! echo "$declared" | grep -qx "$name"; then
          mcp2cli bake remove "$name" >/dev/null 2>&1 || true
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

[ -z "$servers" ] && exit 0

summary=""
for server in $servers; do
  tools=$(mcp2cli "@${server}" --list 2>/dev/null | sed -n 's/^  \([a-z][a-z0-9_-]*\)  \{1,\}/  \1: /p')
  if [ -n "$tools" ]; then
    summary="${summary}[${server}]
${tools}
"
  fi
done

[ -z "$summary" ] && exit 0

START="<!-- MCP_MANAGER_TOOLS_START -->"
END="<!-- MCP_MANAGER_TOOLS_END -->"

echo "$START"
echo "# MCP Manager 可用工具"
echo ""
echo "你可以通过mcp-manager Skill调用以下外部工具:"
echo ""
echo "$summary"
echo "$END"
echo "注意：${START} 和 ${END} 之间的工具摘要在 /compact 压缩上下文时可以全部丢弃"
