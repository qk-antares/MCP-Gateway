import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount

from backend.api.servers import router as servers_router
from backend.config import PROJECT_ROOT
from backend.database import close_db, init_db
from backend.gateway import gateway_mcp

STATIC_DIR = PROJECT_ROOT / "frontend" / "dist"

mcp_app = gateway_mcp.streamable_http_app()


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    import asyncio

    await init_db()
    async with gateway_mcp.session_manager.run():
        # 后台补全缺失的 embedding（不阻塞启动）
        asyncio.create_task(_ensure_embeddings())
        yield
    await close_db()


async def _ensure_embeddings():
    try:
        from backend.gateway.embedding import ensure_all_embeddings
        await ensure_all_embeddings()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("启动时 embedding 补全失败")


app = FastAPI(title="MCP Gateway", description="MCP Server Gateway 网关", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(servers_router)

app.router.routes.append(Mount("/mcp", app=mcp_app))

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
