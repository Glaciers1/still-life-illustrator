#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "2.1.0"
"""静物插画文字后期合成：主标题（可艺术变形）+ 次要文字（一句短诗 ＋ 季节、拉丁学名两行）。

规则兑现：
- 主标题字块占版面（--title-width，默认 0.30），字距默认稀疏
- 次要文字字高为主标题的 18%-36%（--subtitle-ratio，默认 0.25），字距默认收紧
- 次要文字用一个空行(\n\n)把"短诗块"与"季节·学名块"分开：两块之间段距=次要字高的 2.5 倍（--subtitle-section-gap 默认 2.5），空行之后的季节/学名自动转英文大写（--no-upper-section 可关）
- 语言模式（内容由调用方决定、脚本只渲染）：英文排版=大写季节+大写学名两行；中文排版（主标题与短诗均中文）只放一行中文季节、不生成学名
- 主/次字体必须不同；主标题字体 kai/hand/serif/sans（已取消 marker），次要文字 type；自动在 assets/fonts 与系统字体目录查找
- 中文回退：次要文字（或主标题）含中文而所选西文字体（如 type=Courier New）无中文字形时，自动回退到 kai（楷体），避免渲染成空心方框（effective_spec）；因此中文排版主标题请用 serif/hand/sans 等非 kai 字体，以免主、次实际都成楷体而撞字体
- 主标题艺术变形 --title-style：normal/italic/wave（波浪）/arch（弧形上拱）/scatter（疏密错落），五者平等、由调用方随机指定，脚本不设风格默认
- 自由摆放 --title-xy/--subtitle-xy "x%,y%"（文字块中心）与 --title-rotate/--subtitle-rotate

示例:
    python overlay_text.py outputs/a.png --title "CHERRY" `
        --subtitle "A handful of June,`nbright as a red wish.`n`nEARLY SUMMER`nPRUNUS AVIUM" --subtitle-ratio 0.25 --title-pos top-center `
        --title-font serif --subtitle-font type --title-style arch -o out.png
    # 短诗与季节/学名之间用一个空行(`n`n)分界：段距=次要字高x2.5，分界后季节/学名自动英文大写

依赖: pip install Pillow
"""
import argparse
import json
import math
import os
import statistics
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("缺少 Pillow，请先运行: pip install Pillow")

SCRIPT_DIR = Path(__file__).resolve().parent
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

# 每个别名按顺序尝试；末位的 LXGWWenKai-Regular.ttf 是随技能分发的 OFL 字体
# （assets/fonts/，含完整 CJK 字形），作为系统字体全缺失时的跨平台兜底，
# 避免非 Windows 环境下中文渲染成空心方框。
ALIASES = {
    "kai": ["simkai.ttf", "STKAITI.TTF", "Kaiti.ttc", "ukai.ttc", "LXGWWenKai-Regular.ttf"],
    "hand": ["STXINGKA.TTF", "simli.ttf", "simkai.ttf", "Kaiti.ttc", "LXGWWenKai-Regular.ttf"],
    "serif": ["simsun.ttc", "STSONG.TTF", "times.ttf", "georgia.ttf",
              "NotoSerifCJK-Regular.ttc", "NotoSerifCJKsc-Regular.otf", "LXGWWenKai-Regular.ttf"],
    "song": ["simsun.ttc", "STSONG.TTF", "NotoSerifCJK-Regular.ttc", "LXGWWenKai-Regular.ttf"],
    "sans": ["msyh.ttc", "msyhbd.ttf", "simhei.ttf", "arial.ttf", "PingFang.ttc",
             "NotoSansCJK-Regular.ttc", "NotoSansSC-Regular.otf", "LXGWWenKai-Regular.ttf"],
    "hei": ["simhei.ttf", "msyhbd.ttf", "NotoSansCJK-Regular.ttc", "LXGWWenKai-Regular.ttf"],
    "marker": ["comic.ttf", "comicbd.ttf", "seguisb.ttf", "verdana.ttf"],
    "crayon": ["comicbd.ttf", "comic.ttf"],
    "type": ["cour.ttf", "couri.ttf", "consola.ttf", "lucon.ttf", "Courier New.ttf",
             "Menlo.ttc", "Monaco.ttf", "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"],
    "typewriter": ["cour.ttf", "couri.ttf", "Courier New.ttf", "Menlo.ttc", "DejaVuSansMono.ttf"],
}

