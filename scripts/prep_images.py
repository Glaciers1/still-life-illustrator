#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "2.1.0"
"""静物插画一键后处理：下载 URL / 读取本地图 -> 等比校正到目标像素 -> 输出检查摘要。

把原来"curl 下载 + PIL 缩放 + inspect_image"三步合并为一条命令。

用法:
    # 1) 两稿 URL 直接校正为 3:4(1920x2560)，按前缀命名 A/B
    python prep_images.py URL1 URL2 --ratio 3:4 --prefix parfum --out outputs

    # 2) 本地文件 + 精确像素
    python prep_images.py a.png b.png --size 2048x2048 --out outputs

    # 3) 不指定 ratio/size：仅把长边等比缩到 2048 并取偶数（保持原比例）
    python prep_images.py x.png

依赖: pip install Pillow
"""
import argparse
import io
import sys
import urllib.request
from collections import Counter
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("缺少 Pillow，请先运行: pip install Pillow")

# 与 layout-and-composition.md §1 保持一致的固定画布（竖）
CANVAS = {
    "1:1": (2048, 2048),
    "4:5": (2048, 2560),
    "3:4": (1920, 2560),
    "2:3": (1707, 2560),
    "9:16": (1152, 2048),
    "4:3": (2048, 1536),
    "3:2": (2048, 1365),
    "16:9": (2048, 1152),
}
LETTERS = "ABCDEFGH"


def load_source(src: str, retries: int = 3, cache_dir: str = "") -> Image.Image:
    """URL 下载或本地读取，返回 RGB Image。
    URL 下载失败时自动重试（默认 3 次，指数退避 1s/2s/4s）。"""
    if src.lower().startswith(("http://", "https://")):
        # 缓存逻辑：用 URL 的 MD5 作为缓存文件名
        cache_path = ""
        if cache_dir:
            import hashlib
            os.makedirs(cache_dir, exist_ok=True)
            cache_key = hashlib.md5(src.encode("utf-8")).hexdigest()
            cache_path = os.path.join(cache_dir, f"{cache_key}.png")
            if os.path.exists(cache_path):
                return Image.open(cache_path).convert("RGB")
        last_exc = None
        for attempt in range(retries):
            try:
                req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = r.read()
                if cache_path:
                    with open(cache_path, "wb") as f:
                        f.write(data)
                    return Image.open(cache_path).convert("RGB")
                return Image.open(io.BytesIO(data)).convert("RGB")
            except Exception as e:
                last_exc = e
                if attempt < retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    print(f"  [重试] 下载失败（第 {attempt+1}/{retries} 次）: {e}，{wait}s 后重试...",
                          file=sys.stderr)
                    import time
                    time.sleep(wait)
        raise last_exc
    p = Path(src)
    if not p.exists():
        raise FileNotFoundError(p)
    return Image.open(p).convert("RGB")


def target_size(w: int, h: int, args) -> tuple[int, int]:
    if args.size:
        tw, th = (int(x) for x in args.size.lower().split("x"))
        return tw, th
    if args.ratio:
        return CANVAS[args.ratio]
    scale = args.long_edge / max(w, h)
    return round(w * scale / 2) * 2, round(h * scale / 2) * 2


def fit(img: Image.Image, tw: int, th: int, tol: float = 0.02):
    """等比校正到目标像素；源比例与目标偏差>tol 时警告（不裁剪，直接 resize）。"""
    w, h = img.size
    src_r, dst_r = w / h, tw / th
    if abs(src_r - dst_r) / dst_r > tol:
        print(f"  [警告] 源比例 {w}x{h} 与目标 {tw}x{th} 偏差 {abs(src_r-dst_r)/dst_r:.1%}，"
              f"已直接拉伸；如需裁切请先核对生成比例", file=sys.stderr)
    return img.resize((tw, th), Image.LANCZOS)


def top_colors(img: Image.Image, colors: int = 5, sample: int = 160):
    small = img.resize((sample, sample)).convert("P", palette=Image.ADAPTIVE, colors=colors)
    pal = small.getpalette() or []
    cnt = Counter(small.tobytes())
    out = []
    for idx, n in cnt.most_common(colors):
        r, g, b = pal[idx * 3:idx * 3 + 3]
        out.append(f"#{r:02x}{g:02x}{b:02x}({n/(sample*sample):.2f})")
    return ", ".join(out)


def gcd_ratio(w: int, h: int) -> str:
    import math
    g = math.gcd(w, h)
    rw, rh = w // g, h // g
    return f"{rw}:{rh}" if rw <= 30 and rh <= 30 else f"{round(w/h,2)}:1"


