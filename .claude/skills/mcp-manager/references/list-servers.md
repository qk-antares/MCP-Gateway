# 查看已连接的 MCP Server

## 查看所有已连接的 MCP Server

```bash
mcp2cli bake list
```

输出为表格格式，包含 Name、Type、Source 三列。如果没有已连接的 Server，输出 "No baked tools."。

## 查看某个 MCP Server 下的工具列表

```bash
mcp2cli @<server-name> --list
```

输出该 Server 提供的所有工具名称和描述。

也可以用关键词搜索工具：

```bash
mcp2cli @<server-name> --search "<关键词>"
```

### 示例

```bash
# 查看所有已连接的 Server
mcp2cli bake list

# 查看 code 这个 Server 下有哪些工具
mcp2cli @code --list

# 搜索包含 "issue" 关键词的工具
mcp2cli @code --search "issue"
```
