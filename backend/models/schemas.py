from pydantic import BaseModel, Field


class CreateServerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    transport_type: str = Field(..., pattern=r"^(http|stdio)$")
    url: str | None = None
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    auth_type: str | None = Field("none", pattern=r"^(none|api_key|bearer|oauth)$")
    auth_config: dict | None = None


class ToolInfo(BaseModel):
    id: int
    name: str
    description: str | None = None


class ServerInfo(BaseModel):
    id: int
    name: str
    transport_type: str
    url: str | None = None
    command: str | None = None
    auth_type: str | None = None
    status: str
    error_message: str | None = None
    tool_count: int = 0
    created_at: str
    updated_at: str


class ServerListResponse(BaseModel):
    servers: list[ServerInfo]


class ServerResponse(BaseModel):
    server: ServerInfo


class ToolListResponse(BaseModel):
    tools: list[ToolInfo]
