#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静物插画图片分析：尺寸、比例、方向、主色板、边缘背景色。

单图分析：
    python inspect_image.py IMG [IMG ...] [--json]

批量风格汇总（多张参考图时用）：
    python inspect_image.py IMG1 IMG2 IMG3 --summary
    python inspect_image.py IMG1 IMG2 --prompt-inject   （输出可粘贴到提示词的风格片段）

依赖: pip install Pillow
"""
import argparse
import glob
import json
import math
import sys
from collections import Counter
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("缺少 Pillow，请先运行: pip install Pillow")


def ratio_pair(w: int, h: int):
    g = math.gcd(w, h)
    rw, rh = w // g, h // g
    # 大数约分太碎时，给一个小数近似比例
    if rw > 30 or rh > 30:
        if w >= h:
            rw, rh = round(w / h, 2), 1
        else:
            rw, rh = 1, round(h / w, 2)
    return f"{rw}:{rh}"


def top_colors(img: Image.Image, colors: int = 6, sample: int = 200):
    small = img.convert("RGB").resize((sample, sample))
    pal = small.convert("P", palette=Image.ADAPTIVE, colors=colors)
    raw = pal.getpalette() or []
    cnt = Counter(pal.tobytes())
    total = sample * sample
    out = []
    for idx, n in cnt.most_common(colors):
        r, g, b = raw[idx * 3:idx * 3 + 3]
        out.append({"hex": f"#{r:02x}{g:02x}{b:02x}", "ratio": round(n / total, 3)})
    return out


def edge_colors(img: Image.Image, frac: float = 0.12):
    """取四边 frac 宽条带，估计背景/留白区颜色。"""
    w, h = img.size
    bw, bh = max(1, int(w * frac)), max(1, int(h * frac))
    rgb = img.convert("RGB")
    strips = Image.new("RGB", (bw * 2 + bh * 2, max(bh, bw)))
    strips.paste(rgb.crop((0, 0, w, bh)), (0, 0))                      # top
    strips.paste(rgb.crop((0, h - bh, w, h)), (0, 0))                  # bottom
    strips.paste(rgb.crop((0, 0, bw, h)), (0, 0))                      # left
    strips.paste(rgb.crop((w - bw, 0, w, h)), (bw, 0))                 # right
    return top_colors(strips, colors=3, sample=160)


def analyze(path: str):
    p = Path(path)
    with Image.open(p) as im:
        w, h = im.size
        orient = "portrait" if h > w else "landscape" if w > h else "square"
        info = {
            "file": str(p),
            "width": w,
            "height": h,
            "orientation": orient,
            "ratio": ratio_pair(w, h),
            "long_edge_target": 2048,
            "suggested_canvas": _suggest(w, h),
            "top_colors": top_colors(im),
            "edge_colors": edge_colors(im),
        }
    return info


def _suggest(w: int, h: int):
    scale = 2048 / max(w, h)
    nw, nh = round(w * scale / 2) * 2, round(h * scale / 2) * 2
    return f"{nw}x{nh}"


def pretty(d: dict) -> str:
    lines = [
        f"文件: {d['file']}",
        f"尺寸: {d['width']}x{d['height']} ({d['orientation']}, 比例 {d['ratio']})",
        f"建议画布: {d['suggested_canvas']}",
        "主色板: " + ", ".join(f"{c['hex']}({c['ratio']})" for c in d["top_colors"]),
        "边缘色: " + ", ".join(f"{c['hex']}({c['ratio']})" for c in d["edge_colors"]),
    ]
    return "\n".join(lines)


def batch_summary(results):
    """对多张参考图输出整批风格汇总。
    返回 dict：统一比例、统一主色板、统一边缘色、风格倾向判断。
    """
    if not results:
        return {}

    # 统一比例：取出现最多的比例
    ratios = Counter(r["ratio"] for r in results)
    dominant_ratio = ratios.most_common(1)[0][0]

    # 统一主色板：合并所有图的主色，按出现频率和占比加权
    all_top = []
    for r in results:
        for c in r["top_colors"]:
            all_top.append((c["hex"], c["ratio"]))
    # 按 hex 分组，取平均占比
    color_avg = {}
    for h, ratio in all_top:
        if h not in color_avg:
            color_avg[h] = []
        color_avg[h].append(ratio)
    unified_top = sorted(
        [{"hex": h, "avg_ratio": round(sum(v) / len(v), 3)} for h, v in color_avg.items()],
        key=lambda x: x["avg_ratio"], reverse=True
    )[:6]

    # 统一边缘色（背景色）：合并所有图的边缘色
    all_edge = []
    for r in results:
        for c in r["edge_colors"]:
            all_edge.append((c["hex"], c["ratio"]))
    edge_avg = {}
    for h, ratio in all_edge:
        if h not in edge_avg:
            edge_avg[h] = []
        edge_avg[h].append(ratio)
    unified_edge = sorted(
        [{"hex": h, "avg_ratio": round(sum(v) / len(v), 3)} for h, v in edge_avg.items()],
        key=lambda x: x["avg_ratio"], reverse=True
    )[:3]

    # 风格倾向判断：基于主色和边缘色
    # 计算整体饱和度（简化：用 hex 亮度判断）
    def hex_brightness(h):
        h = h.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r * 299 + g * 587 + b * 114) / 1000

    avg_brightness = sum(hex_brightness(c["hex"]) for c in unified_top) / max(len(unified_top), 1)
    bg_brightness = hex_brightness(unified_edge[0]["hex"]) if unified_edge else 200

    if bg_brightness > 200:
        bg_style = "light background (high-key)"
    elif bg_brightness < 80:
        bg_style = "dark background (low-key)"
    else:
        bg_style = "mid-tone background"

    if avg_brightness > 180:
        color_style = "soft, muted pastel palette"
    elif avg_brightness < 80:
        color_style = "deep, rich saturated palette"
    else:
        color_style = "balanced middle-tone palette"

    # 比例倾向
    if "3:4" in dominant_ratio or "4:5" in dominant_ratio:
        ratio_style = "portrait orientation"
    elif "4:3" in dominant_ratio or "16:9" in dominant_ratio:
        ratio_style = "landscape orientation"
    else:
        ratio_style = f"{dominant_ratio} ratio"

    return {
        "image_count": len(results),
        "dominant_ratio": dominant_ratio,
        "ratio_style": ratio_style,
        "unified_top_colors": unified_top,
        "unified_edge_colors": unified_edge,
        "bg_style": bg_style,
        "color_style": color_style,
        "avg_brightness": round(avg_brightness, 1),
        "bg_brightness": round(bg_brightness, 1),
    }


def prompt_inject(summary):
    """根据批量汇总生成可直接粘贴到提示词中的英文风格描述片段。
    返回字符串，包含：背景色、主色调、比例、风格倾向。
    """
    if not summary:
        return ""

    lines = []

    # 背景色
    if summary.get("unified_edge_colors"):
        bg_hex = summary["unified_edge_colors"][0]["hex"]
        lines.append(f"background color {bg_hex}")

    # 主色调
    if summary.get("unified_top_colors"):
        top_hexes = [c["hex"] for c in summary["unified_top_colors"][:4]]
        lines.append(f"palette dominated by {', '.join(top_hexes)}")

    # 风格倾向
    lines.append(summary.get("color_style", "balanced palette"))
    lines.append(summary.get("bg_style", "light background"))

    # 比例
    lines.append(summary.get("ratio_style", ""))

    # 过滤空行
    lines = [l for l in lines if l]
    return "; ".join(lines)


def main():
    ap = argparse.ArgumentParser(description="静物插画图片分析")
    ap.add_argument("images", nargs="+", help="图片路径，支持 * 通配符")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--summary", action="store_true", help="批量风格汇总：多张参考图输出统一比例/主色板/边缘色/风格倾向")
    ap.add_argument("--prompt-inject", action="store_true", help="输出可直接粘贴到提示词的英文风格描述片段（基于批量汇总）")
    args = ap.parse_args()

    files = []
    for item in args.images:
        matched = sorted(glob.glob(item))
        files.extend(matched if matched else [item])
    results = [analyze(i) for i in files]

    if args.summary or args.prompt_inject:
        summary = batch_summary(results)
        if args.prompt_inject:
            # 只输出提示词注入片段
            print(prompt_inject(summary))
        else:
            # 输出批量汇总详情
            print(f"\n===== 批量风格汇总（{summary['image_count']} 张参考图）=====")
            print(f"统一比例: {summary['dominant_ratio']} ({summary['ratio_style']})")
            print(f"统一主色板: " + ", ".join(f"{c['hex']}({c['avg_ratio']})" for c in summary["unified_top_colors"]))
            print(f"统一边缘色: " + ", ".join(f"{c['hex']}({c['avg_ratio']})" for c in summary["unified_edge_colors"]))
            print(f"背景风格: {summary['bg_style']} (亮度 {summary['bg_brightness']})")
            print(f"色彩风格: {summary['color_style']} (平均亮度 {summary['avg_brightness']})")
            if args.json:
                print("\n--- JSON ---")
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            print(f"\n提示词注入片段:")
            print(f"  {prompt_inject(summary)}")
    elif args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("\n---\n".join(pretty(r) for r in results))


if __name__ == "__main__":
    main()
