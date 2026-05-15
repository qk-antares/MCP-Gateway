import asyncio
import json
import logging
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlparse

from mcp import ClientSession
from mcp.client.auth.oauth2 import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

from backend.database import get_db
from backend.services import server_manager

logger = logging.getLogger(__name__)

OAUTH_CALLBACK_URL = "http://localhost:8000/api/oauth/callback"

class OAuthFlowState:
    """管理单个 Server 的 OAuth 授权流程状态。"""

    def __init__(self, server_id: int):
        self.server_id = server_id
        self.auth_url: str | None = None
        self.auth_url_ready = asyncio.Event()
        self.callback_received = asyncio.Event()
        self.auth_code: str | None = None
        self.auth_state: str | None = None

    async def redirect_handler(self, url: str) -> None:
        self.auth_url = url
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        state_list = params.get("state", [])
        if state_list:
            _state_to_server_id[state_list[0]] = self.server_id
        self.auth_url_ready.set()

    async def callback_handler(self) -> tuple[str, str | None]:
        await asyncio.wait_for(self.callback_received.wait(), timeout=300)
        return (self.auth_code or "", self.auth_state)


class DbTokenStorage(TokenStorage):
    """将 OAuth token 和 client_info 持久化到数据库的 TokenStorage 实现。

    数据存储在 mcp_servers.oauth_state 字段（JSON），结构：
    {"tokens": {...}, "client_info": {...}}
    """

    def __init__(self, server_id: int) -> None:
        self._server_id = server_id
        self._tokens: OAuthToken | None = None
        self._client_info: OAuthClientInformationFull | None = None
        self._loaded = False

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        db = await get_db()
        row = await (await db.execute(
            "SELECT oauth_state FROM mcp_servers WHERE id = ?", (self._server_id,)
        )).fetchone()
        if not row or not row["oauth_state"]:
            return
        try:
            state = json.loads(row["oauth_state"])
            if state.get("tokens"):
                self._tokens = OAuthToken(**state["tokens"])
            if state.get("client_info"):
                self._client_info = OAuthClientInformationFull(**state["client_info"])
        except Exception:
            logger.warning("加载 Server %d 的 OAuth 状态失败，将重新授权", self._server_id)

    async def _persist(self) -> None:
        state = {}
        if self._tokens:
            state["tokens"] = self._tokens.model_dump(mode="json", exclude_none=True)
        if self._client_info:
            state["client_info"] = self._client_info.model_dump(mode="json", exclude_none=True)
        db = await get_db()
        await db.execute(
            "UPDATE mcp_servers SET oauth_state = ? WHERE id = ?",
            (json.dumps(state), self._server_id),
        )
        await db.commit()

    async def get_tokens(self) -> OAuthToken | None:
        await self._ensure_loaded()
        return self._tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._tokens = tokens
        await self._persist()

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        await self._ensure_loaded()
        return self._client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._client_info = client_info
        await self._persist()


_pending_oauth_flows: dict[int, OAuthFlowState] = {}
_state_to_server_id: dict[str, int] = {}
_server_token_stores: dict[int, DbTokenStorage] = {}


def get_oauth_flow(server_id: int) -> OAuthFlowState | None:
    return _pending_oauth_flows.get(server_id)


def resolve_oauth_callback(state: str, code: str) -> bool:
    """处理 OAuth 回调，通知等待中的流程。"""
    server_id = _state_to_server_id.pop(state, None)
    if server_id is None:
        return False
    flow = _pending_oauth_flows.get(server_id)
    if flow is None:
        return False
    flow.auth_code = code
    flow.auth_state = state
    flow.callback_received.set()
    return True


# ── 公共连接逻辑 ──────────────────────────────────────────────


def _get_storage(server_id: int) -> DbTokenStorage:
    """获取或创建 server 的持久化 TokenStorage。"""
    if server_id not in _server_token_stores:
        _server_token_stores[server_id] = DbTokenStorage(server_id)
    return _server_token_stores[server_id]


