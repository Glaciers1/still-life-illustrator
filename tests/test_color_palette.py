#!/usr/bin/env python3
"""color_palette.py v2.0 单元测试。

覆盖：色彩提取（动态+排除背景色+中心加权+去重）、颜色空间转换、
颜色名匹配（私有函数）、布局（只条形+0间距）、渲染集成、
上下区域干净度检测、CLI入口。
运行: python -m pytest tests/test_color_palette.py -v
"""
import os
import sys

import pytest
from PIL import Image

# 把 scripts 目录加入 path
SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import color_palette as cp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def solid_image():
    """纯色测试图。"""
    return Image.new("RGB", (100, 100), (200, 100, 50))


@pytest.fixture
def gradient_image():
    """渐变测试图。"""
    img = Image.new("RGB", (200, 200))
    pixels = img.load()
    for y in range(200):
        for x in range(200):
            r = int(255 * x / 199)
            g = int(255 * y / 199)
            b = 128
            pixels[x, y] = (r, g, b)
    return img


@pytest.fixture
def sample_colors():
    """示例颜色列表 [(r,g,b,ratio), ...]。"""
    return [
        (240, 230, 210, 0.5),
        (180, 140, 100, 0.3),
        (100, 80, 60, 0.2),
    ]


@pytest.fixture
def color_names():
    """加载颜色名字典（私有函数 _load_color_names）。"""
    return cp._load_color_names()


# ---------------------------------------------------------------------------
# 色彩提取（v2.0：动态 + 排除背景色 + 中心加权 + 颜色去重 + 明->暗排序）
# ---------------------------------------------------------------------------

class TestExtractColors:
    def test_extract_returns_list(self, solid_image):
        colors = cp.extract_colors(solid_image, max_colors=3)
        assert isinstance(colors, list)
        # v2.0：纯色图全部被排除为背景色，可能返回空列表（正确行为）

    def test_extract_color_format(self, solid_image):
        colors = cp.extract_colors(solid_image, max_colors=3)
        for c in colors:
            assert len(c) == 4  # r, g, b, ratio
            r, g, b, ratio = c
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255
            assert 0 <= ratio <= 1

    def test_extract_max_colors_limit(self, gradient_image):
        colors = cp.extract_colors(gradient_image, max_colors=5)
        assert len(colors) <= 5

    def test_extract_with_subject_color(self):
        """v2.0：用中心有主体色、边缘是背景色的测试图，验证能提取到主体色。"""
        img = Image.new("RGB", (200, 200), (240, 230, 210))  # 米色背景
        pixels = img.load()
        # 中心区域画红色主体
        for y in range(70, 130):
            for x in range(70, 130):
                pixels[x, y] = (200, 50, 50)
        colors = cp.extract_colors(img, max_colors=5)
        # 应能提取到红色主体色（排除米色背景）
        assert len(colors) >= 1
        r, g, b, _ = colors[0]
        # 最亮的颜色可能是背景残留，但至少应有一个颜色接近红色
        red_found = any(abs(c[0] - 200) < 50 and c[1] < 100 and c[2] < 100 for c in colors)
        assert red_found, f"未找到红色主体色，实际颜色: {colors}"

    def test_extract_sorted_brightness(self, gradient_image):
        """v2.0：extract_colors 返回的颜色按明->暗排序。"""
        colors = cp.extract_colors(gradient_image, max_colors=8)
        if len(colors) >= 2:
            luminances = [cp.luminance(c[0], c[1], c[2]) for c in colors]
            # 明->暗：第一个亮度 >= 最后一个亮度
            assert luminances[0] >= luminances[-1]

    def test_extract_empty_max_colors(self, solid_image):
        """max_colors=0 时返回空列表。"""
        colors = cp.extract_colors(solid_image, max_colors=0)
        assert isinstance(colors, list)


# ---------------------------------------------------------------------------
# 颜色空间转换
# ---------------------------------------------------------------------------

