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
    await init_db()
    async with gateway_mcp.session_manager.run():
        yield
    await close_db()


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
