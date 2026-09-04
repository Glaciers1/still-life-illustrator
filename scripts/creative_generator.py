#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "2.1.0"
"""
creative_generator.py —— 预制创意库 + 模板自动生成器。

【核心目标】跳过 LLM 补创意环节，将前置流程从 5 步缩到 3 步：
  旧：self_skeleton → LLM补创意(多轮对话) → self_merge → build_from_brief → 生图
  新：self_skeleton(--auto-creative) → build_from_brief → 生图

【两种模式】
  1. 预制库优先：从 references/creative_library.json 查询已生成的高质量创意
  2. 模板兜底：查询不到时用结构化模板自动生成（pv_en/poem/latin/title）

【创意字段】
  - title: 主标题（英文大写）
  - latin: 拉丁学名（英文斜体格式）
  - poem: 短诗（两行，英文）
  - pv_en: {"A": "...", "B": "..."} 画面描述（英文，A/B视角构图不同）

用法:
  # 作为库导入
  from creative_generator import CreativeGenerator
  gen = CreativeGenerator(library_path="references/creative_library.json")
  creative = gen.get_creative("栗子蛋糕", hero_en="chestnut cake", style="S3", ...)

  # 批量生成预制库
  python creative_generator.py --batch-generate --out references/creative_library.json
"""
import json, os, sys, re, random, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.normpath(os.path.join(HERE, ".."))
DEFAULT_LIBRARY = os.path.join(SKILL_ROOT, "references", "creative_library.json")

# ---- 视角与构图模板 ----
ANGLES = {
    "90°正俯视": "straight top-down flat-lay (90-degree) view",
    "45°三分之三高角": "three-quarter high-angle (about 45-degree) view",
    "60°微俯": "slightly high-angle (about 60-degree) view",
    "0°平视": "eye-level frontal view",
    "微仰": "slight low-angle view",
}

COMPOSES = {
    "居中对称": "centered symmetrical composition, generous margins",
    "三分偏心": "rule-of-thirds off-center composition",
    "对角线": "diagonal composition, subject along diagonal axis",
    "80-20极简": "80-20 minimal composition, large negative space on one side",
}

# ---- 容器模板 ----
CONTAINERS = {
    "auto": "a rustic ceramic shallow plate on linen cloth",
    "ceramic": "a white porcelain shallow plate with matte ceramic texture",
    "wood": "a wooden cutting board or large platter on linen",
    "bamboo": "a woven bamboo basket or shallow bamboo tray with visible weave texture",
    "metal": "a stainless steel shallow plate with subtle reflection",
    "glass": "a clear glass bowl or plate with transparent edges",
    "stone": "a marble slab or stone plate with natural veining",
    "fabric": "a linen cloth or coarse fabric spread as surface",
}

# ---- 季节短诗模板 ----
SEASON_POEMS = {
    "早春": [
        ("Awakening from winter's sleep,", "tender greens begin to creep."),
        ("First blooms pierce the frosty air,", "gentle signs of spring are there."),
        ("Soft rain kisses waking earth,", "stirring seeds to gentle birth."),
    ],
    "初夏": [
        ("Golden sun on ripening fruit,", "summer's warmth takes root."),
        ("Lush green leaves and blossoms bright,", "summer days are full of light."),
        ("Warm breeze carries sweet perfume,", "summer's bounty fills the room."),
    ],
    "晚秋": [
        ("Amber leaves begin to fall,", "autumn's warmth enfolds us all."),
        ("Harvest gold and rusty red,", "autumn's tapestry is spread."),
        ("Cool air carries woodsmoke scent,", "autumn's quiet time is spent."),
    ],
    "初冬": [
        ("Frosty mornings, quiet still,", "winter's breath upon the sill."),
        ("Pine and cinnamon fill the air,", "winter's warmth is everywhere."),
        ("Soft snow blankets the sleeping earth,", "winter's quiet, gentle birth."),
    ],
    "全年": [
        ("Through the seasons, still and bright,", "nature's beauty takes its flight."),
        ("Timeless forms in quiet grace,", "nature's art in every place."),
        ("Simple beauty, pure and true,", "nature's gift for me and you."),
    ],
}