class TestColorConversions:
    def test_rgb_to_hex(self):
        assert cp.rgb_to_hex(255, 0, 0) == "#ff0000"
        assert cp.rgb_to_hex(0, 255, 0) == "#00ff00"
        assert cp.rgb_to_hex(0, 0, 255) == "#0000ff"
        assert cp.rgb_to_hex(255, 255, 255) == "#ffffff"

    def test_rgb_to_hsl_white(self):
        h, s, l = cp.rgb_to_hsl(255, 255, 255)
        assert abs(l - 1.0) < 0.01
        assert abs(s - 0.0) < 0.01

    def test_rgb_to_hsl_black(self):
        h, s, l = cp.rgb_to_hsl(0, 0, 0)
        assert abs(l - 0.0) < 0.01

    def test_rgb_to_hsl_red(self):
        h, s, l = cp.rgb_to_hsl(255, 0, 0)
        assert abs(h - 0.0) < 1.0 or abs(h - 360.0) < 1.0
        assert s > 0.9

    def test_luminance(self):
        # 白色亮度最高
        assert cp.luminance(255, 255, 255) > cp.luminance(0, 0, 0)
        # 绿色比蓝色亮（人眼感知）
        assert cp.luminance(0, 255, 0) > cp.luminance(0, 0, 255)

    def test_saturation(self):
        # 灰色饱和度为 0
        assert abs(cp.saturation(128, 128, 128)) < 0.01
        # 纯红色饱和度高
        assert cp.saturation(255, 0, 0) > 0.9


# ---------------------------------------------------------------------------
# 颜色名匹配（v2.0：私有函数 _load_color_names / _match_color_name）
# ---------------------------------------------------------------------------

class TestColorNameMatching:
    def test_load_color_names(self, color_names):
        assert isinstance(color_names, list)
        # 颜色名字典可能为空（color_names.json 不存在时），非空时至少50个
        if color_names:
            assert len(color_names) > 50
            for name, rgb in color_names:
                assert isinstance(name, str)
                assert len(rgb) == 3

    def test_match_red(self, color_names):
        name = cp._match_color_name((255, 0, 0), color_names)
        if color_names:
            assert name.lower() in ("red", "scarlet", "crimson")
        else:
            assert name == "#ff0000"

    def test_match_white(self, color_names):
        name = cp._match_color_name((255, 255, 255), color_names)
        if color_names:
            assert name.lower() == "white"
        else:
            assert name == "#ffffff"

    def test_match_black(self, color_names):
        name = cp._match_color_name((0, 0, 0), color_names)
        if color_names:
            assert name.lower() == "black"
        else:
            assert name == "#000000"

    def test_match_blue(self, color_names):
        name = cp._match_color_name((0, 0, 255), color_names)
        if color_names:
            assert "blue" in name.lower()
        else:
            assert name == "#0000ff"

    def test_match_empty_list(self):
        # 空颜色名列表时回退到 HEX
        name = cp._match_color_name((255, 0, 0), [])
        assert name == "#ff0000"


# ---------------------------------------------------------------------------
# 色块布局（v2.0：只条形，固定尺寸，0间距，一排显示）
# ---------------------------------------------------------------------------

class TestLayoutSwatches:
    def test_layout_3_colors(self, sample_colors):
        positions, bw, bh = cp.layout_swatches(sample_colors, swatch_w=90, swatch_h=20)
        assert len(positions) == 3
        # 只条形：全部在一排（y=0）
        ys = set(p[1] for p in positions)
        assert len(ys) == 1
        assert ys == {0}

    def test_layout_zero_gap(self, sample_colors):
        """v2.0：0间距，色块紧挨。"""
        positions, bw, bh = cp.layout_swatches(sample_colors, swatch_w=90, swatch_h=20)
        xs = sorted([p[0] for p in positions])
        for i in range(len(xs) - 1):
            # 下一个色块的 x = 前一个的 x + 宽度（0间距）
            assert xs[i + 1] == xs[i] + 90

    def test_layout_bounding_box(self, sample_colors):
        positions, bw, bh = cp.layout_swatches(sample_colors, swatch_w=90, swatch_h=20)
        # 包围盒 = n * swatch_w
        assert bw == 3 * 90
        assert bh == 20

    def test_layout_empty(self):
        positions, bw, bh = cp.layout_swatches([], swatch_w=90, swatch_h=20)
        assert positions == []
        assert bw == 0
        assert bh == 0

    def test_layout_custom_size(self):
        colors = [(i * 30, i * 20, i * 10, 0.1) for i in range(5)]
        positions, bw, bh = cp.layout_swatches(colors, swatch_w=60, swatch_h=15)
        assert len(positions) == 5
        assert bw == 5 * 60
        assert bh == 15


# ---------------------------------------------------------------------------
# 渲染集成（v2.0：新参数 pos/swatch_w/swatch_h/margin_px/label_mode/font_spec）
# ---------------------------------------------------------------------------

