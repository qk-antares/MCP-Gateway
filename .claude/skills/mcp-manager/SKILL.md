---
name: mcp-manager
description: 管理 MCP Server 的添加/移除/同步并调用其工具。当用户的任务涉及 MCP 管理、需要调用 MCP Manager 提供的外部工具、或需要访问阿里内部资源（alidocs.dingtalk.com、gitlab.alibaba-inc.com 等）时使用此 Skill。
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

| 意图 | 参考文档 |
|------|----------|
| 查看已连接的 MCP Server / 查看工具列表 | 阅读 `references/list-servers.md` |
| 添加 / 连接新的 MCP Server | 阅读 `references/add-server.md` |
| 移除 / 删除 MCP Server | 阅读 `references/remove-server.md` |
| 查看工具参数 / 调用工具  | 阅读 `references/call-tool.md` |

