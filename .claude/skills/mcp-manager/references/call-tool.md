# 查看工具详情与调用工具

## 工作流

调用工具分两步：先了解参数，再执行调用。不要跳过第一步直接调用，因为参数名和格式可能与工具描述不完全一致。

### 第一步：确定目标

`<!-- MCP_MANAGER_TOOLS_START -->` 和 `<!-- MCP_MANAGER_TOOLS_END -->` 之间列出了所有已连接 MCP Server 的工具摘要，格式为：

```
[server-name]
  tool-name: 工具描述
```

先根据工具摘要确定目标 server-name 和 tool-name。

### 第二步：获取工具参数详情

```bash
mcp2cli @<server-name> <tool-name> --help
```

这会显示工具的所有参数、类型、是否必填等信息。仔细阅读输出，了解每个参数的含义和格式要求。

### 第三步：执行调用

```bash
mcp2cli @<server-name> <tool-name> --param1 value1 --param2 value2 | jq .
```

始终管道到 `jq .` 以确保中文等非 ASCII 字符正确显示（mcp2cli 输出的 JSON 默认使用 `\uXXXX` 转义）。

注意事项：
- 字符串参数值如果包含空格，需要用引号包裹
- JSON 类型的参数，传入 JSON 字符串：`--complex-param '{"key": "value"}'`

### 示例

```bash
# 查看 "查询工作项详情" 工具的参数
mcp2cli @coop query_workitem_detail --help

# 调用工具
mcp2cli @coop query_workitem_detail --id 12345 | jq .
```
