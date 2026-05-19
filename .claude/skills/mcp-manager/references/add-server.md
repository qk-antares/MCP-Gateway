# 添加 MCP Server

## 流程

### 1. 收集连接信息

向用户确认以下信息：
- **名称**：为这个 Server 起一个简短的名称（用于 `mcp2cli @name` 引用）
- **协议类型**：HTTP（`--mcp <url>`）还是 stdio（`--mcp-stdio "<command>"`）
- **认证方式**：无认证 / Bearer Token / API Key / OAuth
- **级别**：项目级（默认）还是用户级：
  - **项目级**（默认）：写入 `$PROJECT_ROOT/mcp-manager.json`，仅当前项目生效
  - **用户级**：写入 `~/.mcp-config.json`，对所有项目生效。用户表达"全局/用户级/global/-g/--global/所有项目通用"等意图时，视为用户级。未明确指定时默认项目级。

### 2. 执行 bake create

根据协议和认证方式组合命令：

**HTTP + 无认证**：
```bash
mcp2cli bake create <name> --mcp <url>
```

**HTTP + Bearer Token**：
```bash
mcp2cli bake create <name> --mcp <url> --auth-header "Authorization:Bearer env:<ENV_VAR_NAME>"
```

**HTTP + API Key**：
```bash
mcp2cli bake create <name> --mcp <url> --auth-header "x-api-key:env:<ENV_VAR_NAME>"
```

**HTTP + OAuth**：
```bash
mcp2cli bake create <name> --mcp <url> --oauth
```

**stdio**：
```bash
mcp2cli bake create <name> --mcp-stdio "<command> <args...>"
```

**stdio + 环境变量**：
```bash
mcp2cli bake create <name> --mcp-stdio "<command>" --env API_KEY=env:MY_SECRET
```

安全提醒：认证凭据始终使用 `env:` 前缀从环境变量读取，不要在命令中写入明文密码。

### 3. 验证连接

```bash
mcp2cli @<name> --list
```

确认能看到工具列表。如果连接失败，检查 URL、认证信息是否正确。

### 4. 更新配置文件

根据级别选择目标文件：

```bash
# 项目级（默认）
TARGET="$PROJECT_ROOT/mcp-manager.json"
# 用户级（-g）
TARGET="~/.mcp-config.json"
```

**HTTP 类型**：
```bash
(cat "$TARGET" 2>/dev/null || echo '{"mcpServers":{}}') | \
  jq --arg name "<name>" --argjson entry '{"type":"http","url":"<url>","auth":"<auth>"}' \
  '.mcpServers[$name] = $entry' > /tmp/mcp-manager.tmp && mv /tmp/mcp-manager.tmp "$TARGET"
```

**stdio 类型**：
```bash
(cat "$TARGET" 2>/dev/null || echo '{"mcpServers":{}}') | \
  jq --arg name "<name>" --argjson entry '{"type":"stdio","command":"<command>","auth":"none"}' \
  '.mcpServers[$name] = $entry' > /tmp/mcp-manager.tmp && mv /tmp/mcp-manager.tmp "$TARGET"
```

### 5. 刷新工具摘要到 .claude/CLAUDE.md

```bash
sh <SKILL_DIR>/scripts/refresh.sh $PROJECT_ROOT
```

其中 `<SKILL_DIR>` 是此 skill 所在的目录（根据 SKILL.md 的加载路径推导）。
