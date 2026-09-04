#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "2.1.0"
# v2.0: 新增 --auto-creative 参数，集成 CreativeGenerator 自动填充创意字段，跳过 LLM 补创意环节
"""
self_skeleton.py —— self 批量骨架生成器（v2.0 合并 quick_batch 能力后的唯一批量入口）。

把一份"批次选题清单"（或简单主体列表）一次性变成 N 份 brief@1.1 骨架：
固定字段（id/source/style/cast_size/ratio/lang/hero/secondary 结构/palette/views 角度构图/text 字体排法）
全部按规则填好并保证批次内档位/风格/季节/视角均衡；
真正需要创意的字段（views[].pv_en、text.poem、text.latin、text.title）默认留 TBD，
由 LLM 后续用 self_merge.py 合并（selfA 路径）；加 --auto-creative 则跳过 LLM，
由 CreativeGenerator（预制库优先 + 模板兜底）自动填充。

【v2.0 合并】原 quick_batch.py 已并入本脚本，新增：
  --build         骨架+创意+拼装一步完成（直接输出 *_A.txt / *_B.txt / *_overlay.json / batch_summary.json）
  --cast-size     固定档位 auto/large/1-6（默认 auto 按概率均衡；large=Abundant~Lush 4-6 大档位）
  --container     固定容器 auto/ceramic/wood/bamboo/metal/glass/stone/fabric（写入 brief._container_override）
  --skip-validate --build 拼装时跳过 brief 校验

批量规模：--batch-size 2/5/10/15/20/30（默认 10），实际数量以主体列表为准。

用法:
  # 方式一：选题清单 JSON（推荐，可带全局约束和每个主体的英文名）
  python self_skeleton.py --spec batch_spec.json --outdir ./batch20

  # 方式二：简单文本，每行一个主体中文名
  python self_skeleton.py --subjects subjects.txt --batch-size 20 --outdir ./batch20

  # 方式三：命令行直接列主体
  python self_skeleton.py --names "巴斯克芝士蛋糕,马卡龙,可露丽" --outdir ./batch20

  # 方式四（v2.0 一步出提示词，等价原 quick_batch）：骨架+自动创意+拼装
  python self_skeleton.py --names "栗子蛋糕" --auto-creative --build --cast-size 3 --container bamboo --outdir ./batch

输出:
  不加 --build：<outdir>/B001_brief.json … B0NN_brief.json（骨架，创意按 --auto-creative 决定）
               <outdir>/creative_template.json（LLM 补创意模板）
  加 --build：额外产出 <outdir>/B001_A.txt、B001_B.txt、B001_overlay.json … 与 batch_summary.json
  终端打印紧凑摘要表
"""
import json, os, sys, argparse, random, re, glob, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from creative_generator import CreativeGenerator
except Exception:
    CreativeGenerator = None
try:
    from build_from_brief import build_one, brief_errors
except Exception as e:
    print(f"[warn] 导入 build_from_brief 失败: {e}，--build 不可用", file=sys.stderr)
    build_one = None
    brief_errors = None

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.normpath(os.path.join(HERE, ".."))
SEASONAL_INDEX = os.path.join(SKILL_ROOT, "references", "seasonal-produce-index.md")
SEASONAL_INDEX_JSON = os.path.join(SKILL_ROOT, "references", "seasonal_produce_index.json")

# ---- 常量池 ----
CAST_SIZES = [1, 2, 3, 4, 5, 6]
CAST_PROBS = [0.12, 0.18, 0.28, 0.22, 0.12, 0.08]  # Solo/Duo/Standard/Abundant/Bountiful/Lush
CAST_NAMES = {1: "Solo", 2: "Duo", 3: "Standard", 4: "Abundant", 5: "Bountiful", 6: "Lush"}

STYLES = ["S1", "S2", "S3"]
SEASONS = ["早春", "初夏", "晚秋", "初冬"]  # 四季节代表词，可被全局覆盖
SEASON_EN = {"早春": "EARLY SPRING", "初夏": "EARLY SUMMER", "晚秋": "LATE AUTUMN", "初冬": "EARLY WINTER"}

# 视角池（中文描述 + 英文 pv 用角度词）
ANGLES = [
    ("90°正俯视", "straight top-down flat-lay (90-degree) view"),
    ("45°三分之三高角", "three-quarter high-angle (about 45-degree) view"),
    ("60°微俯", "slightly high-angle (about 60-degree) view"),
    ("0°平视", "eye-level frontal view"),
    ("微仰", "slight low-angle view"),
]
# A/B 视角对（保证明显不同）
ANGLE_PAIRS = [(0, 3), (0, 1), (1, 3), (2, 3), (0, 4), (1, 4), (2, 1)]

COMPOSES = [
    ("居中对称", "centered symmetrical composition, generous margins"),
    ("三分偏心", "rule-of-thirds off-center composition, subject placed at intersection"),
    ("对角线", "diagonal composition, subject along diagonal axis"),
    ("80-20极简", "80-20 minimal composition, large negative space on one side"),
]

TITLE_STYLES = ["normal", "italic", "wave", "arch", "scatter"]
TITLE_FONTS = ["serif", "sans", "kai", "hand"]

