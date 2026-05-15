import aiosqlite

from backend.config import DATA_DIR, DB_PATH

_db: aiosqlite.Connection | None = None

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS mcp_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    transport_type TEXT NOT NULL CHECK (transport_type IN ('http', 'stdio')),
    url TEXT,
    command TEXT,
    args TEXT,
    env TEXT,
    auth_type TEXT CHECK (auth_type IN ('none', 'api_key', 'bearer', 'oauth')),
    auth_config TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    oauth_state TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    input_schema TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (server_id) REFERENCES mcp_servers(id) ON DELETE CASCADE,
    UNIQUE(server_id, name)
);
"""


_MIGRATIONS = [
    "ALTER TABLE mcp_servers ADD COLUMN oauth_state TEXT",
]


async def init_db() -> None:
    global _db
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _db = await aiosqlite.connect(str(DB_PATH))
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL")
    await _db.execute("PRAGMA foreign_keys=ON")
    await _db.executescript(_SCHEMA_SQL)
    for sql in _MIGRATIONS:
        try:
            await _db.execute(sql)
        except Exception:
            pass
    await _db.commit()


async def get_db() -> aiosqlite.Connection:
    assert _db is not None, "数据库未初始化，请先调用 init_db()"
    return _db


async def close_db() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None
