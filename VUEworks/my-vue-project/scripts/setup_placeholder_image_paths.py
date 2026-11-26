# -*- coding: utf-8 -*-
"""构建图片占位路径并回填到 JSON 数据。"""
import base64
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"

COMPONENT_JSON = PUBLIC_DIR / "electronicComponents.json"
INSTRUMENT_JSON = PUBLIC_DIR / "labInstruments.json"

# 1x1 PNG 占位图（灰色像素）
PLACEHOLDER_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7ZPioAAAAASUVORK5CYII="
)


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def ensure_placeholder_png(path: Path):
    if path.exists():
        return
    data = base64.b64decode(PLACEHOLDER_PNG_BASE64)
    path.write_bytes(data)


def ensure_readme(path: Path, label: str):
    readme = path / "README.txt"
    if readme.exists():
        return
    readme.write_text(
        f"此目录为{label}占位图目录。\n"
        "当前为占位 PNG，可替换为真实图片并保持同名。\n",
        encoding="utf-8",
    )


def process_json(json_path: Path, kind: str):
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if kind == "components":
        base_real = PUBLIC_DIR / "images" / "components" / "real"
        base_schematic = PUBLIC_DIR / "images" / "components" / "schematic"
        real_web_tpl = "/images/components/real/component-{code}.png"
        schematic_web_tpl = "/images/components/schematic/component-{code}.png"
    else:
        base_real = PUBLIC_DIR / "images" / "instruments" / "real"
        base_schematic = PUBLIC_DIR / "images" / "instruments" / "schematic"
        real_web_tpl = "/images/instruments/real/instrument-{code}.png"
        schematic_web_tpl = "/images/instruments/schematic/instrument-{code}.png"

    ensure_dir(base_real)
    ensure_dir(base_schematic)
    ensure_readme(base_real, "现实图像")
    ensure_readme(base_schematic, "电路原理图")

    for idx, item in enumerate(data, start=1):
        code = f"{idx:03d}"
        real_web = real_web_tpl.format(code=code)
        schematic_web = schematic_web_tpl.format(code=code)

        # 回填字段（若已存在用户自定义路径则保留）
        if not item.get("现实图像"):
            item["现实图像"] = real_web
        if not item.get("原理图像"):
            item["原理图像"] = schematic_web

        real_file = PUBLIC_DIR / real_web.lstrip("/")
        schematic_file = PUBLIC_DIR / schematic_web.lstrip("/")
        ensure_placeholder_png(real_file)
        ensure_placeholder_png(schematic_file)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return len(data)


def main():
    c_count = process_json(COMPONENT_JSON, "components")
    i_count = process_json(INSTRUMENT_JSON, "instruments")
    print(f"Done. components={c_count}, instruments={i_count}")


if __name__ == "__main__":
    main()