# ---- 主体结构描述模板（基于质感关键词）----
TEXTURE_DESCRIPTIONS = {
    "奶油": "smooth creamy texture with soft peaks",
    "酥脆": "crisp flaky layers with golden crust",
    "湿润": "moist dense crumb with tender interior",
    "蓬松": "fluffy airy texture with light crumb",
    "光滑": "smooth glossy surface with subtle sheen",
    "粗糙": "rough matte texture with handmade irregularity",
    "晶莹": "translucent crystal-clear texture with light refraction",
    "软糯": "soft chewy sticky texture with gentle give",
    "干爽": "dry crumbly texture with delicate break",
    "多汁": "juicy succulent flesh with natural moisture",
}


def extract_structure_size_en(structure):
    """从旬物索引中文「结构」字段中提取可安全转译为英文的尺寸信息。

    结构字段为中文（如"心形，径3-5cm"、"杯状花冠，高20-40cm"、"茎长15-25cm，笔直微锥"），
    不能直接拼入英文 pv_en（会造成提示词中文污染）。本函数只提取 径/高/茎长/长 的尺寸
    范围并转译为英文；无法提取时返回空串（其余中文一律不进入提示词）。
    """
    if not structure:
        return ""
    for pat, fmt in (
        (r'径\s*(\d+(?:\.\d+)?)\s*[-~至]?\s*(\d+(?:\.\d+)?)?\s*cm', 'about {a}{b} cm across'),
        (r'高\s*(\d+(?:\.\d+)?)\s*[-~至]?\s*(\d+(?:\.\d+)?)?\s*cm', 'about {a}{b} cm tall'),
        (r'茎长\s*(\d+(?:\.\d+)?)\s*[-~至]?\s*(\d+(?:\.\d+)?)?\s*cm', 'about {a}{b} cm long'),
        (r'长\s*(\d+(?:\.\d+)?)\s*[-~至]?\s*(\d+(?:\.\d+)?)?\s*cm', 'about {a}{b} cm long'),
    ):
        m = re.search(pat, structure)
        if m:
            a, b = m.group(1), m.group(2)
            return fmt.format(a=a, b=f'-{b}' if b else '')
    return ""


