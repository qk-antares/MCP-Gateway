import asyncio

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from backend.database import get_db
from backend.models.schemas import (
    CreateServerRequest,
    ServerListResponse,
    ServerResponse,
    ToolListResponse,
)
from backend.services import server_manager
from backend.services.mcp_client import (
    _server_token_stores,
    connect_and_sync_tools,
    get_oauth_flow,
    resolve_oauth_callback,
)

router = APIRouter(prefix="/api", tags=["servers"])


@router.get("/servers", response_model=ServerListResponse)
async def list_servers():
    db = await get_db()
    servers = await server_manager.list_servers(db)
    return ServerListResponse(servers=servers)


@router.post("/servers", response_model=ServerResponse, status_code=201)
async def create_server(req: CreateServerRequest):
    if req.transport_type == "http" and not req.url:
        raise HTTPException(status_code=422, detail="HTTP 类型必须提供 url")
    if req.transport_type == "stdio" and not req.command:
        raise HTTPException(status_code=422, detail="stdio 类型必须提供 command")

    db = await get_db()
    server = await server_manager.create_server(db, req)
    # 后台异步连接 MCP Server 并获取工具列表
    asyncio.create_task(connect_and_sync_tools(server.id))
    return ServerResponse(server=server)


@router.delete("/servers/{server_id}")
async def delete_server(server_id: int):
    db = await get_db()
    deleted = await server_manager.delete_server(db, server_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Server 不存在")
    _server_token_stores.pop(server_id, None)
    return {"ok": True}


@router.get("/servers/{server_id}/tools", response_model=ToolListResponse)
async def list_server_tools(server_id: int):
    db = await get_db()
    server = await server_manager.get_server(db, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server 不存在")
    tools = await server_manager.list_tools_by_server(db, server_id)
    return ToolListResponse(tools=tools)


@router.get("/servers/{server_id}/oauth-url")
async def get_oauth_url(server_id: int):
    """获取待完成 OAuth 授权的 URL（前端轮询此接口，获取到后在新窗口打开）。"""
    flow = get_oauth_flow(server_id)
    if not flow:
        return {"oauth_url": None}
    if not flow.auth_url_ready.is_set():
        return {"oauth_url": None}
    return {"oauth_url": flow.auth_url}


@router.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request):
    """OAuth 授权回调端点。浏览器授权完成后重定向到此处。"""
    code = request.query_params.get("code", "")
    state = request.query_params.get("state", "")

    if not code or not state:
        return HTMLResponse("<h3>授权失败：缺少必要参数</h3>", status_code=400)

    ok = resolve_oauth_callback(state, code)
    if not ok:
        return HTMLResponse("<h3>授权失败：无效的 state 参数</h3>", status_code=400)

    return HTMLResponse(
        "<h3>授权成功！</h3><p>此窗口可以关闭。</p>"
        "<script>window.close()</script>"
    )