_font_file_cache = {}


def _find_font_file(name):
    """按文件名在 FONT_DIRS 中查找字体，返回完整路径或空串。

    大小写不敏感；Linux/macOS 的字体常位于系统字体目录的子目录
    （如 /usr/share/fonts/truetype/dejavu/），故对非直命中情况递归扫描。
    结果按文件名缓存，避免重复遍历目录树。
    """
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


def parse_color(s, default=(43, 41, 38)):
    if not s:
        return default
    if isinstance(s, tuple):
        return s
    if s.startswith("#") and len(s) in (4, 7):
        h = s.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return default


def _lum(c):
    """相对亮度（Luma），用于判断文字与背景对比度。"""
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _relative_luminance(color):
    """计算 sRGB 颜色的相对亮度（WCAG 标准），返回 0-1。"""
    r, g, b = [c / 255.0 for c in color[:3]]
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(c1, c2):
    """计算两个颜色的 WCAG 对比度比值（1-21）。"""
    l1 = _relative_luminance(c1)
    l2 = _relative_luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def auto_text_color(img, x, y, w, h, user_color=None):
    """采样指定区域背景亮度，自动选择与背景对比足够的文字颜色。
    - user_color=None（auto 模式）：浅底用深字，深底用浅字
    - user_color 指定：WCAG 对比度 >=4.5 则保留，否则自动切换为黑/白
    返回 (color, was_switched, bg_lum)
    """
    W, H = img.size
    box = (max(0, x), max(0, y), min(W, x + w), min(H, y + h))
    if box[2] <= box[0] or box[3] <= box[1]:
        return (43, 41, 38), False, 128
    lums = list(img.convert("L").crop(box).tobytes())
    bg_lum = sum(lums) / len(lums) if lums else 128
    # 采样背景的平均 RGB（用于对比度计算）
    bg_rgb = tuple(img.crop(box).resize((1, 1)).getpixel((0, 0))[:3])
    DARK = (20, 18, 16)   # 近黑，保证对比度
    LIGHT = (250, 247, 240)  # 近白，保证对比度
    base = DARK if bg_lum >= 128 else LIGHT
    if user_color is None:
        return base, False, bg_lum
    # B3: WCAG 4.5:1 对比度强制标准
    cr = _contrast_ratio(user_color, bg_rgb)
    if cr >= 4.5:
        return user_color, False, bg_lum
    # 对比度不足，选择黑或白中对比度更高的那个
    cr_dark = _contrast_ratio(DARK, bg_rgb)
    cr_light = _contrast_ratio(LIGHT, bg_rgb)
    fallback = DARK if cr_dark >= cr_light else LIGHT
    return fallback, True, bg_lum


def load_font(spec: str, size: int) -> ImageFont.FreeTypeFont:
    """加载字体，失败时降级到内置默认字体（保证不崩溃）。"""
    if spec and os.path.isfile(spec):
        try:
            return ImageFont.truetype(spec, size)
        except Exception:
            pass  # 继续尝试别名
    names = ALIASES.get((spec or "serif").lower(), [spec or "serif"])
    for name in names:
        if not name:
            continue
        candidate = _find_font_file(name)
        if candidate:
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                continue
    # 兜底：所有字体都找不到时，降级到 PIL 内置默认字体
    print(f"  [警告] 找不到字体“{spec}”，已降级到内置默认字体（可能无中文字形）",
          file=sys.stderr)
    try:
        return ImageFont.load_default(size)
    except TypeError:
        # 旧版 Pillow 的 load_default 不接受 size 参数
        return ImageFont.load_default()


def has_cjk(text):
    """是否含中文或中文标点（这类字符必须用中文字体，否则渲染成空心方框）。"""
    return any(
        "一" <= c <= "鿿" or "　" <= c <= "〿" or "＀" <= c <= "￯"
        for c in (text or "")
    )


CJK_FONT_HINTS = ("msyh", "simhei", "simsun", "stkaiti", "simkai", "lxgw",
                  "stsong", "stxingka", "simli", "ukai", "deng", "kaiti",
                  "notoserifcjk", "notosanscjk", "pingfang")