class CreativeGenerator:
    """预制创意库 + 模板自动生成器。"""

    def __init__(self, library_path=None, rng=None):
        self.library_path = library_path or DEFAULT_LIBRARY
        self.library = {}
        self.rng = rng or random.Random()
        self._load_library()

    def _load_library(self):
        """加载预制创意库。"""
        if os.path.exists(self.library_path):
            try:
                with open(self.library_path, "r", encoding="utf-8") as f:
                    self.library = json.load(f)
                print(f"[creative_generator] 预制库已加载: {len(self.library)} 条")
            except Exception as e:
                print(f"[creative_generator] 预制库加载失败: {e}，使用模板模式")

    def save_library(self, path=None):
        """保存预制创意库。"""
        path = path or self.library_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.library, f, ensure_ascii=False, indent=2)
        print(f"[creative_generator] 预制库已保存: {path} ({len(self.library)} 条)")

    def get_creative(self, subject_name, hero_en="", style="auto", cast_size=4,
                      container="auto", season="auto", angle_a="", angle_b="",
                      compose_a="", compose_b="", secondary=None, seasonal_info=None,
                      states="whole, natural state", use_library=True):
        """获取创意字段。优先预制库，否则模板生成。

        Returns:
            dict: {title, latin, poem, pv_en: {A, B}}
        """
        # 预制库优先
        if use_library and subject_name in self.library:
            cached = self.library[subject_name]
            # 预制库的 pv_en 可能需要根据视角/构图调整，但基础创意复用
            return self._adapt_cached(cached, angle_a, angle_b, compose_a, compose_b)

        # 模板生成
        return self._generate_template(
            subject_name, hero_en, style, cast_size, container, season,
            angle_a, angle_b, compose_a, compose_b, secondary, seasonal_info, states
        )

    def _adapt_cached(self, cached, angle_a, angle_b, compose_a, compose_b):
        """适配预制库创意：替换视角和构图为当前 brief 的值。"""
        result = dict(cached)
        # latin 必须为大写学名；预制库缺学名或无值时清空（build 跳过 latin 行）
        if result.get("latin"):
            result["latin"] = str(result["latin"]).strip().upper()
        else:
            result["latin"] = ""
        pv = result.get("pv_en", {})
        if isinstance(pv, dict):
            for tag, angle, compose in [("A", angle_a, compose_a), ("B", angle_b, compose_b)]:
                if tag in pv and angle:
                    # 替换视角描述
                    angle_en = ANGLES.get(angle, angle)
                    old_angle = None
                    for k in ANGLES.values():
                        if k in pv[tag]:
                            old_angle = k
                            break
                    if old_angle:
                        pv[tag] = pv[tag].replace(old_angle, angle_en)
                    # 替换构图描述
                    if compose:
                        compose_en = COMPOSES.get(compose, compose)
                        old_compose = None
                        for k in COMPOSES.values():
                            if k in pv[tag]:
                                old_compose = k
                                break
                        if old_compose:
                            pv[tag] = pv[tag].replace(old_compose, compose_en)
            result["pv_en"] = pv
        return result

    def _generate_template(self, subject_name, hero_en, style, cast_size,
                            container, season, angle_a, angle_b, compose_a, compose_b,
                            secondary, seasonal_info, states):
        """模板生成创意字段。"""
        hero_en = hero_en or subject_name.lower()
        # v2.0.1: 中文检测——如果 hero_en 包含中文，用英文替代
        _cjk = lambda s: any('一' <= c <= '鿿' for c in (s or ''))
        if _cjk(hero_en):
            # 从旬物索引的质感/结构中提取英文关键词，或用通用替代
            hero_en = "still life subject"
            if seasonal_info:
                _texture = seasonal_info.get("质感", "") or ""
                if "奶油" in _texture:
                    hero_en = "creamy dessert"
                elif "酥脆" in _texture:
                    hero_en = "crispy pastry"
                elif "湿润" in _texture:
                    hero_en = "moist cake"
                elif "多汁" in _texture:
                    hero_en = "juicy fruit"
                elif "晶莹" in _texture:
                    hero_en = "crystal glassware"
                elif "软糯" in _texture:
                    hero_en = "soft sticky rice"
                elif "干爽" in _texture:
                    hero_en = "dry crumbly bread"
                elif "蓬松" in _texture:
                    hero_en = "fluffy bread"
                elif "光滑" in _texture:
                    hero_en = "smooth ceramic"
                elif "粗糙" in _texture:
                    hero_en = "rough matte ceramic"
            print(f"  [creative_generator] 中文主体 '{subject_name}' -> 英文替代 '{hero_en}'")

        # ---- title ----
        title_words = hero_en.upper().split()
        title = title_words[0] if title_words else hero_en.upper()
        if _cjk(title):
            title = "STILL LIFE"
        if len(title) > 22:
            title = title[:22]

        # ---- latin ----
        # 模板兜底无法保证准确学名：无学名时留空，由 build 跳过 latin 行。
        # 只有预制库命中且确有学名时才填充（见 _adapt_cached 大写化处理）。
        latin = ""

        # ---- poem ----
        season_key = season if season in SEASON_POEMS else "全年"
        poem_templates = SEASON_POEMS[season_key]
        poem = list(self.rng.choice(poem_templates))

        # ---- pv_en ----
        pv_en = {}
        for tag, angle, compose in [("A", angle_a, compose_a), ("B", angle_b, compose_b)]:
            angle_en = ANGLES.get(angle, "eye-level frontal view")
            compose_en = COMPOSES.get(compose, "centered symmetrical composition")

            # 主体结构描述
            structure = self._build_structure(hero_en, seasonal_info, states)

            # 配角描述
            secondary_desc = self._build_secondary(secondary, cast_size)

            # 容器描述
            container_en = CONTAINERS.get(container, CONTAINERS["auto"])

            # 组装 pv_en
            pv_parts = [
                f"{angle_en}, {compose_en}",
                f"ONE single {hero_en} as the hero: {structure}",
                f"held in/on {container_en} that catches the hero with believable contact point",
                secondary_desc,
                "soft contact shadows where parts meet",
                "warm ivory textured paper background with one pale color-wash",
                "soft diffused near-flat light, no hard shadow",
            ]
            pv_en[tag] = ", ".join(p for p in pv_parts if p)

        return {
            "title": title,
            "latin": latin,
            "poem": poem,
            "pv_en": pv_en,
        }

    def _build_structure(self, hero_en, seasonal_info, states):
        """构建主体结构描述。"""
        parts = []

        # 整体形态
        parts.append("natural organic form with gentle irregularity")

        # 质感（从旬物索引提取）
        if seasonal_info:
            texture = seasonal_info.get("质感", "") or ""
            for kw, desc in TEXTURE_DESCRIPTIONS.items():
                if kw in texture:
                    parts.append(desc)
                    break
            if not any(kw in texture for kw in TEXTURE_DESCRIPTIONS):
                parts.append("natural matte texture with subtle surface detail")

            # 结构（旬物索引的"结构"为中文：仅提取尺寸信息转译为英文，其余中文不进入提示词）
            structure = seasonal_info.get("结构", "") or ""
            size_en = extract_structure_size_en(structure)
            if size_en:
                parts.append(size_en)

        # 状态叠加
        if states and "whole" not in states.lower():
            parts.append(f"one whole {hero_en} together with one {states.split('+')[-1].strip() if '+' in states else states} showing inner structure")

        # 自然大小变化
        parts.append("natural size/orientation variation (parts differ 15-30%)")

        return "; ".join(parts)

    def _build_secondary(self, secondary, cast_size):
        """构建配角描述。"""
        if not secondary or cast_size <= 1:
            return ""

        parts = []
        for i, sec in enumerate(secondary):
            name = sec.get("en", sec.get("name", "accent")) if isinstance(sec, dict) else str(sec)
            count = sec.get("count", 1) if isinstance(sec, dict) else 1
            parts.append(f"exactly {count} small {name} as supporting accent, clearly smaller and softer than hero")

        if parts:
            return "; ".join(parts) + ", all clustered tightly around hero within 1-2 body-lengths"
        return ""

    def batch_generate(self, subjects, output_path=None):
        """批量生成创意并保存到预制库。

        Args:
            subjects: list of dict (name, en) or list of str
            output_path: 保存路径
        """
        count = 0
        for sub in subjects:
            if isinstance(sub, dict):
                name = sub.get("name", "")
                en = sub.get("en", name.lower())
            else:
                name = str(sub)
                en = name.lower()

            if not name:
                continue

            # 生成创意（用默认参数，实际使用时会适配视角构图）
            creative = self._generate_template(
                name, en, style="S3", cast_size=4, container="bamboo",
                season="晚秋", angle_a="90°正俯视", angle_b="0°平视",
                compose_a="居中对称", compose_b="对角线",
                secondary=None, seasonal_info=None, states="whole, natural state"
            )
            self.library[name] = creative
            count += 1

        self.save_library(output_path)
        print(f"[creative_generator] 批量生成完成: {count} 条")
        return count


