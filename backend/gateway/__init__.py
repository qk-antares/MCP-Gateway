import json

from mcp.server.fastmcp import FastMCP

from backend.database import get_db
from backend.services import server_manager
from backend.services.mcp_client import call_tool_on_server

gateway_mcp = FastMCP(
    name="MCP Gateway",
    instructions=(
        "MCP Gateway提供元工具来访问所有已注册的MCP Servers。"
        "所有可用工具的摘要已注入上下文，无需额外发现。"
        "工作流程：用 get_tool_schema 获取具体参数格式，"
        "再用 invoke_tool 执行调用。"
    ),
    stateless_http=True,
)


@gateway_mcp.tool(
    name="get_tool_schema",
    description="获取指定工具的完整JSON Schema。在调用 invoke_tool 之前使用，了解工具需要的参数。",
)
async def meta_get_tool_schema(server_name: str, tool_name: str) -> str:
    db = await get_db()
    tool = await server_manager.get_tool_with_schema(db, server_name, tool_name)
    if not tool:
        return f"未找到工具：server_name={server_name}, tool_name={tool_name}"
    return json.dumps(tool, ensure_ascii=False)


@gateway_mcp.tool(
    name="invoke_tool",
    description="调用指定 MCP Server 上的工具。arguments 为 JSON 字符串，包含工具所需的参数。",
)
async def meta_invoke_tool(server_name: str, tool_name: str, arguments: str) -> str:
    db = await get_db()
    srv = await server_manager.get_server_by_name(db, server_name)
    if not srv:
        return f"未找到 MCP Server：{server_name}"

    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        return f"arguments 不是合法的 JSON：{arguments}"

    return await call_tool_on_server(srv.id, tool_name, args)
