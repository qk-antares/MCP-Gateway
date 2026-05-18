# 移除 MCP Server

## 流程

### 1. 确认要移除的 Server

查看当前已连接的 Server：

```bash
mcp2cli bake list
```

向用户确认要移除的 Server 名称。

### 2. 执行 bake remove

```bash
mcp2cli bake remove <name>
```

### 3. 刷新工具摘要到 CLAUDE.md

```bash
python3 <SKILL_DIR>/scripts/refresh.py $PROJECT_ROOT
```

其中 `<SKILL_DIR>` 是此 skill 所在的目录（根据 SKILL.md 的加载路径推导）。

刷新后该 Server 的工具将从 CLAUDE.md 中移除。