@asynccontextmanager
async def _open_session(
    server_id: int,
    url: str,
    auth_type: str,
    auth_config: dict | None,
    server_name: str = "",
):
    """连接上游 HTTP MCP Server 并 yield 已初始化的 ClientSession。"""
    auth_config = auth_config or {}

    if auth_type in ("bearer", "api_key"):
        token = auth_config.get("token") or auth_config.get("api_key", "")
        http_client = create_mcp_http_client(headers={"Authorization": f"Bearer {token}"})
        async with http_client:
            async with streamable_http_client(url, http_client=http_client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session

    elif auth_type == "oauth":
        storage = _get_storage(server_id)

        flow_state = OAuthFlowState(server_id)
        _pending_oauth_flows[server_id] = flow_state

        client_metadata = OAuthClientMetadata(
            client_name=f"MCP Gateway ({server_name})" if server_name else "MCP Gateway",
            redirect_uris=[OAUTH_CALLBACK_URL],
            grant_types=["authorization_code"],
            response_types=["code"],
            token_endpoint_auth_method="none",
        )
        oauth_auth = OAuthClientProvider(
            server_url=url,
            client_metadata=client_metadata,
            storage=storage,
            redirect_handler=flow_state.redirect_handler,
            callback_handler=flow_state.callback_handler,
        )
        http_client = create_mcp_http_client(auth=oauth_auth)
        try:
            async with http_client:
                async with streamable_http_client(url, http_client=http_client) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        yield session
        finally:
            _pending_oauth_flows.pop(server_id, None)

    else:
        async with streamable_http_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


# ── 获取工具列表 ──────────────────────────────────────────────


async def connect_http_server(
    server_id: int,
    url: str,
    auth_type: str,
    auth_config: dict | None,
    server_name: str = "",
) -> list[dict]:
    """连接 HTTP 类型的 MCP Server 并获取工具列表。"""
    async with _open_session(server_id, url, auth_type, auth_config, server_name) as session:
        result = await session.list_tools()
        tools = []
        for t in result.tools:
            schema = t.inputSchema if isinstance(t.inputSchema, dict) else {}
            tools.append({
                "name": t.name,
                "description": t.description or "",
                "input_schema": schema,
            })
        return tools


# ── 调用上游工具 ──────────────────────────────────────────────


async def call_tool_on_server(server_id: int, tool_name: str, arguments: dict) -> str:
    """连接上游 MCP Server 并调用指定工具，返回结果文本。"""
    db = await get_db()
    server = await server_manager.get_server(db, server_id)
    if not server:
        return json.dumps({"error": f"Server id={server_id} 不存在"}, ensure_ascii=False)
    if server.status != "active":
        return json.dumps({"error": f"Server '{server.name}' 状态为 {server.status}，无法调用"}, ensure_ascii=False)

    auth_config = None
    row = await (await db.execute(
        "SELECT auth_config FROM mcp_servers WHERE id = ?", (server_id,)
    )).fetchone()
    if row and row["auth_config"]:
        auth_config = json.loads(row["auth_config"])

    if server.transport_type != "http":
        return json.dumps({"error": "当前仅支持 HTTP 类型的 MCP Server 调用"}, ensure_ascii=False)

    async with _open_session(server_id, server.url or "", server.auth_type or "none", auth_config, server.name) as session:
        result = await session.call_tool(tool_name, arguments)

        contents = []
        for item in result.content:
            if hasattr(item, "text"):
                contents.append(item.text)
            elif hasattr(item, "data"):
                contents.append(f"[二进制内容: {item.mimeType}]")
            else:
                contents.append(str(item))

        if result.isError:
            return json.dumps({"error": True, "content": contents}, ensure_ascii=False)
        return "\n".join(contents) if contents else ""


# ── 后台同步任务 ──────────────────────────────────────────────


async def connect_and_sync_tools(server_id: int) -> None:
    """后台任务：连接 MCP Server 并同步工具列表到数据库。"""
    db = await get_db()
    server = await server_manager.get_server(db, server_id)
    if not server:
        return

    try:
        auth_config = None
        row = await (await db.execute(
            "SELECT auth_config FROM mcp_servers WHERE id = ?", (server_id,)
        )).fetchone()
        if row and row["auth_config"]:
            auth_config = json.loads(row["auth_config"])

        if server.transport_type == "http":
            tools = await connect_http_server(
                server_id, server.url or "", server.auth_type or "none", auth_config, server.name
            )
        else:
            await server_manager.update_server_status(db, server_id, "error", "stdio 类型暂未实现自动连接")
            return

        await server_manager.bulk_insert_tools(db, server_id, tools)
        await server_manager.update_server_status(db, server_id, "active")
        logger.info("Server %d 连接成功，获取到 %d 个工具", server_id, len(tools))

    except Exception as e:
        logger.exception("连接 Server %d 失败", server_id)
        await server_manager.update_server_status(db, server_id, "error", str(e))
