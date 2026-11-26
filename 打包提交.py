#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「可安全提交」的源代码压缩包。

为什么需要它：
    直接用「右键 → 压缩」会把下面这些东西一起打进去：
      · APIKey.env        —— 里面是真实的各厂商 API 密钥
      · feedback_data.json —— 真实的姓名 / 邮箱 / 学号
      · node_modules/      —— 上万个文件、上百 MB，接收方自己 npm install 即可
      · __pycache__/ .idea/ —— 无用缓存

本脚本会剔除以上内容，并对文本文件做一次密钥扫描，确认没有残留。

用法:
    python 打包提交.py
    python 打包提交.py 我的毕业设计.zip
"""
from __future__ import annotations

import json
import os
import re
import sys
import zipfile

basedir = os.path.abspath(os.path.dirname(__file__))
DEFAULT_OUT = os.path.join(basedir, "源代码_提交版.zip")

# 按目录名排除（出现在路径任意层级即排除）
EXCLUDE_DIR_NAMES = {
    "node_modules", "__pycache__", ".idea", ".git", ".vscode",
    ".venv", "venv", ".pytest_cache", ".mypy_cache",
}

# 按「相对路径」排除（仅排指定位置，不影响别处同名目录）
EXCLUDE_REL_PATHS = {
    os.path.join("VUEworks", "my-vue-project", "dist"),  # 前端构建中间产物
}

# 按文件名排除（真实密钥与个人数据）
EXCLUDE_FILE_NAMES = {
    "APIKey.env",
    "feedback_data.json",
    "源代码.zip",
    "源代码_提交版.zip",
}

# 打包时替换写入的文件（脱敏后的内容）
SYNTHETIC_FILES = {
    "feedback_data.json": json.dumps(
        [
            {"name": "测试用户", "email": "user@example.com", "message": "测试消息", "timestamp": "2025-04-12T09:59:43.744Z"},
            {"name": "测试用户", "email": "user@example.com", "message": "测试消息2", "timestamp": "2025-04-12T10:00:09.562Z"},
            {"name": "测试用户", "email": "user@example.com", "message": "测试消息3，测试时间戳为北京时间", "timestamp": "2025-04-12T18:18:41.745396+08:00"},
        ],
        ensure_ascii=False,
        indent=2,
    )
}

# 密钥扫描：只扫文本文件
TEXT_EXT = {".py", ".js", ".vue", ".json", ".md", ".txt", ".html", ".css", ".env", ".example", ".yml", ".yaml"}
SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "疑似 API Key（sk- 开头）"),
    (re.compile(r"\b\d{8}@stu\.xidian\.edu\.cn\b"), "疑似学号邮箱"),
]


def is_excluded(rel: str, name: str) -> bool:
    parts = rel.split(os.sep)
    if any(p in EXCLUDE_DIR_NAMES for p in parts[:-1]):
        return True
    if name in EXCLUDE_FILE_NAMES:
        return True
    if rel in EXCLUDE_REL_PATHS:
        return True
    return False


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    if not os.path.isabs(out):
        out = os.path.join(basedir, out)

    included: list[tuple[str, int]] = []
    excluded: list[str] = []
    findings: list[str] = []

    if os.path.exists(out):
        os.remove(out)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(basedir):
            # 原地裁剪，避免走进被排除的目录（如 node_modules）
            dirs[:] = [
                d for d in dirs
                if d not in EXCLUDE_DIR_NAMES
                and os.path.relpath(os.path.join(root, d), basedir) not in EXCLUDE_REL_PATHS
            ]
            dirs.sort()
            for fn in sorted(files):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, basedir)
                if is_excluded(rel, fn):
                    excluded.append(rel)
                    continue
                try:
                    zf.write(full, rel)
                except OSError as e:
                    print("  跳过（无法读取）:", rel, e)
                    continue
                included.append((rel, os.path.getsize(full)))

                # 密钥扫描
                if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                    try:
                        with open(full, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                    except OSError:
                        continue
                    for pat, desc in SECRET_PATTERNS:
                        for m in pat.finditer(text):
                            findings.append(f"{rel}: {desc} -> {m.group()[:14]}...")

        # 写入脱敏文件
        for rel, content in SYNTHETIC_FILES.items():
            zf.writestr(rel, content)
            included.append((rel + "（已脱敏）", len(content)))

    total = sum(s for _, s in included)
    print("=" * 62)
    print(f"已生成: {out}")
    print(f"压缩包大小: {os.path.getsize(out) / 1048576:.2f} MB  |  原始合计: {total / 1048576:.2f} MB")
    print(f"收录文件: {len(included)} 个   |  排除文件: {len(excluded)} 个")
    print("=" * 62)

    print("\n【已排除的关键文件】")
    for rel in sorted(excluded):
        if os.path.basename(rel) in EXCLUDE_FILE_NAMES:
            print("  -", rel)
    print(f"  （另有 {len(excluded)} 个依赖/缓存文件被排除，如 node_modules、__pycache__）")

    print("\n【密钥扫描结果】")
    if findings:
        print("  ⚠ 发现疑似敏感内容，请检查后再提交：")
        for f in findings:
            print("   ", f)
    else:
        print("  ✓ 未发现 API Key / 学号邮箱等敏感内容")

    print("\n【提示】")
    print("  · 压缩包里不含 APIKey.env；接收方需复制 APIKey.env.example 为 APIKey.env 并填写自己的密钥")
    print("  · 完整部署方式见 README.md")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