def detect_text_regions(img: Image.Image, sample: int = 256, threshold: float = 0.8):
    """启发式伪文字检测：基于边缘密度、高对比度块分布与横向排列特征，返回 (是否疑似, 置信度, 详情)。
    仅作辅助提示，不替代 AI 目检。文字特征：边缘密度适中、高对比度块集中在少数行横向排列、行内密度高。
    """
    import math
    small = img.convert("L").resize((sample, sample))
    pixels = list(small.getdata())
    w, h = small.size

    # 1. 计算边缘密度
    edge_count = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            idx = y * w + x
            gx = abs(pixels[idx + 1] - pixels[idx - 1])
            gy = abs(pixels[idx + w] - pixels[idx - w])
            if gx + gy > 40:
                edge_count += 1
    edge_density = edge_count / (w * h)

    # 2. 网格分块统计高对比度块，并记录每行的块数
    block_size = 8
    blocks_w, blocks_h = w // block_size, h // block_size
    high_contrast_blocks = 0
    row_block_counts = [0] * blocks_h  # 每行的高对比度块数

    for by in range(blocks_h):
        for bx in range(blocks_w):
            block_pixels = []
            for dy in range(block_size):
                for dx in range(block_size):
                    px = (by * block_size + dy) * w + (bx * block_size + dx)
                    if px < len(pixels):
                        block_pixels.append(pixels[px])
            if not block_pixels:
                continue
            mean = sum(block_pixels) / len(block_pixels)
            variance = sum((p - mean) ** 2 for p in block_pixels) / len(block_pixels)
            if variance > 400:
                high_contrast_blocks += 1
                row_block_counts[by] += 1

    # 3. 文字特有的横向排列特征
    # 文字行：高对比度块 > 3 的行（文字是密集的，一行有多个字符块）
    text_like_rows = sum(1 for c in row_block_counts if c > 3)
    # 集中度：最大行块数 / 总块数（文字集中在少数行，比值高；图形均匀分布，比值低）
    max_row_blocks = max(row_block_counts) if row_block_counts else 0
    concentration = max_row_blocks / high_contrast_blocks if high_contrast_blocks > 0 else 0
    # 行内密度：文字行的块数占该行总块数的比例（文字行应该 >30%）
    dense_rows = sum(1 for c in row_block_counts if c > blocks_w * 0.3)
    # 文字行占比：文字行 / 总行数（文字集中在少数行，占比 <30%；图形可能分布更广）
    text_row_ratio = text_like_rows / blocks_h if blocks_h > 0 else 0

    # 4. 综合评分（文字特有特征权重更高）
    text_score = 0.0
    # 边缘密度适中（文字特征，0.02-0.20）
    if 0.02 < edge_density < 0.20:
        text_score += 0.15
    # 高对比度块数量足够
    if high_contrast_blocks > 15:
        text_score += 0.1
    # 文字行数量（>3 个密集行，文字特征）
    if text_like_rows > 3:
        text_score += 0.2
    # 集中度高（块集中在少数行，文字特征）
    if concentration > 0.15:
        text_score += 0.15
    # 行内密度高（密集行 >3，文字特征）
    if dense_rows > 3:
        text_score += 0.2
    # 文字行占比低（集中在少数行，文字特征）
    if text_row_ratio < 0.3:
        text_score += 0.1
    # 强特征：边缘密度高 + 集中度高 + 密集行多
    if edge_density > 0.03 and concentration > 0.2 and dense_rows > 3:
        text_score += 0.1

    confidence = min(text_score, 1.0)
    suspicious = confidence > threshold

    details = {
        "edge_density": round(edge_density, 3),
        "high_contrast_blocks": high_contrast_blocks,
        "text_like_rows": text_like_rows,
        "max_row_blocks": max_row_blocks,
        "concentration": round(concentration, 2),
        "dense_rows": dense_rows,
        "text_row_ratio": round(text_row_ratio, 2),
        "confidence": round(confidence, 2),
    }
    return suspicious, confidence, details


def main():
    ap = argparse.ArgumentParser(description="静物插画一键后处理（下载/校正/取色）")
    ap.add_argument("sources", nargs="+", help="图片 URL 或本地路径（可多个，按顺序 A/B/C…）")
    ap.add_argument("--ratio", choices=list(CANVAS), help="目标比例（用固定画布表）")
    ap.add_argument("--size", help="精确像素，如 1920x2560（优先于 --ratio）")
    ap.add_argument("--cache-dir", default="",
                    help="图片缓存目录：已下载的原始图片缓存到此目录，避免重复下载（默认不缓存）")
    ap.add_argument("--long-edge", type=int, default=2048, help="不指定 ratio/size 时的长边，默认 2048")
    ap.add_argument("--prefix", default="", help="输出前缀；给定时命名 prefix_A.png / prefix_B.png")
    ap.add_argument("--out", default="outputs", help="输出目录，默认 outputs")
    ap.add_argument("--text-scan", action="store_true", help="启发式伪文字检测：扫描疑似文字区域并输出警告（仅辅助，不替代AI目检）")
    ap.add_argument("--text-threshold", type=float, default=0.8, help="伪文字扫描可疑置信度阈值（默认 0.8，范围 0-1；越低越敏感）")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    for i, src in enumerate(args.sources):
        print(f"[{i+1}/{len(args.sources)}] {src}")
        img = load_source(src, cache_dir=args.cache_dir)
        w0, h0 = img.size
        tw, th = target_size(w0, h0, args)
        img = fit(img, tw, th)
        if args.prefix:
            name = f"{args.prefix}_{LETTERS[i]}.png" if len(args.sources) > 1 else f"{args.prefix}.png"
        else:
            stem = Path(src.split("?")[0]).stem or f"img_{LETTERS[i]}"
            name = f"{stem}_ready.png"
        dst = outdir / name
        img.save(dst)
        line = (f"  -> {dst}  {w0}x{h0}({gcd_ratio(w0,h0)}) => {tw}x{th}({gcd_ratio(tw,th)})\n"
                f"     主色: {top_colors(img)}")
        if args.text_scan:
            suspicious, conf, details = detect_text_regions(img, threshold=args.text_threshold)
            if suspicious:
                line += (f"\n     [警告] 疑似伪文字！置信度 {conf:.0%} "
                         f"(边缘密度={details['edge_density']}, 高对比块={details['high_contrast_blocks']}, "
                         f"文字行={details['text_like_rows']}) — 建议 AI 目检确认，发现文字则自动重生")
            elif conf >= 0.5:
                line += f"\n     [文字扫描] 低置信度（{conf:.0%}），纹理误报可能性高，跳过目检"
            else:
                line += f"\n     [文字扫描] 未发现疑似文字（置信度 {conf:.0%}）"
        print(line)
        results.append(str(dst))
    print("\n完成，产物：")
    for r in results:
        print(" ", r)


if __name__ == "__main__":
    main()