# 状态叠加类型（可切割主体随机选用；whole=单一自然状态；共8种）
STATE_OVERLAYS = [
    ("whole", "whole, natural state"),
    ("halved", "whole + halved cross-section"),
    ("sliced", "whole + sliced"),
    ("cubed", "whole + cut into large pieces"),
    ("diced", "whole + diced into small cubes"),
    ("julienned", "whole + julienned into thin strips"),
    ("peeled", "whole + peeled"),
    ("shelled", "whole + shelled"),
]
# 可切割主体关键词（旬物索引入画字段包含这些词则可切割）
CUTTABLE_KEYWORDS = ("切", "剖", "片", "块", "整颗", "半", "剥皮", "切丁", "切块", "烘焙", "面包", "甜点", "蛋糕", "派", "挞", "布丁", "果冻", "沙拉", "寿司", "刺身", "烤肉", "牛排", "鱼", "虾", "蟹", "贝", "果", "蔬", "菜", "瓜", "茄", "椒", "薯", "芋", "藕", "笋", "菇", "菌", "酪", "奶", "肉", "蛋", "饭", "面", "饼", "糕", "酥", "卷", "包", "馒", "饺", "烧", "烤", "炸", "煎", "蒸", "煮", "炖", "腌", "渍", "泡", "醉", "糟", "熏", "腊", "风", "干", "鲜", "活", "生", "熟")
SUB_BLANKS = ["左上", "右上", "左下", "右下"]
SUB_BLANK_DIAGONAL = {"左上": "右下", "右上": "左下", "左下": "右上", "右下": "左上"}

# 按风格推荐主标题字体（英文模式）
STYLE_FONT_EN = {"S1": "hand", "S2": "serif", "S3": "sans"}
# 按风格推荐主标题字体（中文模式）
STYLE_FONT_ZH = {"S1": "kai", "S2": "hand", "S3": "serif"}

# 默认调色板（暖米白系，甜点/美食通用）
DEFAULT_PALETTE = {
    "overall": "warm ivory base, overall middle-low saturation, calm and quiet",
    "accent": "hero natural color as vivid accent about 10-15%",
    "bg": "#F3EDE2",
}

# 甜点/美食类默认 props 模板（按 cast_size 给容器建议）
PROPS_BY_CAST = {
    1: "a shallow ceramic plate on a linen cloth, generous negative space",
    2: "a ceramic plate with a linen napkin, one small accent resting beside",
    3: "a ceramic or wooden plate on linen cloth, small accents grouped around hero",
    4: "a wooden board or large platter on linen, multiple accents clustered within 1-2 body-lengths",
    5: "a rustic wooden table with linen cloth, bountiful spread of accents all toward hero",
    6: "a generous table spread with linen, lush arrangement of multiple accent groups toward hero",
}

# 配角建议池（按季节，骨架里随机抽取结构化建议，具体由 LLM 在 pv_en 里写）
# 搭配非强制：从季节池中随机选择，优先考虑色彩和谐与画面美感，不固定搭配
SECONDARY_SUGGESTIONS = {
    "早春": ["fresh mint sprig", "edible flower", "green tea leaf", "cherry blossom petal",
             "fresh pea pod", "asparagus tip", "radish slice", "tulip petal",
             "chive sprig", "lemon zest"],
    "初夏": ["fresh berry", "mint leaf", "citrus zest", "edible flower",
             "cherry tomato", "basil leaf", "cucumber slice", "peach slice",
             "lavender sprig", "melon cube"],
    "晚秋": ["dried chrysanthemum", "cinnamon stick", "chestnut", "maple leaf",
             "persimmon slice", "walnut", "dried fig", "sage leaf",
             "quince slice", "pine cone"],
    "初冬": ["pine sprig", "dried orange slice", "cinnamon stick", "star anise",
             "cranberry", "rosemary sprig", "dried apple ring", "clove",
             "walnut", "silver fir sprig"],
}
# 配角代表色映射（用于色彩和谐度评分，#HEX 格式）
SECONDARY_COLORS = {
    # 早春
    "fresh mint sprig": "#98D8AA", "edible flower": "#F4A7B9",
    "green tea leaf": "#88B04B", "cherry blossom petal": "#FFB7C5",
    "fresh pea pod": "#7CB342", "asparagus tip": "#7CB342",
    "radish slice": "#E57373", "tulip petal": "#E91E63",
    "chive sprig": "#8BC34A", "lemon zest": "#FFD54F",
    # 初夏
    "fresh berry": "#E53935", "mint leaf": "#81C784",
    "citrus zest": "#FFB74D", "cherry tomato": "#E53935",
    "basil leaf": "#66BB6A", "cucumber slice": "#AED581",
    "peach slice": "#FFAB91", "lavender sprig": "#9575CD",
    "melon cube": "#F48FB1",
    # 晚秋
    "dried chrysanthemum": "#FFCC80", "cinnamon stick": "#A1887F",
    "chestnut": "#8D6E63", "maple leaf": "#E57373",
    "persimmon slice": "#FF8A65", "walnut": "#6D4C41",
    "dried fig": "#8D6E63", "sage leaf": "#9CCC65",
    "quince slice": "#FFCC80", "pine cone": "#5D4037",
    # 初冬
    "pine sprig": "#2E7D32", "dried orange slice": "#FF8A65",
    "star anise": "#8D6E63", "cranberry": "#C62828",
    "rosemary sprig": "#558B2F", "dried apple ring": "#FFAB91",
    "clove": "#5D4037", "silver fir sprig": "#1B5E20",
}


