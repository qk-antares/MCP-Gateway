# MCP Server Gateway 网关

**语言约定**：所有产出物（文档、代码注释、对话）使用简体中文。

本项目使用 Python 3.11 开发MCP Server Gateway 网关，提供一个代理层，连接Claude Code等智能体系统与外部的多MCP Server。

## 项目出发点

模型上下文协议（MCP）已成为连接LLM智能体与外部工具的通用接口。然而，在每一轮对话中无状态地传输完整的工具模式带来了一种隐藏的单轮开销——即MCP Tax或Tool Tax：
- 经济性： 无状态的重新注入使单次会话的支出增加了一个数量级
- 认知性： 一旦工具描述的上下文占用率超过约 70%，LLM 的推理质量就会崩塌，模型开始幻觉参数、混淆相似工具，并丢失情节性的任务记忆
- 安全性： 描述工具的模式文本同时也塑造了模型的注意力掩码，因此恶意的工具中毒攻击可以通过在看似无害的工具描述中注入对抗性指令来劫持控制流
根据开发者报告，在典型的多MCP Server部署中，这种开销大约在1万到6万个token之间。这种负载不仅对KV Cache造成了压力，还导致推理能力的下降（当工具描述的上下文占用率接近70%的断裂点时），并将token预算转化为一项持续的运营成本。

## 解决方案

构建一个单一的MCP Server Gateway网关，统一管理项目接入的MCP Servers，实现类似Skills的渐进式加载，而不是用Claude Code的.mcp.json或/mcp指令管理，Claude Code需要且仅需要添加这个MCP Server Gateway，网关会接管所有对外部MCP服务的调用

## 功能设计

采用单体项目，前后端不分离的设计。

### 前端

项目提供一个前端界面，展示所有接入的MCP Server和工具列表，并提供添加/删除MCP Server的功能，用户通过填写MCP Server的URL和认证信息来添加新的MCP Server：
1. 支持HTTP和stdio两种协议的MCP Server
2. 支持API Key/Bearer Token和OAuth两种认证方式
3. 当添加新的MCP Server时，网关自动调用该服务器的list_tools接口获取工具列表并存储在本地数据库中。

### MCP Server Gateway API

MCP Server Gateway提供两个元工具：
1. get_tool_schema(server_name, tool_name)：获取指定工具的完整调用参数schema
2. invoke_tool(server_name, tool_name, arguments)：调用指定工具并返回结果