def main():
    ap = argparse.ArgumentParser(description="预制创意库生成器")
    ap.add_argument("--batch-generate", action="store_true",
                    help="从旬物索引批量生成创意库")
    ap.add_argument("--out", default="", help="输出路径（默认 references/creative_library.json）")
    ap.add_argument("--subjects", default="", help="指定主体列表（逗号分隔），不指定则用旬物索引全部")
    ap.add_argument("--show", default="", help="查看指定主体的创意")
    args = ap.parse_args()

    gen = CreativeGenerator()

    if args.show:
        creative = gen.get_creative(args.show, use_library=True)
        print(f"\n=== {args.show} ===")
        print(f"title: {creative.get('title')}")
        print(f"latin: {creative.get('latin')}")
        print(f"poem: {creative.get('poem')}")
        pv = creative.get('pv_en', {})
        for tag, p in pv.items():
            print(f"\npv_en[{tag}] ({len(p.split())} words):")
            print(p)
        return

    if args.batch_generate:
        # 加载旬物索引
        index_json = os.path.join(SKILL_ROOT, "references", "seasonal_produce_index.json")
        subjects = []
        if args.subjects:
            subjects = [{"name": s.strip(), "en": s.strip().lower()}
                        for s in args.subjects.split(",") if s.strip()]
        elif os.path.exists(index_json):
            with open(index_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("items", []):
                name = item.get("name", "").strip()
                if name:
                    subjects.append({"name": name, "en": name.lower()})
        else:
            print("错误：未找到旬物索引，且未指定主体列表")
            sys.exit(1)

        out = args.out or DEFAULT_LIBRARY
        gen.batch_generate(subjects, output_path=out)
        return

    ap.print_help()


if __name__ == "__main__":
    main()