def hex_to_hsl(hex_color):
    """#RRGGBB -> (hue 0-360, saturation 0-1, lightness 0-1)"""
    try:
        r = int(hex_color[1:3], 16) / 255.0
        g = int(hex_color[3:5], 16) / 255.0
        b = int(hex_color[5:7], 16) / 255.0
    except Exception:
        return (0, 0, 0.5)
    max_c, min_c = max(r, g, b), min(r, g, b)
    l = (max_c + min_c) / 2
    if max_c == min_c:
        return (0, 0, l)
    d = max_c - min_c
    s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
    if max_c == r:
        h = (g - b) / d + (6 if g < b else 0)
    elif max_c == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return (h * 60, s, l)


def hue_distance(h1, h2):
    """两个色相的环距离（0-180度）"""
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def color_harmony_score(hex1, hex2):
    """色彩和谐度评分（0-100）。
    色相距离 <30°: 同色冲突(20)；30-90°: 邻近色和谐(70)；
    90-150°: 中距离可接受(55)；150-180°: 互补色最和谐(90)。"""
    h1, _, _ = hex_to_hsl(hex1)
    h2, _, _ = hex_to_hsl(hex2)
    d = hue_distance(h1, h2)
    if d < 30:
        return 20
    elif d < 90:
        return 70
    elif d < 150:
        return 55
    else:
        return 90




# ---- 旬物索引轻量查询（JSON 优先，MD 回退）----
_seasonal_json_cache = None


def _load_seasonal_json():
    """读旬物索引 JSON 数据库，返回 dict；失败返回 None。带缓存。"""
    global _seasonal_json_cache
    if _seasonal_json_cache is not None:
        return _seasonal_json_cache
    try:
        if os.path.exists(SEASONAL_INDEX_JSON):
            with open(SEASONAL_INDEX_JSON, "r", encoding="utf-8") as f:
                _seasonal_json_cache = json.load(f)
            return _seasonal_json_cache
    except Exception:
        pass
    return None


def _load_seasonal_index():
    """读旬物索引全文，返回文本；优先 JSON（转为文本摘要），失败回退 MD。
    注意：JSON 模式下返回的是 JSON 字符串，extract_all_subjects 会优先用 JSON 解析。"""
    js = _load_seasonal_json()
    if js:
        return json.dumps(js, ensure_ascii=False)
    try:
        with open(SEASONAL_INDEX, "r", encoding="utf-8-sig") as f:
            return f.read()
    except Exception:
        return None


def extract_all_subjects(index_text=None):
    """从旬物索引解析全部条目名称，返回 list[str]（去重）。
    优先从 JSON 数据库提取（O(1) 查询），JSON 不存在时回退 MD 目录解析。"""
    # 优先 JSON
    js = _load_seasonal_json()
    if js and "items" in js:
        names = []
        for item in js["items"]:
            name = item.get("name", "").strip()
            if name and name not in names:
                names.append(name)
        return names
    # 回退 MD
    if index_text is None:
        index_text = _load_seasonal_index()
    if not index_text:
        return []
    names = []
    dir_match = re.search(r'##\s*目录(.+?)(?=\n##|\Z)', index_text, re.S)
    if dir_match:
        dir_text = dir_match.group(1)
    else:
        dir_text = index_text
    # 目录行统一取『（数字）**：名单 / （数字）：名单』冒号后部分：
    # 兼容四季顶格加粗行 `- **春（37）**：…` 与全年区缩进子组行 `  - 器物用具（62）：…`；
    # 全年父行 `- **全年 · 常备（198）**：` 冒号后为空、不产出名字（JSON 缺失走此 MD 回退时不丢全年区）
    for m in re.finditer(r'[）)]\s*\**[：:](.+)', dir_text):
        line = m.group(1)
        for raw in re.split(r'[、，]', line):
            name = raw.strip()
            name = re.sub(r'[（(].*?[）)]', '', name).strip()
            if (name and 1 <= len(name) <= 15
                    and '**' not in name and '#' not in name
                    and not re.match(r'^[\d\s]+$', name)
                    and name not in names):
                names.append(name)
    return names


def extract_subjects_by_season(season_tag):
    """按题材分区标签（春/夏/秋/冬/全年）返回该分区条目名列表（去重、保持库内顺序）。
    仅 JSON 主路径支持（item.season 字段，五区：春37/夏69/秋42/冬28/全年198）；
    JSON 缺失时返回 None，由调用方降级为全库随机。"""
    js = _load_seasonal_json()
    if not js or "items" not in js:
        return None
    tag = str(season_tag).strip()
    out = []
    for item in js["items"]:
        if str(item.get("season", "")).strip() == tag:
            name = item.get("name", "").strip()
            if name and name not in out:
                out.append(name)
    return out


def auto_select_subjects(n, index_text=None, avoid=None, rng=None, season_filter=None):
    """从旬物索引全部条目中自动随机选 n 个不重复主体，返回 list[dict]（name/en）。
    - avoid: 要排除的主体名称列表（历史去重）
    - rng: random.Random 实例
    - season_filter: 可选题材分区（春/夏/秋/冬/全年），指定后只从该分区抽
      （分区第五类「全年·常备」用）；JSON 缺失无法分区时自动降级全库随机。"""
    import random as _r
    rng = rng or _r
    if season_filter:
        scoped = extract_subjects_by_season(season_filter)
        all_names = scoped if scoped else extract_all_subjects(index_text)
    else:
        all_names = extract_all_subjects(index_text)
    if not all_names:
        return []
    avoid_set = set(avoid or [])
    pool = [name for name in all_names if name not in avoid_set]
    if len(pool) < n:
        pool = all_names  # 不够时放宽限制
    chosen = rng.sample(pool, min(n, len(pool)))
    return [{"name": name, "en": name.lower()} for name in chosen]