def _resolved_is_cjk_font(spec):
    """按 ALIASES 顺序找到首个实际存在的候选文件，判断它是不是中文字体。"""
    names = ALIASES.get((spec or "serif").lower(), [spec or "serif"])
    for name in names:
        if not name:
            continue
        candidate = _find_font_file(name)
        if candidate:
            low = os.path.basename(candidate).lower()
            return any(hint in low for hint in CJK_FONT_HINTS)
    return False


def effective_spec(spec, text):
    """文本含中文、而所选西文字体（如 type=Courier New）不含中文字形时，回退到楷体 kai，避免豆腐块。"""
    if not has_cjk(text):
        return spec
    if spec and os.path.isfile(spec):  # 显式给定的字体文件，信任并保留
        return spec
    if _resolved_is_cjk_font(spec):
        return spec
    return "kai"


def _display_line(line, after_section, upper_after_section):
    """空行分界之后的季节/学名块自动英文大写；短诗块保持原样。"""
    if upper_after_section and after_section:
        return line.upper()
    return line


def text_size(text, font, spacing=0, section_gap=0, upper_after_section=False):
    widest, total_h = 0, 0
    line_gap = int(font.size * 0.22)
    after_section = False
    prev_blank = False
    for i, line in enumerate(text.split("\n")):
        if line.strip() == "":  # 空行=短诗/季节学名块分界，本身不占行高，只置标记
            after_section = True
            prev_blank = True
            continue
        disp = _display_line(line, after_section, upper_after_section)
        w = sum(_probe.textlength(c, font=font) for c in disp) + spacing * max(0, len(disp) - 1)
        bbox = _probe.textbbox((0, 0), disp or "口", font=font)
        lh = bbox[3] - bbox[1]
        widest = max(widest, w)
        if i == 0:
            total_h += lh
        elif prev_blank:
            total_h += section_gap + lh  # 跨块：2.5 倍字高段距
        else:
            total_h += line_gap + lh
        prev_blank = False
    return int(widest), int(total_h)


def fit_font(text, target_px, spec, spacing=0):
    spec = effective_spec(spec, text)
    lo, hi, best = 12, 1000, 12
    while lo <= hi:
        mid = (lo + hi) // 2
        w, _ = text_size(text, load_font(spec, mid), spacing)
        if w <= target_px:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return load_font(spec, best)


