"""
RAG 检索：读取 build_rag_index.py 生成的索引，对查询做向量化并在本地做相似度检索。
依赖 Ollama 的 /api/embeddings，需与建库时使用同一嵌入模型。
"""
from __future__ import annotations

import json
import math
import os
from typing import Any

import requests

basedir = os.path.abspath(os.path.dirname(__file__))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
RAG_INDEX_PATH = os.getenv(
    "RAG_INDEX_PATH",
    os.path.join(basedir, "database", "rag_index", "store.json"),
)
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.25"))  # 余弦相似度阈值，过低则不当作文本依据

_store: dict[str, Any] | None = None


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def rag_index_exists() -> bool:
    return os.path.isfile(RAG_INDEX_PATH)


def load_rag_store() -> bool:
    """若索引存在则加载到内存；无文件返回 False。"""
    global _store
    if not rag_index_exists():
        _store = None
        return False
    try:
        with open(RAG_INDEX_PATH, "r", encoding="utf-8") as f:
            _store = json.load(f)
    except Exception as e:
        print("[RAG] 加载索引失败:", e)
        _store = None
        return False
    return True


def is_rag_ready() -> bool:
    if _store is not None:
        return bool(_store.get("chunks"))
    return load_rag_store() and bool(_store and _store.get("chunks"))


def ollama_embed(text: str) -> list[float]:
    text = (text or "").strip()
    if not text:
        return []
    r = requests.post(
        f"{OLLAMA_BASE_URL.rstrip('/')}/api/embeddings",
        json={"model": OLLAMA_EMBED_MODEL, "prompt": text[:8000]},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    emb = data.get("embedding")
    if not isinstance(emb, list):
        return []
    return [float(x) for x in emb]


def retrieve_chunks(query: str, top_k: int | None = None, min_score: float | None = None) -> list[dict[str, Any]]:
    """
    返回 [{ "text", "source", "score" }, ...]，按 score 降序。
    索引未加载或查询失败时返回空列表。
    """
    if not is_rag_ready() or not _store:
        return []
    k = top_k if top_k is not None else RAG_TOP_K
    thr = min_score if min_score is not None else RAG_MIN_SCORE
    chunks = _store.get("chunks") or []
    if not chunks:
        return []
    try:
        qv = ollama_embed(query)
    except Exception as e:
        print("[RAG] 查询向量化失败:", e)
        return []
    if not qv:
        return []

    scored: list[tuple[float, dict[str, Any]]] = []
    for ch in chunks:
        ev = ch.get("embedding")
        if not isinstance(ev, list) or len(ev) != len(qv):
            continue
        s = _cosine(qv, [float(x) for x in ev])
        scored.append((s, ch))

    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[dict[str, Any]] = []
    for s, ch in scored[:k]:
        if s < thr:
            continue
        out.append(
            {
                "text": ch.get("text", ""),
                "source": ch.get("source", ""),
                "score": round(s, 4),
            }
        )
    return out


RAG_USER_PREFIX = (
    "请结合下面「课程知识库检索片段」优先作答；若片段不足以回答，可结合你的通识作补充，并说明依据不足的部分。\n\n"
    "【课程知识库检索片段】\n{context}\n\n"
    "【学生问题】\n{user_message}"
)


def build_rag_user_content(user_message: str) -> str:
    """将检索结果拼进用户内容，供 chat 多轮中作为单轮 user 使用。"""
    parts = retrieve_chunks(user_message)
    if not parts:
        return user_message
    lines = []
    for i, p in enumerate(parts, 1):
        src = p.get("source") or "unknown"
        lines.append(f"片段{i}（来源：{src}，相关度约 {p.get('score', 0)}）\n{p.get('text', '').strip()}")
    context = "\n\n---\n\n".join(lines)
    return RAG_USER_PREFIX.format(context=context, user_message=user_message)
