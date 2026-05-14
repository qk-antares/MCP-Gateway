import json

import aiosqlite

from backend.models.schemas import (
    CreateServerRequest,
    ServerInfo,
    ToolInfo,
)


async def create_server(db: aiosqlite.Connection, req: CreateServerRequest) -> ServerInfo:
    args_json = json.dumps(req.args) if req.args else None
    env_json = json.dumps(req.env) if req.env else None
    auth_config_json = json.dumps(req.auth_config) if req.auth_config else None

    cursor = await db.execute(
        """
        INSERT INTO mcp_servers (name, transport_type, url, command, args, env, auth_type, auth_config)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (req.name, req.transport_type, req.url, req.command, args_json, env_json, req.auth_type, auth_config_json),
    )
    await db.commit()

    row = await (await db.execute("SELECT * FROM mcp_servers WHERE id = ?", (cursor.lastrowid,))).fetchone()
    return _row_to_server_info(row, 0)


async def list_servers(db: aiosqlite.Connection) -> list[ServerInfo]:
    rows = await (
        await db.execute(
            """
            SELECT s.*, COUNT(t.id) AS tool_count
            FROM mcp_servers s
            LEFT JOIN tools t ON t.server_id = s.id
            GROUP BY s.id
            ORDER BY s.created_at DESC
            """
        )
    ).fetchall()
    return [_row_to_server_info(row, row["tool_count"]) for row in rows]


async def delete_server(db: aiosqlite.Connection, server_id: int) -> bool:
    cursor = await db.execute("DELETE FROM mcp_servers WHERE id = ?", (server_id,))
    await db.commit()
    return cursor.rowcount > 0


async def get_server(db: aiosqlite.Connection, server_id: int) -> ServerInfo | None:
    row = await (await db.execute("SELECT * FROM mcp_servers WHERE id = ?", (server_id,))).fetchone()
    if not row:
        return None
    tool_count_row = await (
        await db.execute("SELECT COUNT(*) AS cnt FROM tools WHERE server_id = ?", (server_id,))
    ).fetchone()
    return _row_to_server_info(row, tool_count_row["cnt"])


async def list_tools_by_server(db: aiosqlite.Connection, server_id: int) -> list[ToolInfo]:
    rows = await (
        await db.execute(
            "SELECT id, name, description FROM tools WHERE server_id = ? ORDER BY name",
            (server_id,),
        )
    ).fetchall()
    return [ToolInfo(id=row["id"], name=row["name"], description=row["description"]) for row in rows]


async def update_server_status(
    db: aiosqlite.Connection,
    server_id: int,
    status: str,
    error_message: str | None = None,
) -> None:
    await db.execute(
        "UPDATE mcp_servers SET status = ?, error_message = ?, updated_at = datetime('now') WHERE id = ?",
        (status, error_message, server_id),
    )
    await db.commit()


async def bulk_insert_tools(
    db: aiosqlite.Connection,
    server_id: int,
    tools: list[dict],
) -> None:
    await db.executemany(
        "INSERT OR REPLACE INTO tools (server_id, name, description, input_schema) VALUES (?, ?, ?, ?)",
        [(server_id, t["name"], t.get("description"), json.dumps(t.get("input_schema"))) for t in tools],
    )
    await db.commit()


async def list_all_tools_with_server(db: aiosqlite.Connection) -> list[dict]:
    rows = await (
        await db.execute(
            """
            SELECT t.name, t.description, s.name AS server_name
            FROM tools t
            JOIN mcp_servers s ON s.id = t.server_id
            WHERE s.status = 'active'
            ORDER BY s.name, t.name
            """
        )
    ).fetchall()
    return [
        {"server_name": row["server_name"], "tool_name": row["name"], "description": row["description"] or ""}
        for row in rows
    ]


async def list_all_tools_with_embeddings(db: aiosqlite.Connection) -> list[tuple]:
    rows = await (
        await db.execute(
            """
            SELECT t.id, t.name, t.description, s.name AS server_name, t.embedding
            FROM tools t
            JOIN mcp_servers s ON s.id = t.server_id
            WHERE s.status = 'active'
            ORDER BY s.name, t.name
            """
        )
    ).fetchall()
    return [(row["id"], row["name"], row["description"], row["server_name"], row["embedding"]) for row in rows]


async def get_tool_with_schema(
    db: aiosqlite.Connection, server_name: str, tool_name: str
) -> dict | None:
    row = await (
        await db.execute(
            """
            SELECT t.name, t.description, t.input_schema, s.name AS server_name
            FROM tools t
            JOIN mcp_servers s ON s.id = t.server_id
            WHERE s.name = ? AND t.name = ?
            """,
            (server_name, tool_name),
        )
    ).fetchone()
    if not row:
        return None
    return {
        "server_name": row["server_name"],
        "tool_name": row["name"],
        "description": row["description"] or "",
        "input_schema": json.loads(row["input_schema"]) if row["input_schema"] else {},
    }


async def get_server_by_name(db: aiosqlite.Connection, name: str) -> ServerInfo | None:
    row = await (
        await db.execute("SELECT * FROM mcp_servers WHERE name = ?", (name,))
    ).fetchone()
    if not row:
        return None
    tool_count_row = await (
        await db.execute("SELECT COUNT(*) AS cnt FROM tools WHERE server_id = ?", (row["id"],))
    ).fetchone()
    return _row_to_server_info(row, tool_count_row["cnt"])


async def update_tool_embeddings(
    db: aiosqlite.Connection,
    tool_embeddings: list[tuple[int, bytes]],
) -> None:
    await db.executemany(
        "UPDATE tools SET embedding = ? WHERE id = ?",
        [(emb, tid) for tid, emb in tool_embeddings],
    )
    await db.commit()


def _row_to_server_info(row: aiosqlite.Row, tool_count: int) -> ServerInfo:
    return ServerInfo(
        id=row["id"],
        name=row["name"],
        transport_type=row["transport_type"],
        url=row["url"],
        command=row["command"],
        auth_type=row["auth_type"],
        status=row["status"],
        error_message=row["error_message"],
        tool_count=tool_count,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
