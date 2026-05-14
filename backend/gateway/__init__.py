import json
import logging

from mcp.server.fastmcp import FastMCP

from backend.database import get_db
from backend.services import server_manager
from backend.services.mcp_client import call_tool_on_server

logger = logging.getLogger(__name__)

gateway_mcp = FastMCP(
    name="MCP Gateway",
    instructions=(
        "MCP Gateway提供元工具来访问所有已注册的MCP Servers。"
        "工作流程：先用 list_tools 或 discover_tools 了解可用工具，"
        "再用 get_tool_schema 获取具体参数格式，最后用 invoke_tool 执行调用。"
    ),
    stateless_http=True,
)

@gateway_mcp.tool(
    name="list_tools",
    description="列出所有已注册 MCP Servers 下的工具。返回每个工具的 server_name、tool_name、description（不含 inputSchema 以节省 token）。",
)
async def meta_list_tools() -> str:
    db = await get_db()
    tools = await server_manager.list_all_tools_with_server(db)
    if not tools:
        return "当前没有已注册的工具。请先在管理界面添加 MCP Server。"
    return json.dumps(tools, ensure_ascii=False)


@gateway_mcp.tool(
    name="discover_tools",
    description="根据简体中文的意图描述进行语义搜索，返回最匹配的工具列表（含相似度分数）。适合在意图较为明确时使用。",
)
async def meta_discover_tools(intent: str) -> str:
    from backend.gateway.embedding import cosine_search

    db = await get_db()
    candidates = await server_manager.list_all_tools_with_embeddings(db)

    has_embeddings = any(c[4] for c in candidates)
    if not has_embeddings:
        return "工具尚未生成 embedding 向量，无法进行语义搜索。请使用 list_tools 查看所有工具。"

    results = cosine_search(intent, candidates, top_k=5)
    if not results:
        return "未找到匹配的工具。"
    return json.dumps(results, ensure_ascii=False)


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
