#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "3.0.0"
"""静物插画色块后期合成 v2.0：从成品图动态提取主色，渲染条形色带。

规则兑现（用户确认版）：
- 色块数量：动态提取，排除插画背景色，最多10个（--max-colors，默认10）
- 色块形状：只条形，固定尺寸 宽90px x 高20px（--swatch-w/--swatch-h）
- 色块间距：0（直接拼接，连成一条色带）
- 色块排序：明->暗 左->右（--sort brightness，默认）
- 色块位置：水平居中，auto自动选上方或下方（比较区域方差选更干净的一侧）
- 边距：固定120px（--margin-px，默认120）
- 颜色标签：去掉（--label none，默认none）
- 描边：无（色块无边框）
- 背景色排除：采样图片四边10%区域，占比>10%的颜色视为背景色排除
- 颜色去重：颜色距离<30视为重复合并
- 中心加权：中心区域权重x2 + 饱和度x0.5，优先提取主体色

示例:
    python color_palette.py outputs/a_final.png -o out.png
    python color_palette.py outputs/a_final.png --max-colors 8 --pos top -o out.png
    python color_palette.py --batch outputs/

依赖: pip install Pillow
"""
import argparse
import colorsys
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("缺少 Pillow，请先运行: pip install Pillow")

SCRIPT_DIR = Path(__file__).resolve().parent
COLOR_NAMES_FILE = SCRIPT_DIR / "color_names.json"
ASSET_FONTS = [SCRIPT_DIR.parent / "assets" / "fonts"]
SYS_FONT_DIRS = (
    [r"C:\Windows\Fonts"]
    if os.name == "nt"
    else [
        "/usr/share/fonts", "/usr/local/share/fonts",
        "/System/Library/Fonts", "/System/Library/Fonts/Supplemental",
        "/Library/Fonts", os.path.expanduser("~/.fonts"),
    ]
)
FONT_DIRS = [str(d) for d in ASSET_FONTS] + SYS_FONT_DIRS

# 末位的 LXGWWenKai-Regular.ttf（assets/fonts/）为随技能分发的 OFL 字体兜底
ALIASES = {
    "type": ["cour.ttf", "couri.ttf", "consola.ttf", "lucon.ttf", "Courier New.ttf",
             "Menlo.ttc", "Monaco.ttf", "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"],
    "typewriter": ["cour.ttf", "couri.ttf", "Courier New.ttf", "Menlo.ttc", "DejaVuSansMono.ttf"],
    "serif": ["simsun.ttc", "STSONG.TTF", "times.ttf", "georgia.ttf",
              "NotoSerifCJK-Regular.ttc", "NotoSerifCJKsc-Regular.otf", "LXGWWenKai-Regular.ttf"],
    "sans": ["msyh.ttc", "msyhbd.ttf", "simhei.ttf", "arial.ttf", "PingFang.ttc",
             "NotoSansCJK-Regular.ttc", "NotoSansSC-Regular.otf", "LXGWWenKai-Regular.ttf"],
}

_font_file_cache = {}


def _find_font_file(name):
    """按文件名在 FONT_DIRS 中查找字体（大小写不敏感；Linux/macOS 递归子目录，结果缓存）。"""
    key = name.lower()
    if key in _font_file_cache:
        return _font_file_cache[key]
    found = ""
    for directory in FONT_DIRS:
        if not os.path.isdir(directory):
            continue
        direct = os.path.join(directory, name)
        if os.path.isfile(direct):
            found = direct
            break
        for root, _subdirs, files in os.walk(directory):
            for fn in files:
                if fn.lower() == key:
                    found = os.path.join(root, fn)
                    break
            if found:
                break
        if found:
            break
    _font_file_cache[key] = found
    return found

_probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))


# ---------------------------------------------------------------------------
# 色彩提取（动态 + 排除背景色 + 中心加权 + 颜色去重）
# ---------------------------------------------------------------------------

