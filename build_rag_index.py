#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 database/*.md 构建 RAG 向量索引，写入 database/rag_index/store.json

前置条件（需已安装 Ollama 并拉取与 rag_service.OLLAMA_EMBED_MODEL 一致的嵌入模型，默认 nomic-embed-text）:
  ollama pull nomic-embed-text

用法:
  python build_rag_index.py

环境变量:
  OLLAMA_BASE_URL   默认 http://127.0.0.1:11434
  OLLAMA_EMBED_MODEL 默认 nomic-embed-text
  DATABASE_DIR      默认 <项目根>/database
  RAG_INDEX_PATH    输出文件路径
"""
from __future__ import annotations

import json
import os
import sys
import time

import requests

basedir = os.path.abspath(os.path.dirname(__file__))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
DATABASE_DIR = os.getenv("DATABASE_DIR", os.path.join(basedir, "database"))
RAG_OUT = os.getenv(
    "RAG_INDEX_PATH",
    os.path.join(basedir, "database", "rag_index", "store.json"),
)

# 中文实验文档：按块大小与重叠切分
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))


def ollama_embed(text: str) -> list[float]:
    r = requests.post(
        f"{OLLAMA_BASE_URL.rstrip('/')}/api/embeddings",
        json={"model": OLLAMA_EMBED_MODEL, "prompt": text[:8000]},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    emb = data.get("embedding")
    if not isinstance(emb, list):
        raise RuntimeError("Ollama 未返回有效 embedding 列表")
    return [float(x) for x in emb]


def chunk_text(text: str, max_size: int, overlap: int) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        j = min(i + max_size, n)
        piece = text[i:j]
        if j < n:
            for sep in ("\n\n", "\n", "。"):
                k = piece.rfind(sep, max(0, len(piece) - max_size // 2))
                if k >= max(50, len(piece) // 4):
                    piece = piece[: k + len(sep)]
                    j = i + len(piece)
                    break
        piece = piece.strip()
        if piece:
            chunks.append(piece)
        if j >= n:
            break
        i = j - overlap
        if i <= 0:
            i = j
    return chunks


def read_markdown_files(folder: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if not os.path.isdir(folder):
        print("目录不存在:", folder, file=sys.stderr)
        return out
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(".md"):
            continue
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            out.append((name, f.read()))
    return out


def main() -> int:
    # 测 Ollama
    try:
        r = requests.get(f"{OLLAMA_BASE_URL.rstrip('/')}/", timeout=5)
    except requests.RequestException as e:
        print("无法连接 Ollama，请确认服务已启动:", e, file=sys.stderr)
        return 1

    files = read_markdown_files(DATABASE_DIR)
    if not files:
        print("在", DATABASE_DIR, "未找到 .md 文件", file=sys.stderr)
        return 1

    all_chunks: list[dict] = []
    for source_name, content in files:
        for c in chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP):
            all_chunks.append({"source": source_name, "text": c})

    print(
        f"共 {len(files)} 个文件，{len(all_chunks)} 个文本块；嵌入模型 {OLLAMA_EMBED_MODEL}"
    )

    for idx, ch in enumerate(all_chunks):
        t0 = time.time()
        ch["id"] = str(idx)
        ch["embedding"] = ollama_embed(ch["text"])
        if (idx + 1) % 10 == 0 or idx == 0:
            print(
                f"  已处理 {idx + 1}/{len(all_chunks)} 块, 耗时 {time.time() - t0:.2f}s"
            )
        time.sleep(0)  # 可选：限流

    store = {
        "version": 1,
        "embed_model": OLLAMA_EMBED_MODEL,
        "ollama_base": OLLAMA_BASE_URL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "source_dir": os.path.normpath(DATABASE_DIR),
        "chunks": all_chunks,
    }

    out_dir = os.path.dirname(RAG_OUT)
    os.makedirs(out_dir, exist_ok=True)
    with open(RAG_OUT, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False)

    size_mb = os.path.getsize(RAG_OUT) / (1024 * 1024)
    print("已写入", RAG_OUT, f"（约 {size_mb:.2f} MB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