def render_lines_layer(text, font, color, spacing=0, align="left",
                       section_gap=0, upper_after_section=False):
    """普通多行文字渲染到透明层；空行(\n\n)为短诗/季节学名块分界，分界处用 section_gap 段距、分界后自动大写。"""
    raw_lines = text.split("\n")
    after_section = False
    rows = []
    for line in raw_lines:
        if line.strip() == "":
            after_section = True
            rows.append(("", True))
            continue
        rows.append((_display_line(line, after_section, upper_after_section), False))
    sizes = [text_size(disp, font, spacing) for disp, _ in rows]
    w = max(s[0] for s in sizes)
    line_gap = int(font.size * 0.22)
    _, h = text_size(text, font, spacing, section_gap, upper_after_section)
    layer = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = 4
    prev_blank, prev_lh = False, 0
    for idx, (disp, blank) in enumerate(rows):
        if blank:
            prev_blank = True
            continue
        lw, lh = sizes[idx]
        if idx == 0:
            pass
        elif prev_blank:
            y += section_gap
        else:
            y += prev_lh + line_gap
        x = 4 if align == "left" else (4 + (w - lw) // 2)
        for ch in disp:
            d.text((x, y), ch, font=font, fill=color)
            x += _probe.textlength(ch, font=font) + spacing
        prev_blank, prev_lh = False, lh
    return layer


def render_title_layer(text, spec, size, color, spacing_px, style):
    """艺术主标题：逐字变形后合成透明层。normal 时直接整行渲染（快速路径，避免逐字 tile+rotate 的重采样模糊与额外字距）。"""
    spec = effective_spec(spec, text)  # 含中文且西文字体无中文字形时自动回退
    # normal 快速路径：直接整行渲染，不逐字 tile/rotate(0,BICUBIC)
    if style == "normal":
        f = load_font(spec, int(size))
        char_widths = [_probe.textlength(ch, font=f) for ch in text]
        total_w = int(sum(char_widths) + spacing_px * max(0, len(text) - 1))
        bbox = _probe.textbbox((0, 0), text or "口", font=f)
        text_h = int(bbox[3] - bbox[1])
        total_h = text_h + 28 + int(size * 0.5)  # 高度与逐字路径一致，保证垂直落点相同
        layer = Image.new("RGBA", (max(1, total_w), max(1, total_h)), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        y = (total_h - text_h) // 2 - bbox[1]  # 垂直居中，与逐字路径一致
        x = 0
        for ch, cw in zip(text, char_widths):
            d.text((x - bbox[0], y), ch, font=f, fill=color)
            x += cw + spacing_px
        return layer
    chars = list(text)
    n = max(1, len(chars) - 1)
    pieces = []
    for i, ch in enumerate(chars):
        cs, ang, dy = size, 0.0, 0.0
        t = i / n
        if style == "italic":
            ang = -9
        elif style == "wave":
            dy = size * 0.14 * math.sin(t * math.pi)
            ang = 11 * math.sin(t * math.pi * 2)
        elif style == "arch":
            dy = -size * 0.22 * (1 - (2 * t - 1) ** 2)
            ang = (0.5 - t) * 26
        elif style == "scatter":
            r = ((i * 73 + 17) % 97) / 97
            ang = (r - 0.5) * 14
            dy = (r - 0.5) * size * 0.08
            cs = int(size * (0.94 + 0.12 * r))
        f = load_font(spec, int(cs))
        bbox = _probe.textbbox((0, 0), ch, font=f)
        cw, chh = int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])
        tile = Image.new("RGBA", (cw + 28, chh + 28), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((14 - bbox[0], 14 - bbox[1]), ch, font=f, fill=color)
        tile = tile.rotate(ang, expand=True, resample=Image.BICUBIC)
        pieces.append((tile, int(dy)))

    gap = spacing_px
    total_w = sum(p.width for p, _ in pieces) + gap * (len(pieces) - 1)
    total_h = max(p.height for p, _ in pieces) + int(size * 0.5)
    canvas = Image.new("RGBA", (max(1, total_w), max(1, total_h)), (0, 0, 0, 0))
    x = 0
    for piece, dy in pieces:
        y = (total_h - piece.height) // 2 + dy
        canvas.alpha_composite(piece, (x, y))
        x += piece.width + gap
    return canvas


def anchor_top_left(W, H, pos, bw, bh, margin):
    if pos == "center":
        return (W - bw) // 2, (H - bh) // 2
    row = col = "middle"
    if pos.startswith("top"):
        row = "top"
    elif pos.startswith("bottom"):
        row = "bottom"
    if pos.endswith("left"):
        col = "left"
    elif pos.endswith("right"):
        col = "right"
    elif pos.endswith("center"):
        col = "center"
    x = margin if col == "left" else (W - margin - bw if col == "right" else (W - bw) // 2)
    y = margin if row == "top" else (H - margin - bh if row == "bottom" else (H - bh) // 2)
    return x, y


def parse_xy(spec, W, H):
    x_s, y_s = spec.split(",")
    return int(float(x_s.strip().rstrip("%")) / 100 * W), int(float(y_s.strip().rstrip("%")) / 100 * H)


def paste_layer(img, layer, center_or_topleft, is_center=False, rotate=0, bounds=None):
    if rotate:
        layer = layer.rotate(rotate, expand=True, resample=Image.BICUBIC)
    if is_center:
        cx, cy = center_or_topleft
        x, y = cx - layer.width // 2, cy - layer.height // 2
    else:
        x, y = center_or_topleft
    if bounds:
        m, W, H = bounds
        x = max(m, min(x, W - m - layer.width))
        y = max(m, min(y, H - m - layer.height))
    img.paste(layer, (x, y), layer)


def main():
    ap = argparse.ArgumentParser(description="静物插画文字合成")
    ap.add_argument("image", nargs="?", help="输入图片路径（单张模式必填；--batch 模式可省略）")
    ap.add_argument("--batch", help="批量模式：指定目录，自动读取 *_overlay.json 并对 A/B 校正图批量叠字")
    ap.add_argument("--title", default="", help="主标题；通常必填，为空则只叠次要文字")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--title-font", default="serif")
    ap.add_argument("--subtitle-font", default="type")
    ap.add_argument("--title-pos", default="top-center",
                    choices=["top-left", "top-center", "top-right", "center",
                             "middle-left", "middle-right",
                             "bottom-left", "bottom-center", "bottom-right"])
    ap.add_argument("--subtitle-pos", default="follow")
    ap.add_argument("--title-xy", default="", help="主标题块中心，如 45%%,28%%（覆盖 --title-pos）")
    ap.add_argument("--subtitle-xy", default="", help="次要文字块中心，如 50%%,88%%")
    ap.add_argument("--title-rotate", type=float, default=0.0)
    ap.add_argument("--subtitle-rotate", type=float, default=0.0)
    ap.add_argument("--title-width", type=float, default=0.30, help="主标题占版面比例（默认 0.30）")
    ap.add_argument("--subtitle-ratio", type=float, default=0.25,
                    help="次要文字字号占主标题字号比例 0.18-0.36（--subtitle-size-px>0 时被覆盖）")
    ap.add_argument("--subtitle-size-px", type=int, default=20,
                    help="次要文字/短诗固定字号(px)，默认20；>0时覆盖--subtitle-ratio比例自适应")
    ap.add_argument("--title-size-px", type=int, default=120,
                    help="主标题固定字号(px)，默认120；>0时覆盖--title-width自适应，设为0则回退比例自适应；标题字符数建议不超过22")
    ap.add_argument("--letter-spacing", type=float, default=0.08, help="主标题字距占字号比例，默认稀疏")
    ap.add_argument("--subtitle-tracking", type=float, default=-0.06, help="次要文字字距，默认收紧")
    ap.add_argument("--subtitle-section-gap", type=float, default=2.5,
                    help="短诗块与季节/学名块之间的段距=次要字高的倍数（默认2.5；用空行\\n\\n分界）")
    ap.add_argument("--no-upper-section", dest="upper_section", action="store_false",
                    help="关闭空行分界后季节/学名的自动英文大写（默认开启）")
    ap.set_defaults(upper_section=True)
    ap.add_argument("--title-style", default="normal",
                    choices=["normal", "italic", "wave", "arch", "scatter"])
    ap.add_argument("--margin", type=float, default=0.12)
    ap.add_argument("--color", default="auto")
    ap.add_argument("--subtitle-color", default="")
    ap.add_argument("--no-auto-contrast", dest="auto_contrast", action="store_false",
                    help="关闭次要文字颜色自动对比（默认开启：采样落点背景亮度自动选深/浅色保证可读）")
    ap.set_defaults(auto_contrast=True)
    ap.add_argument("--vertical", action="store_true", help="主标题中文竖排（不做艺术变形）")
    ap.add_argument("-o", "--output", default="", help="输出图片路径（单张模式必填；--batch 模式自动命名）")
    args = ap.parse_args()

    # ---- 批量模式：遍历目录下的 *_overlay.json，对 A/B 校正图批量叠字 ----
    if args.batch:
        import glob as _glob
        import subprocess as _sp
        batch_dir = os.path.abspath(args.batch)
        overlay_files = sorted(_glob.glob(os.path.join(batch_dir, "*_overlay.json")))
        if not overlay_files:
            sys.exit(f"错误：目录 {batch_dir} 下未找到 *_overlay.json 文件")

        print(f"===== 批量叠字：找到 {len(overlay_files)} 个 overlay 配置 =====")
        ok_count, fail_count = 0, 0
        script_path = os.path.abspath(__file__)

        for ov_path in overlay_files:
            base_id = os.path.basename(ov_path).replace("_overlay.json", "")
            try:
                with open(ov_path, "r", encoding="utf-8-sig") as f:
                    ov = json.load(f)
            except Exception as ex:
                print(f"  [FAIL] {base_id}: 读取 overlay.json 失败: {ex}")
                fail_count += 1
                continue

            common = ov.get("common", {})
            views = ov.get("views", {})

            for tag in ("A", "B"):
                if tag not in views:
                    continue
                view = views[tag]
                # 查找校正图：优先 <id>_<tag>.png，其次 <id>_<tag>.jpg
                img_path = None
                for ext in (".png", ".jpg", ".jpeg"):
                    candidate = os.path.join(batch_dir, f"{base_id}_{tag}{ext}")
                    if os.path.exists(candidate):
                        img_path = candidate
                        break
                if not img_path:
                    print(f"  [FAIL] {base_id}_{tag}: 未找到校正图（{base_id}_{tag}.png/jpg）")
                    fail_count += 1
                    continue

                out_path = os.path.join(batch_dir, f"{base_id}_{tag}_final.png")
                subtitle_lines = common.get("subtitle_lines", [])
                subtitle_text = "\n".join(str(l) for l in subtitle_lines if l is not None)

                # 构造命令行参数，调用自己（单张模式）
                cmd = [
                    sys.executable, script_path, img_path,
                    "--title", str(common.get("title", "")),
                    "--subtitle", subtitle_text,
                    "--title-font", str(common.get("title_font", "serif")),
                    "--title-style", str(common.get("title_style", "normal")),
                    "--title-size-px", str(common.get("title_size_px", 180)),
                    "--subtitle-size-px", str(common.get("subtitle_size_px", 30)),
                    "--title-width", str(common.get("title_width", 0.30)),
                    "--subtitle-ratio", str(common.get("sub_ratio", 0.25)),
                    "--subtitle-pos", "follow",
                    "-o", out_path,
                ]
                # 可选参数
                if common.get("title_color"):
                    cmd += ["--color", str(common["title_color"])]
                if common.get("sub_color"):
                    cmd += ["--subtitle-color", str(common["sub_color"])]
                if view.get("title_pos"):
                    cmd += ["--title-pos", str(view["title_pos"])]
                if view.get("sub_xy"):
                    # 保留 brief 规划的次文预留角（与主标题对角的干净留白）；
                    # 与主标题是否重叠由单张层的真实边界框兜底判断
                    cmd += ["--subtitle-xy", str(view["sub_xy"])]

                try:
                    # 子进程输出统一按 UTF-8 解码，避免 Windows cp936 控制台中文告警乱码
                    _sp_env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
                    result = _sp.run(cmd, capture_output=True, text=True, timeout=60,
                                     encoding="utf-8", errors="replace", env=_sp_env)
                    if result.returncode == 0:
                        print(f"  [OK]   {base_id}_{tag}: {out_path}")
                        ok_count += 1
                    else:
                        err = result.stderr.strip() or result.stdout.strip()
                        print(f"  [FAIL] {base_id}_{tag}: {err[:200]}")
                        fail_count += 1
                except Exception as ex:
                    print(f"  [FAIL] {base_id}_{tag}: 调用失败: {ex}")
                    fail_count += 1

        print(f"\n===== 批量叠字完成：成功 {ok_count} / 失败 {fail_count} / 总计 {ok_count + fail_count} =====")
        sys.exit(1 if fail_count else 0)

    # ---- 单张模式 ----
    if not args.image:
        sys.exit("错误：单张模式必须提供输入图片路径，或使用 --batch 批量模式")
    if not args.output:
        sys.exit("错误：单张模式必须提供 -o/--output 输出路径")

    if args.subtitle and not 0.18 <= args.subtitle_ratio <= 0.36:
        print("提示: 次要文字字号应为主标题的 0.18-0.36，已按你的输入继续", file=sys.stderr)
    if args.title and args.subtitle:
        # 按"回退后的实际字体"判断主/次是否撞字体（中文会把西文字体回退到 kai）
        eff_t = effective_spec(args.title_font, args.title)
        eff_s = effective_spec(args.subtitle_font, args.subtitle)
        norm = lambda s: s.split("\\")[-1].split("/")[-1].lower()
        if norm(eff_t) == norm(eff_s):
            sys.exit("主标题与次要文字实际字体相同（中文会自动回退到 kai 楷体）："
                     "请把主标题换成 serif/song/hand/sans 之一，或用 --subtitle-font 指定不同字体")

    img = Image.open(args.image).convert("RGBA")
    W, H = img.size
    margin = int(min(W, H) * args.margin)

    # ---- 主标题 ----
    if args.title:
        if args.title_size_px and args.title_size_px > 0:
            # 固定字号模式（默认180px）
            t_font = load_font(args.title_font, args.title_size_px)
            t_spacing = int(t_font.size * args.letter_spacing)
        else:
            # 自适应模式（按 --title-width 比例）
            _tile_pad = 28 * max(1, len(args.title))  # 每字符 tile 左右各14px padding
            target = (H * args.title_width if args.vertical else W * args.title_width) - _tile_pad
            t_font = fit_font(args.title, target, args.title_font)
            t_spacing = int(t_font.size * args.letter_spacing)
            t_font = fit_font(args.title, target, args.title_font, t_spacing)

        # 主标题排法
        style = args.title_style
        # 自动截断：固定字号下如果标题超出画面可用宽度，逐词截断（舍弃被截断的词，不显示半个词）
        _max_title_w = W - 2 * margin
        _title_text = args.title
        while _title_text:
            _tmp_check = render_title_layer(_title_text, args.title_font, t_font.size, (0, 0, 0), t_spacing, style)
            if _tmp_check.width <= _max_title_w:
                break
            _words = _title_text.rsplit(None, 1)
            if len(_words) > 1:
                _title_text = _words[0]
            else:
                _title_text = _title_text[:-1]
        if _title_text != args.title:
            print(f"提示: 主标题过长已自动截断为: {_title_text}", file=sys.stderr)
            args.title = _title_text

        # 主标题颜色：auto 模式或自动对比开启时，先算位置再采样背景选色
        # 先用临时颜色渲染，计算尺寸和落点
        _tmp = render_title_layer(args.title, args.title_font, t_font.size, (0, 0, 0), t_spacing, style)
        if args.title_xy:
            _cx, _cy = parse_xy(args.title_xy, W, H)
            _tx, _ty = _cx - _tmp.width // 2, _cy - _tmp.height // 2
        else:
            _tx, _ty = anchor_top_left(W, H, args.title_pos, _tmp.width, _tmp.height, margin)
        _tx = max(margin, min(_tx, W - margin - _tmp.width))
        _ty = max(margin, min(_ty, H - margin - _tmp.height))

        if args.color == "auto" or args.auto_contrast:
            user_c = None if args.color == "auto" else parse_color(args.color)
            t_color, switched, bg_lum = auto_text_color(img, _tx, _ty, _tmp.width, _tmp.height, user_c)
            if switched:
                kind = "深色" if _lum(t_color) < 128 else "浅色"
                print(f"提示: 主标题指定色与背景明度差不足(背景亮度{bg_lum:.0f})，已自动改用{kind}保证清晰",
                      file=sys.stderr)
        else:
            t_color = parse_color(args.color)

        if args.vertical:
            tw, th = text_size(args.title, t_font, t_spacing)
            tx, ty = anchor_top_left(W, H, args.title_pos, tw, th, margin)
            tl = Image.new("RGBA", (tw + 8, th + 8), (0, 0, 0, 0))
            d = ImageDraw.Draw(tl)
            cy = 4
            for ch in args.title:
                cw = _probe.textlength(ch, font=t_font)
                d.text((4 + (tw - cw) / 2, cy), ch, font=t_font, fill=t_color)
                cy += cw + t_spacing
            paste_layer(img, tl, (tx - 4, ty - 4))
        else:
            title_layer = render_title_layer(
                args.title, args.title_font, t_font.size, t_color, t_spacing, style)
            if args.title_xy:
                paste_layer(img, title_layer, parse_xy(args.title_xy, W, H), True,
                            args.title_rotate, bounds=(margin, W, H))
            else:
                paste_layer(img, title_layer, (_tx, _ty), False, args.title_rotate,
                            bounds=(margin, W, H))

    # ---- 次要文字 ----
    if args.subtitle:
        if args.subtitle_size_px and args.subtitle_size_px > 0:
            # 固定字号模式（默认30px）
            s_size = args.subtitle_size_px
        elif args.title:
            s_size = int(t_font.size * args.subtitle_ratio)
        elif args.title_size_px:
            s_size = int(args.title_size_px * args.subtitle_ratio)
        else:
            s_size = int(H * 0.03)
        max_w = W - 2 * margin
        sub_spec = effective_spec(args.subtitle_font, args.subtitle)  # 中文自动回退中文字体，避免豆腐块
        if sub_spec != args.subtitle_font:
            print(f"提示: 次要文字含中文，{args.subtitle_font} 无中文字形，已自动回退到 {sub_spec} 字体",
                  file=sys.stderr)
        probe = None
        if s_size < 12:  # 字号下限保护：主标题过小时也保证次要文字至少渲染一次
            s_size = 12
        while s_size >= 12:  # 字号自适应：最长行不得超出安全宽度
            s_font = load_font(sub_spec, s_size)
            s_spacing = int(s_size * args.subtitle_tracking)
            sec_gap = int(s_size * args.subtitle_section_gap)
            probe = render_lines_layer(args.subtitle, s_font, (0, 0, 0), s_spacing,
                                       section_gap=sec_gap, upper_after_section=args.upper_section)
            if probe.width - 8 <= max_w:
                break
            s_size -= 2

        # 先算次要文字块落点，再采样背景，自动选一个与背景对比足够的颜色
        sw, sh = probe.width - 8, probe.height - 8
        if args.subtitle_xy:
            cx, cy = parse_xy(args.subtitle_xy, W, H)
            tx, ty = cx - sw // 2, cy - sh // 2
        else:
            pos = args.subtitle_pos
            if pos == "follow":
                row = "top" if args.title_pos.startswith("bottom") else "bottom"
                col = "left" if args.title_pos.endswith("left") else \
                      "right" if args.title_pos.endswith("right") else "center"
                pos = f"{row}-{col}"
            tx, ty = anchor_top_left(W, H, pos, sw, sh, margin)
        tx = max(margin, min(tx, W - margin - sw))
        ty = max(margin, min(ty, H - margin - sh))

        # B: 运行时重叠检测兜底——主标题与次要文字边界框重叠时，自动下移次要文字
        if args.title:
            title_box = (_tx, _ty, _tx + _tmp.width, _ty + _tmp.height)
            sub_box = (tx, ty, tx + sw, ty + sh)
            overlap = (max(title_box[0], sub_box[0]) < min(title_box[2], sub_box[2]) and
                       max(title_box[1], sub_box[1]) < min(title_box[3], sub_box[3]))
            if overlap:
                ty = title_box[3] + margin
                ty = max(margin, min(ty, H - margin - sh))

        DARK, LIGHT = (72, 56, 44), (245, 240, 229)  # 手绘感深棕 / 暖白，非纯黑纯白


        user_color = parse_color(args.subtitle_color) if args.subtitle_color else None
        if args.auto_contrast:
            box = (max(0, tx), max(0, ty), min(W, tx + sw), min(H, ty + sh))
            lums = list(img.convert("L").crop(box).tobytes())  # 灰度字节即亮度，避免 getdata
            bg_lum = sum(lums) / len(lums)
            bg_std = statistics.pstdev(lums)
            base = DARK if bg_lum >= 128 else LIGHT  # 浅底用深字，深底用浅字
            if user_color is None:
                s_color = base
            elif abs(_lum(user_color) - bg_lum) >= 90:
                s_color = user_color  # 指定色对比已足够
            else:
                kind = "深色" if base == DARK else "浅色"
                print(f"提示: 次要文字指定色与背景明度差不足(背景亮度{bg_lum:.0f})，已自动改用{kind}保证清晰",
                      file=sys.stderr)
                s_color = base
            if bg_std > 55:
                print("提示: 次要文字落点背景深浅不一，建议用 --subtitle-xy 移到干净留白区",
                      file=sys.stderr)
        else:
            s_color = user_color or (107, 107, 102)

        sub = render_lines_layer(args.subtitle, s_font, s_color, s_spacing,
                                 section_gap=int(s_size * args.subtitle_section_gap),
                                 upper_after_section=args.upper_section)
        img.paste(sub, (tx - 4, ty - 4), sub)

    img.convert("RGB").save(args.output, quality=95)
    msg = f"已保存: {args.output}"
    if args.title:
        if args.title_size_px and args.title_size_px > 0:
            msg += f"  主标题字号={t_font.size}px(固定) 风格={args.title_style}"
        else:
            msg += f"  主标题字号≈{t_font.size}px 占比={args.title_width:.0%} 风格={args.title_style}"
    print(msg)


if __name__ == "__main__":
    main()
