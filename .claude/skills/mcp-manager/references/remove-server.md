# 移除 MCP Server

## 流程

### 1. 确认要移除的 Server

查看当前已连接的 Server：

```bash
mcp2cli bake list
```

确认要移除的 Server 名称。

### 2. 执行 bake remove

```bash
mcp2cli bake remove <name>
```

### 3. 从配置文件中删除

同时从项目级和用户级配置中删除该 Server（若存在）：

```bash
# 项目级
if [ -f "$PROJECT_ROOT/mcp-manager.json" ]; then
  jq --arg name "<name>" 'del(.mcpServers[$name])' "$PROJECT_ROOT/mcp-manager.json" > /tmp/mcp-manager.tmp \
    && mv /tmp/mcp-manager.tmp "$PROJECT_ROOT/mcp-manager.json"
fi

# 用户级
if [ -f "$HOME/.mcp-config.json" ]; then
  jq --arg name "<name>" 'del(.mcpServers[$name])' "$HOME/.mcp-config.json" > /tmp/mcp-config.tmp \
    && mv /tmp/mcp-config.tmp "$HOME/.mcp-config.json"
fi
```
