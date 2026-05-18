# 查看工具详情与调用工具

## 工作流

调用工具分两步：先了解参数，再执行调用。不要跳过第一步直接调用，因为参数名和格式可能与工具描述不完全一致。

### 第一步：确定目标

查看 CLAUDE.md 中 `<!-- MCP_GATEWAY_TOOLS_START -->` 区域内的工具摘要，找到目标 server-name 和 tool-name。

也可以用搜索缩小范围：

```bash
mcp2cli @<server-name> --search "<关键词>"
```

### 第二步：获取工具参数详情

```bash
mcp2cli @<server-name> <tool-name> --help
```

这会显示工具的所有参数、类型、是否必填等信息。仔细阅读输出，了解每个参数的含义和格式要求。

### 第三步：执行调用

```bash
mcp2cli @<server-name> <tool-name> --param1 value1 --param2 value2
```

注意事项：
- 对于可能返回大量数据的调用，使用 `--head N` 限制返回条数
- 字符串参数值如果包含空格，需要用引号包裹
- JSON 类型的参数，传入 JSON 字符串：`--complex-param '{"key": "value"}'`

### 示例

```bash
# 搜索工作项相关的工具
mcp2cli @coop --search "workitem"

# 查看 "查询工作项详情" 工具的参数
mcp2cli @coop query_workitem_detail --help

# 调用工具
mcp2cli @coop query_workitem_detail --id 12345 --pretty

# 搜索代码
mcp2cli @code search_code --query "authentication" --repo "foo/bar" --head 5
```
