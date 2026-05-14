import logging
import struct

import numpy as np

logger = logging.getLogger(__name__)

_model = None
_MODEL_NAME = "all-MiniLM-L6-v2"
_EMBEDDING_DIM = 384


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("加载 Embedding 模型: %s", _MODEL_NAME)
        try:
            _model = SentenceTransformer(_MODEL_NAME, local_files_only=True)
        except Exception:
            _model = SentenceTransformer(_MODEL_NAME)
    return _model


def generate_embedding(text: str) -> bytes:
    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return struct.pack(f"{_EMBEDDING_DIM}f", *vec.tolist())


def generate_embeddings_batch(texts: list[str]) -> list[bytes]:
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return [struct.pack(f"{_EMBEDDING_DIM}f", *v.tolist()) for v in vecs]


def _bytes_to_vec(data: bytes) -> np.ndarray:
    return np.array(struct.unpack(f"{_EMBEDDING_DIM}f", data), dtype=np.float32)


async def ensure_all_embeddings() -> None:
    """为所有缺失 embedding 的工具生成向量。启动时或同步后调用。"""
    from backend.database import get_db
    from backend.services import server_manager

    db = await get_db()
    rows = await (await db.execute(
        "SELECT id, name, description FROM tools WHERE embedding IS NULL"
    )).fetchall()
    if not rows:
        return

    logger.info("为 %d 个工具补生成 embedding...", len(rows))
    texts = [f"{r['name']}: {r['description'] or ''}" for r in rows]
    embeddings = generate_embeddings_batch(texts)

    tool_embeddings = [(r["id"], emb) for r, emb in zip(rows, embeddings)]
    await server_manager.update_tool_embeddings(db, tool_embeddings)
    logger.info("embedding 补全完成")


def cosine_search(
    query: str,
    candidates: list[tuple[int, str, str | None, str, bytes]],
    top_k: int = 5,
) -> list[dict]:
    """语义搜索。

    candidates: [(tool_id, tool_name, description, server_name, embedding_bytes), ...]
    返回 top-k 匹配结果（按相似度降序）。
    """
    if not candidates:
        return []

    query_vec = _bytes_to_vec(generate_embedding(query))

    scored = []
    for tool_id, name, desc, server_name, emb_bytes in candidates:
        if not emb_bytes:
            continue
        vec = _bytes_to_vec(emb_bytes)
        score = float(np.dot(query_vec, vec))
        scored.append((score, tool_id, name, desc, server_name))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            "server_name": item[4],
            "tool_name": item[2],
            "description": item[3] or "",
            "score": round(item[0], 4),
        }
        for item in scored[:top_k]
    ]
