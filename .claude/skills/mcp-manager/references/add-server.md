# 添加 MCP Server

## 流程

### 1. 收集连接信息

向用户确认以下信息：
- **名称**：为这个 Server 起一个简短的名称（用于 `mcp2cli @name` 引用）
- **协议类型**：HTTP（`--mcp <url>`）还是 stdio（`--mcp-stdio "<command>"`）
- **认证方式**：无认证 / Bearer Token / API Key / OAuth

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

### 4. 更新 mcp-manager.json

将新 Server 信息写入项目配置文件，确保下次 Session 启动时自动同步：

**HTTP 类型**：
```bash
jq --arg name "<name>" --argjson entry '{"type":"http","url":"<url>","auth":"<auth>"}' \
  '.mcpServers[$name] = $entry' $PROJECT_ROOT/mcp-manager.json > /tmp/mcp-manager.tmp \
  && mv /tmp/mcp-manager.tmp $PROJECT_ROOT/mcp-manager.json
```

**stdio 类型**：
```bash
jq --arg name "<name>" --argjson entry '{"type":"stdio","command":"<command>","auth":"none"}' \
  '.mcpServers[$name] = $entry' $PROJECT_ROOT/mcp-manager.json > /tmp/mcp-manager.tmp \
  && mv /tmp/mcp-manager.tmp $PROJECT_ROOT/mcp-manager.json
```

如果 `mcp-manager.json` 不存在，先创建：
```bash
echo '{"mcpServers":{}}' > $PROJECT_ROOT/mcp-manager.json
```

### 5. 刷新工具摘要到 .claude/CLAUDE.md

```bash
sh <SKILL_DIR>/scripts/refresh.sh $PROJECT_ROOT
```

其中 `<SKILL_DIR>` 是此 skill 所在的目录（根据 SKILL.md 的加载路径推导）。
