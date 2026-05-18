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
uvx mcp2cli --help
# 或
pip install mcp2cli
```

## 意图识别

根据用户意图选择对应操作：

| 意图 | 操作 | 参考文档 |
|------|------|----------|
| 添加/连接新的 MCP Server | bake create + 刷新摘要 | 阅读 `references/add-server.md` |
| 移除/删除 MCP Server | bake remove + 刷新摘要 | 阅读 `references/remove-server.md` |
| 查看工具参数 / 调用工具 | @name tool --help / @name tool --params | 阅读 `references/call-tool.md` |

## 查看当前已连接的 MCP Server

```bash
mcp2cli bake list
```

CLAUDE.md 中 `<!-- MCP_GATEWAY_TOOLS_START -->` 和 `<!-- MCP_GATEWAY_TOOLS_END -->` 之间列出了所有已连接 Server 的工具摘要（name + description），格式为：

```
[server-name]
  tool-name: 工具描述
```

在调用工具前，先查看 CLAUDE.md 中的摘要确定目标 server-name 和 tool-name。
