# -*- coding: utf-8 -*-
"""still-life-illustrator 单元测试
覆盖：validate_brief 核心校验、self_merge 合并逻辑、overlay_text 色差/字体/位置算法

运行方式：
    cd <skill_root>
    python -m pytest tests/ -v
"""
import os
import sys
import json
import pytest

# 把 scripts 目录加入 path，方便 import
SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import validate_brief
import self_merge
import overlay_text


# ============================================================
# validate_brief.py 测试
# ============================================================

class TestValidateBrief:
    """validate_brief.brief_errors 核心校验测试"""

    def _load_fixture(self, name):
        """从 tests/fixtures/ 加载示例 brief"""
        fp = os.path.join(os.path.dirname(__file__), "fixtures", name)
        with open(fp, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    def test_valid_solo_brief_no_errors(self):
        """有效的 Solo brief 不应有 error"""
        b = self._load_fixture("valid_brief_solo.json")
        errors, warns = validate_brief.brief_errors(b)
        assert len(errors) == 0, f"不应有 error: {errors}"

    def test_valid_standard_brief_no_errors(self):
        """有效的 Standard brief 不应有 error"""
        b = self._load_fixture("valid_brief_standard.json")
        errors, warns = validate_brief.brief_errors(b)
        assert len(errors) == 0, f"不应有 error: {errors}"

    def test_invalid_cast_mismatch_has_error(self):
        """cast_size 与 secondary 不符应有 error"""
        b = self._load_fixture("invalid_brief_cast_mismatch.json")
        errors, warns = validate_brief.brief_errors(b)
        assert len(errors) > 0, "cast_size=3 但 secondary=[] 应报错"

    def test_missing_required_fields(self):
        """缺少必填字段应报错"""
        b = {"id": "X001"}  # 缺少 hero/views/text 等
        errors, warns = validate_brief.brief_errors(b)
        assert len(errors) > 0, "缺少必填字段应报错"

    def test_views_not_ab(self):
        """views 不是 A/B 两个应报错"""
        b = self._load_fixture("valid_brief_solo.json")
        b["views"] = [{"tag": "A"}, {"tag": "C"}]  # 缺少 B
        errors, warns = validate_brief.brief_errors(b)
        assert len(errors) > 0, "views 不是 A/B 应报错"

    def test_pv_en_word_count(self):
        """pv_en 词数偏离 90-130 应有 warn"""
        b = self._load_fixture("valid_brief_solo.json")
        b["views"][0]["pv_en"] = "too short"  # 只有 2 词
        errors, warns = validate_brief.brief_errors(b)
        # pv_en 词数可能是 warn 或 error，取决于实现
        assert len(errors) + len(warns) > 0, "pv_en 词数偏离应提示"


# ============================================================
# self_merge.py 测试
# ============================================================

class TestSelfMerge:
    """self_merge 合并逻辑测试"""

    def _load_fixture(self, name):
        fp = os.path.join(os.path.dirname(__file__), "fixtures", name)
        with open(fp, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    def test_merge_one_preserves_skeleton_fields(self):
        """合并后应保留骨架中的结构字段（id/schema/source/cast_size 等）"""
        skeleton = self._load_fixture("valid_brief_solo.json")
        creative = {
            "hero": {"name": "测试主体", "en": "test hero", "count": 1, "states": "whole"},
            "secondary": [],
            "views": skeleton["views"],
            "text": skeleton["text"]
        }
        merged = self_merge.merge_one(skeleton, creative)
        assert merged["id"] == skeleton["id"]
        assert merged["schema"] == skeleton["schema"]
        assert merged["cast_size"] == skeleton["cast_size"]

    def test_check_pv_en_valid_range(self):
        """pv_en 90-130 词应通过检查"""
        b = self._load_fixture("valid_brief_solo.json")
        # valid brief 的 pv_en 应该在范围内
        result = self_merge.check_pv_en(b)
        # check_pv_en 返回 (bool, msg) 元组
        if isinstance(result, tuple):
            assert result[0] is True, f"check_pv_en 应通过: {result}"
        else:
            assert result is True or isinstance(result, list), "check_pv_en 应返回布尔或问题列表"

    def test_check_poem_two_lines(self):
        """poem 恰好 2 行应通过检查"""
        b = self._load_fixture("valid_brief_solo.json")
        result = self_merge.check_poem(b)
        # check_poem 返回 (bool, msg) 元组
        if isinstance(result, tuple):
            assert result[0] is True, f"check_poem 应通过: {result}"
        else:
            assert result is True or isinstance(result, list), "check_poem 应返回布尔或问题列表"


# ============================================================
# overlay_text.py 测试
# ============================================================

class TestOverlayText:
    """overlay_text 色差/字体/位置算法测试"""

    # --- parse_color ---
    def test_parse_color_hex(self):
        """十六进制颜色解析"""
        assert overlay_text.parse_color("#FF0000") == (255, 0, 0)
        assert overlay_text.parse_color("#00ff00") == (0, 255, 0)

    def test_parse_color_short_hex(self):
        """短十六进制颜色解析"""
        assert overlay_text.parse_color("#F00") == (255, 0, 0)

    def test_parse_color_empty_returns_default(self):
        """空字符串返回默认色"""
        default = (10, 20, 30)
        assert overlay_text.parse_color("", default=default) == default

    def test_parse_color_invalid_returns_default(self):
        """无效格式返回默认色"""
        default = (10, 20, 30)
        assert overlay_text.parse_color("not-a-color", default=default) == default

    # --- _lum ---
    def test_lum_black(self):
        """黑色亮度为 0"""
        assert overlay_text._lum((0, 0, 0)) == 0

    def test_lum_white(self):
        """白色亮度为 255"""
        assert overlay_text._lum((255, 255, 255)) == 255

    def test_lum_red(self):
        """红色亮度（0.299*255）"""
        assert abs(overlay_text._lum((255, 0, 0)) - 0.299 * 255) < 0.01

    # --- _relative_luminance (WCAG) ---
    def test_relative_luminance_black(self):
        """黑色相对亮度为 0"""
        assert overlay_text._relative_luminance((0, 0, 0)) == 0

    def test_relative_luminance_white(self):
        """白色相对亮度为 1"""
        assert abs(overlay_text._relative_luminance((255, 255, 255)) - 1.0) < 0.01

    # --- _contrast_ratio (WCAG) ---
    def test_contrast_ratio_black_white(self):
        """黑白对比度应为 21:1"""
        cr = overlay_text._contrast_ratio((0, 0, 0), (255, 255, 255))
        assert abs(cr - 21.0) < 0.1, f"黑白对比度应约 21，实际 {cr}"

    def test_contrast_ratio_same_color(self):
        """同色对比度应为 1:1"""
        cr = overlay_text._contrast_ratio((100, 100, 100), (100, 100, 100))
        assert abs(cr - 1.0) < 0.01, f"同色对比度应约 1，实际 {cr}"

    def test_contrast_ratio_high_contrast(self):
        """高对比度对（深字浅底）应 >= 4.5"""
        cr = overlay_text._contrast_ratio((20, 18, 16), (250, 247, 240))
        assert cr >= 4.5, f"深字浅底对比度应 >= 4.5，实际 {cr}"

    # --- has_cjk ---
    def test_has_cjk_chinese(self):
        """中文字符应返回 True"""
        assert overlay_text.has_cjk("你好世界") is True

    def test_has_cjk_english(self):
        """纯英文应返回 False"""
        assert overlay_text.has_cjk("Hello World") is False

    def test_has_cjk_mixed(self):
        """混合中英文应返回 True"""
        assert overlay_text.has_cjk("Hello 你好") is True

    def test_has_cjk_empty(self):
        """空字符串应返回 False"""
        assert overlay_text.has_cjk("") is False

    # --- effective_spec (字体回退) ---
    def test_effective_spec_no_cjk_keeps_spec(self):
        """无中文时保持原字体规格"""
        assert overlay_text.effective_spec("type", "Hello") == "type"

    def test_effective_spec_cjk_with_western_font_falls_back(self):
        """中文 + 西文字体应回退到 kai"""
        result = overlay_text.effective_spec("type", "你好")
        assert result == "kai", f"中文+type 应回退到 kai，实际 {result}"

    # --- anchor_top_left ---
    def test_anchor_top_left_center(self):
        """center 位置应返回居中坐标"""
        x, y = overlay_text.anchor_top_left(1000, 800, "center", 200, 100, 50)
        assert x == (1000 - 200) // 2
        assert y == (800 - 100) // 2

    def test_anchor_top_left_top_left(self):
        """top-left 位置应返回 margin 坐标"""
        x, y = overlay_text.anchor_top_left(1000, 800, "top-left", 200, 100, 50)
        assert x == 50
        assert y == 50

    def test_anchor_top_left_bottom_right(self):
        """bottom-right 位置应返回右下角坐标"""
        x, y = overlay_text.anchor_top_left(1000, 800, "bottom-right", 200, 100, 50)
        assert x == 1000 - 50 - 200
        assert y == 800 - 50 - 100

    # --- parse_xy ---
    def test_parse_xy_percentage(self):
        """百分比坐标解析"""
        x, y = overlay_text.parse_xy("50%,80%", 1000, 800)
        assert x == 500
        assert y == 640

    def test_parse_xy_corner(self):
        """角落坐标解析"""
        x, y = overlay_text.parse_xy("0%,0%", 1000, 800)
        assert x == 0
        assert y == 0


# ============================================================
# 集成测试：fixtures 中的 brief 能通过完整校验
# ============================================================

class TestFixturesIntegration:
    """fixtures 示例 brief 的集成测试"""

    def _load_fixture(self, name):
        fp = os.path.join(os.path.dirname(__file__), "fixtures", name)
        with open(fp, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    def test_all_valid_fixtures_pass_validation(self):
        """所有 valid_ 开头的 fixture 应通过校验"""
        fixture_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        valid_files = [f for f in os.listdir(fixture_dir)
                       if f.startswith("valid_") and f.endswith(".json")]
        assert len(valid_files) >= 2, "应至少有 2 个 valid fixture"
        for fname in valid_files:
            b = self._load_fixture(fname)
            errors, warns = validate_brief.brief_errors(b)
            assert len(errors) == 0, f"{fname} 不应有 error: {errors}"

    def test_invalid_fixtures_fail_validation(self):
        """所有 invalid_ 开头的 fixture 应校验失败"""
        fixture_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        invalid_files = [f for f in os.listdir(fixture_dir)
                         if f.startswith("invalid_") and f.endswith(".json")]
        assert len(invalid_files) >= 1, "应至少有 1 个 invalid fixture"
        for fname in invalid_files:
            b = self._load_fixture(fname)
            errors, warns = validate_brief.brief_errors(b)
            assert len(errors) > 0, f"{fname} 应有 error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