def extract_colors(img, max_colors=10, sample=200):
    """从图片提取主色，排除背景色，返回 [(r, g, b, ratio), ...] 按明->暗排序。

    背景色判断：采样图片四边10%区域，占比>10%的颜色视为背景色排除。
    提取策略：中心区域权重x2 + 饱和度权重x0.5，优先主体色。
    颜色去重：颜色距离<30视为重复，保留加权得分更高的。
    """
    W, H = img.size
    small = img.resize((sample, sample)).convert("P", palette=Image.ADAPTIVE, colors=32)
    pal = small.getpalette() or []
    cnt = Counter(small.tobytes())
    total = sample * sample

    # 边缘采样（判断背景色）：取图片四边10%区域
    edge_pixels = []
    edge_band = max(1, sample // 10)
    for y in range(sample):
        for x in range(sample):
            if x < edge_band or x >= sample - edge_band or y < edge_band or y >= sample - edge_band:
                edge_pixels.append(small.getpixel((x, y)))
    edge_cnt = Counter(edge_pixels)
    edge_total = len(edge_pixels)
    # 背景色：边缘占比>10%的颜色
    bg_indices = set()
    for idx, n in edge_cnt.most_common(8):
        if edge_total and n / edge_total > 0.10:
            bg_indices.add(idx)

    # 中心区域掩码（中间50%）
    cx0, cx1 = sample // 4, sample * 3 // 4
    cy0, cy1 = sample // 4, sample * 3 // 4
    center_pixels = []
    for y in range(cy0, cy1):
        for x in range(cx0, cx1):
            center_pixels.append(small.getpixel((x, y)))
    center_cnt = Counter(center_pixels)
    center_total = len(center_pixels)

    # 收集候选颜色（排除背景色）
    candidates = []
    for idx, n in cnt.most_common(32):
        if idx in bg_indices:
            continue
        r, g, b = pal[idx * 3:idx * 3 + 3]
        global_ratio = n / total
        center_ratio = center_cnt.get(idx, 0) / center_total if center_total else 0
        sat = saturation(r, g, b)
        score = center_ratio * 2.0 + global_ratio * 0.3 + sat * 0.5
        candidates.append((r, g, b, global_ratio, score))

    # 按加权得分降序
    candidates.sort(key=lambda x: x[4], reverse=True)

    # 颜色去重：距离<30视为重复，保留得分更高的
    result = []
    for r, g, b, ratio, _ in candidates:
        too_close = False
        for er, eg, eb, _ in result:
            dist = math.sqrt((r - er) ** 2 + (g - eg) ** 2 + (b - eb) ** 2)
            if dist < 30:
                too_close = True
                break
        if not too_close:
            result.append((r, g, b, ratio))
        if len(result) >= max_colors:
            break

    # 明->暗排序
    result.sort(key=lambda c: luminance(c[0], c[1], c[2]), reverse=True)
    return result


# ---------------------------------------------------------------------------
# 颜色空间转换
# ---------------------------------------------------------------------------

def rgb_to_hsl(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return h * 360.0, s, l


def rgb_to_hex(r, g, b):
    return "#%02x%02x%02x" % (r, g, b)


def luminance(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def saturation(r, g, b):
    _, s, _ = rgb_to_hsl(r, g, b)
    return s


# ---------------------------------------------------------------------------
# 字体（保留，标签默认none但仍支持手动开启）
# ---------------------------------------------------------------------------

def load_font(spec, size):
    if spec and os.path.isfile(spec):
        try:
            return ImageFont.truetype(spec, size)
        except Exception:
            pass
    names = ALIASES.get((spec or "type").lower(), [spec or "type"])
    for name in names:
        if not name:
            continue
        candidate = _find_font_file(name)
        if candidate:
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# 上下区域干净度检测（auto选上方或下方）
# ---------------------------------------------------------------------------

def find_clean_vertical_region(img, bw, bh, margin_px=120):
    """比较上方和下方区域的方差，选更干净（方差更低）的一侧。

    返回 (ox, oy) 色块左上角坐标（已水平居中）。
    """
    W, H = img.size
    ox = (W - bw) // 2  # 水平居中

    # 上方区域：从 margin_px 到 margin_px + bh + 缓冲
    top_y = margin_px
    # 下方区域：从 H - margin_px - bh 到 H - margin_px
    bottom_y = H - margin_px - bh

    gray = img.convert("L")

    def region_variance(y):
        box = (max(0, ox - 20), max(0, y - 10), min(W, ox + bw + 20), min(H, y + bh + 10))
        if box[2] <= box[0] or box[3] <= box[1]:
            return float("inf")
        pixels = list(gray.crop(box).tobytes())
        if not pixels:
            return float("inf")
        mean = sum(pixels) / len(pixels)
        return sum((p - mean) ** 2 for p in pixels) / len(pixels)

    top_var = region_variance(top_y)
    bottom_var = region_variance(bottom_y)

    if top_var <= bottom_var:
        return ox, top_y, "top"
    else:
        return ox, bottom_y, "bottom"


# ---------------------------------------------------------------------------
# 色块布局（只条形，固定尺寸，0间距）
# ---------------------------------------------------------------------------

def layout_swatches(colors, swatch_w=60, swatch_h=20):
    """计算色块布局。只条形，固定尺寸，0间距，一排显示。

    返回 [(x, y, w, h, color), ...] 和整体包围盒 (bw, bh)。
    """
    positions = []
    for i, color in enumerate(colors):
        x = i * swatch_w  # 0间距
        positions.append((x, 0, swatch_w, swatch_h, color))

    bw = len(colors) * swatch_w if colors else 0
    bh = swatch_h if colors else 0
    return positions, bw, bh


# ---------------------------------------------------------------------------
# 色块渲染（水平居中，auto上下，边距120，无标签，无描边）
# ---------------------------------------------------------------------------

def render_swatches(img, colors, pos="auto", swatch_w=60, swatch_h=20,
                     margin_px=120, label_mode="none", font_spec="type"):
    """在图片上渲染色块。返回新图片（RGBA）。"""
    W, H = img.size
    result = img.convert("RGBA").copy()
    draw = ImageDraw.Draw(result)

    if not colors:
        return result

    # 计算布局
    positions, bw, bh = layout_swatches(colors, swatch_w, swatch_h)

    # 确定落点
    if pos == "top":
        ox, oy = (W - bw) // 2, margin_px
    elif pos == "bottom":
        ox, oy = (W - bw) // 2, H - bh - margin_px
    else:  # auto
        ox, oy, _side = find_clean_vertical_region(result, bw, bh, margin_px)

    # 渲染色块（无描边、无标签）
    for (x, y, w, h, color) in positions:
        rx, ry = ox + x, oy + y
        r, g, b, _ = color
        draw.rectangle([rx, ry, rx + w, ry + h], fill=(r, g, b, 255))
        # 无描边：不画 outline

    # 颜色标签（默认none，仅手动开启时渲染）
    if label_mode != "none":
        font_size = max(10, int(swatch_h * 0.6))
        font = load_font(font_spec, font_size)
        color_names = _load_color_names()
        label_y = oy + bh + 2
        for (x, y, w, h, color) in positions:
            rx = ox + x
            r, g, b, _ = color
            if label_mode == "hex":
                text = rgb_to_hex(r, g, b)
            else:
                text = _match_color_name((r, g, b), color_names)
            lum = luminance(r, g, b)
            text_color = (30, 28, 26) if lum >= 128 else (245, 242, 235)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((rx + (w - tw) // 2, label_y), text, font=font, fill=text_color)

    return result


def _load_color_names():
    if not COLOR_NAMES_FILE.exists():
        return []
    with open(COLOR_NAMES_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return [(c["name"], tuple(c["rgb"])) for c in data.get("colors", [])]


def _match_color_name(rgb, color_names):
    if not color_names:
        return rgb_to_hex(*rgb)
    r, g, b = rgb
    best_name, best_dist = None, float("inf")
    for name, (nr, ng, nb) in color_names:
        d = (r - nr) ** 2 + (g - ng) ** 2 + (b - nb) ** 2
        if d < best_dist:
            best_dist, best_name = d, name
    return best_name


# ---------------------------------------------------------------------------
# 批量模式
# ---------------------------------------------------------------------------

def batch_process(batch_dir, args):
    import glob
    final_files = sorted(glob.glob(os.path.join(batch_dir, "*_final.png")))
    if not final_files:
        final_files = sorted(glob.glob(os.path.join(batch_dir, "*.png")))
    if not final_files:
        sys.exit("错误：目录 %s 下未找到 *_final.png 文件" % batch_dir)

    print("===== 批量色块渲染：找到 %d 张 =====" % len(final_files))
    ok, fail = 0, 0
    for fp in final_files:
        try:
            img = Image.open(fp).convert("RGBA")
            colors = extract_colors(img, args.max_colors)
            result = render_swatches(
                img, colors,
                pos=args.pos,
                swatch_w=args.swatch_w,
                swatch_h=args.swatch_h,
                margin_px=args.margin_px,
                label_mode=args.label,
                font_spec=args.font,
            )
            out_path = fp  # 直接覆盖原 _final.png
            result.convert("RGB").save(out_path, quality=95)
            print("  [OK]   %s (%d色)" % (os.path.basename(fp), len(colors)))
            ok += 1
        except Exception as ex:
            print("  [FAIL] %s: %s" % (os.path.basename(fp), ex))
            fail += 1

    print("\n===== 批量完成：成功 %d / 失败 %d / 总计 %d =====" % (ok, fail, ok + fail))
    sys.exit(1 if fail else 0)


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="静物插画色块后期合成 v2.0")
    ap.add_argument("image", nargs="?", help="输入图片路径（单张模式必填；--batch 可省略）")
    ap.add_argument("--batch", help="批量模式：指定目录，自动处理 *_final.png（直接覆盖）")
    ap.add_argument("--max-colors", type=int, default=10,
                    help="最多提取色彩数量（默认10；动态提取+排除背景色+颜色去重后取前N）")
    ap.add_argument("--swatch-w", type=int, default=90, help="色块宽度(px)，默认90")
    ap.add_argument("--swatch-h", type=int, default=20, help="色块高度(px)，默认20")
    ap.add_argument("--pos", default="auto", choices=["top", "bottom", "auto"],
                    help="色块位置：top 上方 / bottom 下方 / auto 自动选更干净的一侧（默认auto）")
    ap.add_argument("--margin-px", type=int, default=120, help="色块距离上下边界的边距(px)，默认120")
    ap.add_argument("--label", default="none", choices=["none", "name", "hex"],
                    help="颜色标签：none 无标签（默认）/ name 颜色名 / hex 十六进制")
    ap.add_argument("--font", default="type", help="标签字体（默认 type=Courier；仅--label非none时生效）")
    ap.add_argument("-o", "--output", default="", help="输出图片路径（单张模式必填；批量模式直接覆盖原文件）")
    args = ap.parse_args()

    if args.batch:
        batch_process(args.batch, args)
        return

    if not args.image:
        sys.exit("错误：单张模式必须提供输入图片路径，或使用 --batch 批量模式")
    if not args.output:
        sys.exit("错误：单张模式必须提供 -o/--output 输出路径")

    img = Image.open(args.image).convert("RGBA")
    colors = extract_colors(img, args.max_colors)
    print("提取到 %d 种主色（已排除背景色）:" % len(colors))
    for i, (r, g, b, ratio) in enumerate(colors):
        print("  %d. %s  占比 %.1f%%" % (i + 1, rgb_to_hex(r, g, b), ratio * 100))

    result = render_swatches(
        img, colors,
        pos=args.pos,
        swatch_w=args.swatch_w,
        swatch_h=args.swatch_h,
        margin_px=args.margin_px,
        label_mode=args.label,
        font_spec=args.font,
    )
    result.convert("RGB").save(args.output, quality=95)
    print("已保存: %s" % args.output)


if __name__ == "__main__":
    main()