def query_seasonal(name, index_text=None):
    """从旬物索引查主体，返回 dict（固有色/应季/搭配/cuttable_states/colors），查不到返回 None。
    优先从 JSON 数据库查询（O(1)），JSON 不存在时回退 MD 正则解析。"""
    if not name:
        return None
    # 优先 JSON
    js = _load_seasonal_json()
    if js and "items" in js:
        for item in js["items"]:
            if item.get("name", "").strip() == name.strip():
                result = {
                    "固有色": item.get("固有色", ""),
                    "season": item.get("成熟", ""),
                    "pairing": item.get("搭配", ""),
                    "category": item.get("category", ""),
                    "season_tag": item.get("season", ""),
                    "质感": item.get("质感", ""),
                    "结构": item.get("结构", ""),
                    "入画": item.get("入画", ""),
                    "cuttable": item.get("cuttable", False),
                    "cuttable_states": item.get("cuttable_states", ["whole"]),
                }
                # 从固有色中提取 #HEX 颜色
                hexes = re.findall(r'#[0-9a-fA-F]{6}', item.get("固有色", ""))
                if hexes:
                    result["colors"] = hexes[:3]
                return result
        return None
    # 回退 MD
    if index_text is None:
        index_text = _load_seasonal_index()
    if not index_text:
        return None
    sections = re.split(r'\n#{2,4}\s+', index_text)
    for sec in sections:
        if name in sec[:200]:
            result = {}
            hexes = re.findall(r'#[0-9a-fA-F]{6}', sec)
            if hexes:
                result["colors"] = hexes[:3]
            m = re.search(r'成熟[：:]\s*([^\n]+)', sec)
            if m:
                result["season"] = m.group(1).strip()
            m = re.search(r'搭配[：:]\s*([^\n]+)', sec)
            if m:
                result["pairing"] = m.group(1).strip()
            m = re.search(r'固有色[：:]\s*([^\n]+)', sec)
            if m:
                result["固有色"] = m.group(1).strip()
            if result:
                return result
    return None


# ---- 均衡抽样 ----