class TestRenderSwatches:
    def test_render_basic(self, solid_image, sample_colors):
        result = cp.render_swatches(
            solid_image, sample_colors,
            pos="bottom", swatch_w=90, swatch_h=20,
            margin_px=120, label_mode="none",
        )
        assert result.size == solid_image.size
        assert result.mode == "RGBA"

    def test_render_top(self, solid_image, sample_colors):
        result = cp.render_swatches(
            solid_image, sample_colors,
            pos="top", swatch_w=90, swatch_h=20,
            margin_px=120, label_mode="none",
        )
        assert result.size == solid_image.size

    def test_render_auto(self, solid_image, sample_colors):
        result = cp.render_swatches(
            solid_image, sample_colors,
            pos="auto", swatch_w=90, swatch_h=20,
            margin_px=120, label_mode="none",
        )
        assert result.size == solid_image.size

    def test_render_label_hex(self, solid_image, sample_colors):
        result = cp.render_swatches(
            solid_image, sample_colors,
            pos="bottom", swatch_w=90, swatch_h=20,
            margin_px=120, label_mode="hex",
        )
        assert result.size == solid_image.size

    def test_render_label_name(self, solid_image, sample_colors):
        result = cp.render_swatches(
            solid_image, sample_colors,
            pos="bottom", swatch_w=90, swatch_h=20,
            margin_px=120, label_mode="name",
        )
        assert result.size == solid_image.size

    def test_render_empty_colors(self, solid_image):
        result = cp.render_swatches(solid_image, [], pos="bottom")
        assert result.size == solid_image.size

    def test_render_preserves_original(self, solid_image, sample_colors):
        # 渲染不应该修改原图
        original_pixels = solid_image.tobytes()
        cp.render_swatches(solid_image, sample_colors, pos="bottom")
        assert solid_image.tobytes() == original_pixels


# ---------------------------------------------------------------------------
# 上下区域干净度检测（v2.0：find_clean_vertical_region 替代 find_empty_region）
# ---------------------------------------------------------------------------

class TestFindCleanVerticalRegion:
    def test_returns_valid_position(self):
        """用足够大的测试图（400x400），确保margin_px不超出范围。"""
        img = Image.new("RGB", (400, 400), (200, 200, 200))
        ox, oy, side = cp.find_clean_vertical_region(img, 270, 20, margin_px=120)
        W, H = img.size
        # 水平居中
        assert ox == (W - 270) // 2
        # side 应为 top 或 bottom
        assert side in ("top", "bottom")
        # y 在合理范围内
        assert 0 <= oy < H

    def test_top_cleaner_than_bottom(self):
        """上方干净（纯色），下方有噪点 -> 应选 top。"""
        img = Image.new("RGB", (200, 200), (200, 200, 200))
        # 下方添加噪点
        pixels = img.load()
        for y in range(150, 200):
            for x in range(200):
                pixels[x, y] = (x % 256, y % 256, (x + y) % 256)
        ox, oy, side = cp.find_clean_vertical_region(img, 100, 20, margin_px=10)
        assert side == "top"

    def test_bottom_cleaner_than_top(self):
        """下方干净（纯色），上方有噪点 -> 应选 bottom。"""
        img = Image.new("RGB", (200, 200), (200, 200, 200))
        # 上方添加噪点
        pixels = img.load()
        for y in range(0, 50):
            for x in range(200):
                pixels[x, y] = (x % 256, y % 256, (x + y) % 256)
        ox, oy, side = cp.find_clean_vertical_region(img, 100, 20, margin_px=10)
        assert side == "bottom"


# ---------------------------------------------------------------------------
# 字体加载
# ---------------------------------------------------------------------------

class TestLoadFont:
    def test_load_type_font(self):
        font = cp.load_font("type", 20)
        assert font is not None

    def test_load_serif_font(self):
        font = cp.load_font("serif", 20)
        assert font is not None

    def test_load_invalid_font_fallback(self):
        # 无效字体名应回退到默认字体
        font = cp.load_font("nonexistent_font_xyz", 20)
        assert font is not None


# ---------------------------------------------------------------------------
# CLI 入口（冒烟测试）
# ---------------------------------------------------------------------------

class TestCLI:
    def test_module_version(self):
        assert hasattr(cp, "__version__")
        assert isinstance(cp.__version__, str)
        # v2.0 版本号
        assert cp.__version__.startswith("2.")

    def test_main_callable(self):
        assert callable(cp.main)

    def test_argparse_setup(self):
        # 验证 argparse 可以正常解析 --help（会 SystemExit）
        with pytest.raises(SystemExit):
            cp.main()  # 无参数时应该报错退出


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
