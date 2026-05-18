---
name: mcp-manager
description: 统一管理 MCP Server 的连接、移除和工具调用。当用户想要添加/连接/移除/删除 MCP Server，查看某个 MCP Server 上某个工具的参数，或调用该工具时使用此 skill。即使用户没有明确提到 "mcp-manager"，只要涉及 MCP Server 管理或工具调用，都应该使用此 skill。触发词包括"添加MCP"、"连接MCP"、"移除MCP"、"调用工具"等。另外，当 CLAUDE.md 中列出了可用工具，且用户的任务需要使用这些工具时，也应主动使用此 skill 来执行调用。
---

# MCP Manager

通过 mcp2cli 管理 MCP Server 并调用工具。mcp2cli 将 MCP Server 转化为 CLI 命令，无需编写代码即可连接、发现和调用工具。

## 环境检查

首次使用前，确认 mcp2cli 可用：

```bash
mcp2cli --version
```

如果未安装，执行安装：

```bash
uv tool install mcp2cli
# 或
pip install mcp2cli
```

## 意图识别

根据用户意图选择对应操作：

| 意图 | 操作 | 参考文档 |
|------|------|----------|
| 同步 MCP Server | sync.sh（对齐 mcp-manager.json + 刷新 CLAUDE.md） | 阅读 `references/sync-servers.md` |
| 查看已连接的 MCP Server / 查看工具列表 | bake list / @name --list | 阅读 `references/list-servers.md` |
| 添加/连接新的 MCP Server | bake create + 刷新摘要 | 阅读 `references/add-server.md` |
| 移除/删除 MCP Server | bake remove + 刷新摘要 | 阅读 `references/remove-server.md` |
| 查看工具参数 / 调用工具 | @name tool --help / @name tool --params | 阅读 `references/call-tool.md` |