def balanced_assign(n, pool, probs=None, rng=None):
    """把 pool 里的元素均衡分配给 n 个位置，返回长度 n 的列表。
    若给 probs 则按概率加权，否则均匀。保证每个元素至少出现一次（n>=len(pool)时）。"""
    rng = rng or random
    if probs:
        # 按比例生成目标数量
        counts = [max(1, round(n * p)) for p in probs]
        # 调整总数到 n
        diff = n - sum(counts)
        i = 0
        while diff != 0:
            if diff > 0:
                counts[i % len(counts)] += 1
                diff -= 1
            else:
                idx = i % len(counts)
                if counts[idx] >= 1:
                    counts[idx] -= 1
                    diff += 1
            i += 1
        result = []
        for item, c in zip(pool, counts):
            result.extend([item] * c)
    else:
        base = pool * (n // len(pool))
        base.extend(rng.sample(pool, n % len(pool)))
        result = base
    rng.shuffle(result)
    # 保证相邻不重复（简单交换）
    for i in range(1, len(result)):
        if result[i] == result[i - 1]:
            for j in range(len(result)):
                if j != i and j != i - 1 and result[j] != result[i - 1] and (j == 0 or result[j - 1] != result[i]):
                    result[i], result[j] = result[j], result[i]
                    break
    return result


def assign_angle_pairs(n, rng=None):
    """给 n 个 brief 分配 A/B 视角对，保证批次内视角对多样化。"""
    rng = rng or random
    pairs = []
    for i in range(n):
        idx = i % len(ANGLE_PAIRS)
        pairs.append(ANGLE_PAIRS[idx])
    rng.shuffle(pairs)
    return pairs


def assign_composes(n, rng=None):
    """给 n 个 brief 分配 A/B 构图，保证两稿不同且批次内多样化。"""
    rng = rng or random
    result = []
    for i in range(n):
        a = i % len(COMPOSES)
        b = (i + 1 + rng.randint(0, 2)) % len(COMPOSES)
        if b == a:
            b = (a + 1) % len(COMPOSES)
        result.append((a, b))
    rng.shuffle(result)
    return result


# ---- 骨架生成 ----


def make_secondary(cast_size, season, rng=None, hero_color=None, hero_name=None, hero_en=None):
    """根据 cast_size 生成 secondary 数组结构（name/en/count/place/note 留建议，具体由 pv_en 写）。
    cast_size=1 → secondary=[]；cast_size=N → N-1 条。
    hero_color: 主体固有色 #HEX，提供时配角抽样自动做色彩和谐度过滤（同色冲突<30°重新抽样）。
    hero_name/hero_en: 主体中英文名，提供时配角自动排除与主体同类的选项（主体≠次要元素）。"""
    rng = rng or random
    n = cast_size - 1
    if n <= 0:
        return []
    pool = SECONDARY_SUGGESTIONS.get(season, SECONDARY_SUGGESTIONS["初夏"])
    # 主体≠次要元素：排除与主体中英文名相关的配角选项
    if hero_name or hero_en:
        hero_keywords = set()
        if hero_name:
            hero_keywords.add(hero_name.lower())
        if hero_en:
            for w in hero_en.lower().split():
                if len(w) > 2:
                    hero_keywords.add(w)
        filtered = []
        for item in pool:
            item_low = item.lower()
            if any(kw in item_low for kw in hero_keywords):
                continue
            filtered.append(item)
        if filtered:
            pool = filtered
    chosen = []
    # 色彩和谐度过滤：有主体色时，同色冲突(<30°)的配角重新抽样（最多20次）
    if hero_color:
        attempts = 0
        while len(chosen) < n and attempts < 20:
            candidate = rng.choice(pool)
            if candidate in chosen:
                attempts += 1
                continue
            cand_color = SECONDARY_COLORS.get(candidate)
            if cand_color and color_harmony_score(hero_color, cand_color) < 40:
                attempts += 1  # 同色冲突，跳过
                continue
            chosen.append(candidate)
            attempts += 1
    # 无主体色或重试次数用完，随机补全
    if not chosen:
        chosen = rng.sample(pool, min(n, len(pool)))
    while len(chosen) < n:
        c = rng.choice(pool)
        if c not in chosen:
            chosen.append(c)
    result = []
    positions = ["左前", "右后", "正前", "左后", "右前"]
    for i, item in enumerate(chosen):
        cnt = rng.choice([1, 2, 2, 3]) if i > 0 else rng.choice([1, 2, 3])
        result.append({
            "name": item,
            "en": item,
            "count": cnt,
            "place": f"{positions[i % len(positions)]}，放在承载面上、距主体1-2身位内、带接触影",
            "note": f"比主体更小更柔，第{i+1}层后退",
        })
    return result


def _pick_state_overlay(seasonal_info, rng):
    """根据旬物索引的 cuttable_states 字段判断主体可用状态，随机选择。

    优先级：
    1. 旬物索引 cuttable_states 字段（权威）
    2. 回退到旧逻辑（入画字段关键词匹配）

    状态类型：whole/halved/sliced/cubed/diced/julienned/peeled/shelled（共8种）
    - 只有 whole：固定不叠加
    - 多个状态：whole 概率 45%，其余状态均分 55%
    """
    rng = rng or random

    # 1. 优先读取 cuttable_states 字段（旬物索引权威）
    cuttable_states = None
    if seasonal_info:
        cuttable_states = seasonal_info.get("cuttable_states")

    if cuttable_states and isinstance(cuttable_states, list) and len(cuttable_states) > 0:
        # 只有 whole：固定不叠加
        if len(cuttable_states) == 1 and cuttable_states[0] == "whole":
            return "whole, natural state"

        # 多个状态：whole 概率 45%，其余状态均分 55%
        non_whole = [s for s in cuttable_states if s != "whole"]
        if rng.random() < 0.45 or not non_whole:
            return "whole, natural state"

        # 从非 whole 状态中随机选
        state_key = rng.choice(non_whole)
        state_map = {
            "halved": "whole + halved cross-section",
            "sliced": "whole + sliced",
            "cubed": "whole + cut into pieces",
            "peeled": "whole + peeled",
        }
        return state_map.get(state_key, "whole, natural state")

    # 2. 回退到旧逻辑（入画字段关键词匹配，兼容无 cuttable_states 的旧数据）
    cuttable = False
    if seasonal_info:
        ruhua = seasonal_info.get("入画", "") or ""
        cuttable = any(kw in ruhua for kw in CUTTABLE_KEYWORDS)
    if not cuttable:
        return "whole, natural state"
    if rng.random() < 0.45:
        return "whole, natural state"
    cut_states = [s for s in STATE_OVERLAYS if s[0] != "whole"]
    return rng.choice(cut_states)[1]


def make_skeleton(idx, subject, style, cast_size, season, angle_pair, compose_pair,
                   lang, ratio, id_prefix, title_style, rng=None, seasonal_info=None,
                   auto_creative=False, creative_gen=None):
    """生成单份 brief 骨架 dict。"""
    rng = rng or random
    pid = f"{id_prefix}{idx:03d}"
    name = subject.get("name", "") if isinstance(subject, dict) else str(subject)
    en = subject.get("en", name.lower()) if isinstance(subject, dict) else str(subject).lower()

    # 字体
    font_pool = STYLE_FONT_EN if lang == "en" else STYLE_FONT_ZH
    title_font = font_pool.get(style, "serif")
    # 偶尔换字体增加多样性
    if rng.random() < 0.3:
        title_font = rng.choice([f for f in TITLE_FONTS if f != title_font])

    # 次文方位 A/B 对角
    sub_a = rng.choice(SUB_BLANKS)
    sub_b = SUB_BLANK_DIAGONAL[sub_a]

    # 调色板（旬物索引查到就用，否则默认）
    palette = dict(DEFAULT_PALETTE)
    hero_color = None
    if seasonal_info and seasonal_info.get("colors"):
        hero_color = seasonal_info["colors"][0]
        palette["accent"] = f"hero natural color {seasonal_info['colors'][0]} as vivid accent about 10-15%"
    if seasonal_info and seasonal_info.get("固有色"):
        palette["overall"] = f"{seasonal_info['固有色']} family, overall middle-low saturation, warm ivory base"

    # 标题（优先使用一个单词的英文，LLM 可改；超长截断到22字符）
    title_words = en.upper().split()
    auto_title = title_words[0] if title_words else en.upper()
    if len(auto_title) > 22:
        auto_title = auto_title[:22]

    # 季节行
    season_line = SEASON_EN.get(season, season.upper()) if lang == "en" else season

    a_angle_cn, a_angle_en = ANGLES[angle_pair[0]]
    b_angle_cn, b_angle_en = ANGLES[angle_pair[1]]
    a_compose_cn, a_compose_en = COMPOSES[compose_pair[0]]
    b_compose_cn, b_compose_en = COMPOSES[compose_pair[1]]

    brief = {
        "schema": "brief@1.1",
        "id": pid,
        "source": "self",
        "season": season,
        "style": style,
        "style_reason": f"auto-assigned for batch balance ({style})",
        "cast_size": cast_size,
        "ratio": ratio,
        "lang": lang,
        "hero": {
            "name": name,
            "en": en,
            "count": 1,
            "states": _pick_state_overlay(seasonal_info, rng),
        },
        "secondary": make_secondary(cast_size, season, rng, hero_color=hero_color,
                                      hero_name=name, hero_en=en),
        "props": PROPS_BY_CAST.get(cast_size, PROPS_BY_CAST[3]),
        "palette": palette,
        "views": [
            {
                "tag": "A",
                "angle": a_angle_cn,
                "compose": a_compose_cn,
                "title_blank": "上方居中",
                "sub_blank": sub_a,
                "pv_en": "TBD",
            },
            {
                "tag": "B",
                "angle": b_angle_cn,
                "compose": b_compose_cn,
                "title_blank": "上方居中",
                "sub_blank": sub_b,
                "pv_en": "TBD",
            },
        ],
        "text": {
            "title": auto_title,
            "title_font": title_font,
            "title_style": title_style,
            "title_width": 0.30,
            "title_color": "",
            "poem": ["TBD", "TBD"],
            "season_line": season_line,
            "latin": "TBD",
            "sub_ratio": 0.25,
            "sub_color": "",
        },
        # 骨架元信息（不参与校验，供 merge 和调试用；validate 会忽略未知字段）
        "_skeleton": {
            "angle_en": {"A": a_angle_en, "B": b_angle_en},
            "compose_en": {"A": a_compose_en, "B": b_compose_en},
            "seasonal_info": seasonal_info,
        },
    }
    # v2.0: 自动填充创意字段（跳过 LLM 补创意）
    if auto_creative and creative_gen is not None:
        hero_en_val = brief["hero"].get("en", "")
        secondary_val = brief.get("secondary", [])
        states_val = brief["hero"].get("states", "whole, natural state")
        creative = creative_gen.get_creative(
            name,
            hero_en=hero_en_val,
            style=style,
            cast_size=cast_size,
            container="auto",
            season=season,
            angle_a=a_angle_cn,
            angle_b=b_angle_cn,
            compose_a=a_compose_cn,
            compose_b=b_compose_cn,
            secondary=secondary_val,
            seasonal_info=seasonal_info,
            states=states_val,
        )
        # 填充 pv_en
        if isinstance(creative.get("pv_en"), dict):
            brief["views"][0]["pv_en"] = creative["pv_en"].get("A", "")
            brief["views"][1]["pv_en"] = creative["pv_en"].get("B", "")
        # 填充文字
        if creative.get("title"):
            brief["text"]["title"] = creative["title"]
        # latin：必须为大写学名；无学名（空）则置空，build 会跳过 latin 行
        _latin = (creative.get("latin") or "").strip()
        brief["text"]["latin"] = _latin.upper() if _latin else ""
        if creative.get("poem") and isinstance(creative["poem"], list):
            brief["text"]["poem"] = creative["poem"]

    return brief


def make_creative_template(skeletons):
    """生成 LLM 补创意字段的紧凑模板。"""
    return [
        {
            "id": s["id"],
            "title": s["text"]["title"],
            "pv_en": {"A": "", "B": ""},
            "poem": ["", ""],
            "latin": "",
        }
        for s in skeletons
    ]


# ---- 主流程 ----


def load_subjects(args):
    """从各种输入加载主体列表，返回 list[dict]。"""
    subjects = []
    if args.spec:
        with open(args.spec, "r", encoding="utf-8-sig") as f:
            spec = json.load(f)
        subs = spec.get("subjects", [])
        for s in subs:
            if isinstance(s, str):
                subjects.append({"name": s, "en": s.lower()})
            else:
                subjects.append(s)
        # 全局约束覆盖
        g = spec.get("global", {})
        if g.get("lang"):
            args.lang = g["lang"]
        if g.get("ratio"):
            args.ratio = g["ratio"]
        if g.get("style") and g["style"] != "auto":
            args.style = g["style"]
        if g.get("season") and g["season"] != "auto":
            args.season = g["season"]
        if spec.get("batch_size"):
            args.batch_size = spec["batch_size"]
    elif args.subjects:
        with open(args.subjects, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "," in line:
                        parts = [p.strip() for p in line.split(",", 1)]
                        subjects.append({"name": parts[0], "en": parts[1] if len(parts) > 1 else parts[0].lower()})
                    else:
                        subjects.append({"name": line, "en": line.lower()})
    elif args.names:
        for n in args.names.split(","):
            n = n.strip()
            if n:
                subjects.append({"name": n, "en": n.lower()})
    # 无主体输入时：自动从旬物索引 374 条目中随机选择
    if not subjects and getattr(args, "auto_subjects", False):
        index_text = _load_seasonal_index()
        avoid = getattr(args, "avoid_subjects", "") or ""
        avoid_list = [s.strip() for s in avoid.split(",") if s.strip()] if avoid else []
        n = getattr(args, "batch_size", 10)
        subjects = auto_select_subjects(n, index_text, avoid=avoid_list)
        if subjects:
            print(f"[自动选题] 从旬物索引 {len(extract_all_subjects(index_text))} 个条目中随机选择 {len(subjects)} 个主体")
    return subjects


def main():
    ap = argparse.ArgumentParser(description="self 批量骨架生成器")
    ap.add_argument("--spec", help="批次选题清单 JSON")
    ap.add_argument("--subjects", help="主体列表文本文件（每行一个，可含英文名逗号分隔）")
    ap.add_argument("--names", help="命令行直接列主体，逗号分隔")
    ap.add_argument("--batch-size", type=int, default=10, choices=[2, 5, 10, 15, 20, 30],
                    help="批量规模 2/5/10/15/20/30（默认 10），实际数量以主体列表为准")
    ap.add_argument("--outdir", required=True, help="输出目录")
    ap.add_argument("--id-prefix", default="B", help="id 前缀（默认 B）")
    ap.add_argument("--lang", default="en", choices=["zh", "en"], help="语言（默认 en）")
    ap.add_argument("--ratio", default="3:4", help="比例（默认 3:4）")
    ap.add_argument("--style", default="auto", help="固定风格 S1/S2/S3，或 auto 批次均衡")
    ap.add_argument("--season", default="auto", help="固定季节，或 auto 批次均衡")
    ap.add_argument("--seed", type=int, default=None, help="随机种子（可复现）")
    ap.add_argument("--no-seasonal-index", action="store_true", help="不查旬物索引")
    ap.add_argument("--auto-subjects", action="store_true",
                    help="无主体输入时自动从旬物索引 374 个条目中随机选择主体")
    ap.add_argument("--avoid-subjects", default="",
                    help="逗号分隔的已用主体列表（历史去重），自动选题时排除")
    ap.add_argument("--history", default="",
                    help="历史已用主体 JSON 文件路径（数组格式），生成时标注重复警告，自动选题时排除")
    ap.add_argument("--auto-creative", action="store_true",
                    help="v2.0: 自动填充创意字段（pv_en/poem/latin/title），跳过 LLM 补创意环节，使用 CreativeGenerator 模板生成或预制库查询")
    ap.add_argument("--creative-library", default="",
                    help="v2.0: 预制创意库路径（默认 references/creative_library.json）")
    ap.add_argument("--title-style", default="auto",
                    choices=["auto", "normal", "italic", "wave", "arch", "scatter"],
                    help="标题排法：auto=批次随机均衡（默认），或固定 normal/italic/wave/arch/scatter 全批统一")
    ap.add_argument("--cast-size", default="auto",
                    help="固定档位：auto/large/1-6（默认auto均衡；large=Abundant~Lush 4-6 大档位）")
    ap.add_argument("--container", default="auto",
                    help="固定容器：auto/ceramic/wood/bamboo/metal/glass/stone/fabric（默认auto；写入 brief._container_override）")
    ap.add_argument("--skip-validate", action="store_true", help="--build 拼装时跳过 brief 校验")
    ap.add_argument("--build", action="store_true",
                    help="v2.0：一步拼装出 A/B 提示词与 overlay（原 quick_batch 行为），配合 --auto-creative 直接可生图")
    args = ap.parse_args()

    rng = random.Random(args.seed) if args.seed is not None else random.Random()

    subjects = load_subjects(args)
    if not subjects:
        print("错误：未加载到任何主体。请用 --spec / --subjects / --names 提供。")
        sys.exit(1)

    # 读取历史已用主体，标注重复警告，并合并到 avoid 列表
    history_subjects = []
    if args.history and os.path.exists(args.history):
        try:
            with open(args.history, "r", encoding="utf-8-sig") as f:
                hist = json.load(f)
                if isinstance(hist, list):
                    history_subjects = [str(h) for h in hist]
        except Exception:
            pass
    # 合并 --avoid-subjects 和 --history
    avoid_list = [s.strip() for s in args.avoid_subjects.split(",") if s.strip()]
    avoid_list.extend(history_subjects)
    if history_subjects:
        dup = [s.get("name", "") for s in subjects if s.get("name", "") in history_subjects]
        if dup:
            print(f"[历史重复警告] 以下主体在历史已用列表中（{len(history_subjects)} 条）: {', '.join(dup)}")
            print("  建议替换为旬物索引中的其他主体，或确认后继续。")

    n = len(subjects)
    if n != args.batch_size:
        print(f"[提示] 主体数量 {n} 与 --batch-size {args.batch_size} 不一致，以实际主体数量 {n} 为准。")

    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    # 加载旬物索引
    index_text = None if args.no_seasonal_index else _load_seasonal_index()

    # 均衡分配（--cast-size 支持 auto/large/1-6，原 quick_batch 行为）
    if args.cast_size == "auto":
        cast_sizes = balanced_assign(n, CAST_SIZES, CAST_PROBS, rng)
    elif args.cast_size == "large":
        cast_sizes = balanced_assign(n, [4, 5, 6], [0.5, 0.3, 0.2], rng)
    else:
        try:
            cs = int(args.cast_size)
            if 1 <= cs <= 6:
                cast_sizes = [cs] * n
            else:
                raise ValueError
        except ValueError:
            print(f"[warn] 无法解析 --cast-size={args.cast_size}（需 1-6/large/auto），回退 auto 均衡")
            cast_sizes = balanced_assign(n, CAST_SIZES, CAST_PROBS, rng)
    if args.style != "auto":
        styles = [args.style] * n
    else:
        styles = balanced_assign(n, STYLES, None, rng)
    if args.season != "auto":
        seasons = [args.season] * n
    else:
        seasons = balanced_assign(n, SEASONS, None, rng)
    angle_pairs = assign_angle_pairs(n, rng)
    compose_pairs = assign_composes(n, rng)
    if args.title_style != "auto":
        title_styles = [args.title_style] * n
    else:
        title_styles = [rng.choice(TITLE_STYLES) for _ in range(n)]

    # v2.0: 初始化 CreativeGenerator
    creative_gen = None
    if args.auto_creative and CreativeGenerator is not None:
        lib_path = args.creative_library or None
        creative_gen = CreativeGenerator(library_path=lib_path, rng=rng)
        print(f"[v2.0] 自动创意模式已启用，跳过 LLM 补创意环节")
    elif args.auto_creative and CreativeGenerator is None:
        print("[warn] creative_generator.py 导入失败，auto-creative 不可用，创意字段仍为 TBD")

    # 生成骨架
    skeletons = []
    for i in range(n):
        seasonal_info = query_seasonal(subjects[i].get("name", ""), index_text) if index_text else None
        sk = make_skeleton(
            idx=i + 1,
            subject=subjects[i],
            style=styles[i],
            cast_size=cast_sizes[i],
            season=seasons[i],
            angle_pair=angle_pairs[i],
            compose_pair=compose_pairs[i],
            lang=args.lang,
            ratio=args.ratio,
            id_prefix=args.id_prefix,
            title_style=title_styles[i],
            rng=rng,
            seasonal_info=seasonal_info,
            auto_creative=args.auto_creative,
            creative_gen=creative_gen,
        )
        # 容器指定：记录到 brief._container_override（原 quick_batch 行为）
        if args.container != "auto":
            sk["_container_override"] = args.container
        skeletons.append(sk)
        fp = os.path.join(outdir, f"{sk['id']}_brief.json")
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(sk, f, ensure_ascii=False, indent=2)

    # 输出创意模板
    tpl = make_creative_template(skeletons)
    with open(os.path.join(outdir, "creative_template.json"), "w", encoding="utf-8") as f:
        json.dump(tpl, f, ensure_ascii=False, indent=2)

    # 紧凑摘要表
    print(f"\n===== 骨架生成完成：{n} 份，输出目录 {outdir} =====")
    print(f"{'id':<6} {'主体':<14} {'风格':<5} {'档位':<10} {'季节':<6} {'视角A':<14} {'视角B':<14} {'状态'}")
    print("-" * 90)
    for sk in skeletons:
        a_angle = sk["views"][0]["angle"]
        b_angle = sk["views"][1]["angle"]
        hero_name = sk["hero"]["name"][:12]
        print(f"{sk['id']:<6} {hero_name:<14} {sk['style']:<5} {CAST_NAMES.get(sk['cast_size'], str(sk['cast_size'])):<10} "
              f"{sk['season']:<6} {a_angle:<14} {b_angle:<14} 骨架OK(创意TBD)")

    # 批次均衡统计
    from collections import Counter
    print(f"\n--- 批次均衡统计 ---")
    print(f"档位分布: {dict(Counter(CAST_NAMES.get(c, str(c)) for c in cast_sizes))}")
    print(f"风格分布: {dict(Counter(styles))}")
    print(f"季节分布: {dict(Counter(seasons))}")
    # v2.0: --build 一步拼装（原 quick_batch 行为）
    if args.build:
        if build_one is None:
            print("[错误] build_from_brief 导入失败，--build 不可用")
            sys.exit(1)
        print(f"\n--- 拼装提示词（--build）---")
        ok_count = 0
        fail_count = 0
        prompts = []
        for sk in skeletons:
            pid = sk["id"]
            try:
                if not args.skip_validate and brief_errors is not None:
                    errors, _ = brief_errors(sk)
                    if errors:
                        print(f"  [FAIL] {pid}: {'; '.join(errors)}")
                        fail_count += 1
                        continue
                res = build_one(sk, outdir, pid=pid, write=True)
                words_a = len(res["prompts"].get("A", "").split())
                words_b = len(res["prompts"].get("B", "").split())
                print(f"  [OK] {pid}: A={words_a}w B={words_b}w")
                ok_count += 1
                prompts.append({
                    "id": pid,
                    "hero": sk.get("hero", {}).get("name", ""),
                    "style": sk.get("style", ""),
                    "cast_size": sk.get("cast_size", ""),
                    "A": os.path.join(outdir, f"{pid}_A.txt"),
                    "B": os.path.join(outdir, f"{pid}_B.txt"),
                    "overlay": os.path.join(outdir, f"{pid}_overlay.json"),
                    "words": f"A={words_a} B={words_b}",
                })
            except Exception as e:
                print(f"  [FAIL] {pid}: {e}")
                traceback.print_exc()
                fail_count += 1
        from datetime import datetime
        summary = {
            "tool": "self_skeleton.py v2.0 (--build)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": n, "ok": ok_count, "fail": fail_count,
            "style": args.style, "cast_size": args.cast_size,
            "container": args.container, "season": args.season,
            "auto_creative": args.auto_creative,
            "prompts": prompts,
        }
        with open(os.path.join(outdir, "batch_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\n===== 拼装完成：成功 {ok_count} / 失败 {fail_count} =====")
        print(f"提示词文件: {outdir}")
        print(f"[v2.0] 已一步拼装完成。下一步：读取 *_A.txt / *_B.txt，调用 image_gen 批量生图。")
    elif args.auto_creative:
        print(f"\n[v2.0] 自动创意模式：创意字段已填充，跳过 LLM 补创意。下一步：用 build_from_brief.py --batch <目录> 拼装提示词，然后生图。")
    else:
        print(f"\n下一步：把 creative_template.json 发给 LLM 补全 pv_en/poem/latin/title，然后用 self_merge.py 合并。")


if __name__ == "__main__":
    main()
