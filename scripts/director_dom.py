#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "3.0.0"
"""
director_dom.py —— 从外部 LLM 网页页面文本里提取 brief JSON 的纯函数库 ＋ 批量落地 CLI。

【函数库模式】在 computer_use_tool 代码环境里被 import 使用：本模块不 import 浏览器库 bu，
调用方自己用 bu.get_page_text() 取到页面文本后，把文本传给 extract_brief / extract_latest_brief
/ extract_brief_array / extract_briefs_by_ids，再用 land_briefs 落地为文件。
普通命令行环境同样可用（例如对已保存的页面 txt/html 离线解析）。

【CLI 模式】直接运行本脚本可批量落地 brief 数组（external 浏览器取回 / self 数组模式共用）：
  python director_dom.py --input briefs_array.json --outdir ./batch20
  python director_dom.py --page-text page_text.txt --outdir ./batch20 --min-count 20
  python director_dom.py --input briefs_array.json --outdir ./batch20 --skip-invalid
  python director_dom.py --merge batch1.json batch2.json --outdir ./batch20  （分批合并落地）
  python director_dom.py --input briefs_array.json --outdir ./batch20 --report --expect-ids B001-B020  （提取诊断）

典型用法见 references/director/director-workflow.md §2 通道A。
"""
import re
import json
import os
import sys
import argparse
import random as _random

# 常见水果列表（prepare_subjects 优先避开，保证多样性；不超过 40%）
_COMMON_FRUITS = {
    "草莓", "番茄", "苹果", "梨", "桃", "葡萄", "西瓜", "芒果", "菠萝", "香蕉",
    "橙子", "柠檬", "柚子", "橘子", "柿子", "石榴", "无花果", "猕猴桃", "樱桃",
    "李子", "杏", "枣", "蓝莓", "树莓", "蔓越莓", "荔枝", "龙眼", "杨梅", "枇杷",
    "山楂", "百香果", "火龙果", "牛油果", "椰子", "榴莲", "山竹", "木瓜", "杨桃",
    "橄榄", "白果", "莲子", "荸荠", "芋艿", "山药", "土豆", "红薯", "紫薯",
}

# 类别关键词映射（用于从旬物索引条目名称推断类别）
_CATEGORY_KEYWORDS = {
    "seafood": ["鱼", "虾", "蟹", "贝", "蚝", "蛤", "蛏", "鱿", "墨", "章", "鲍", "参",
                "翅", "肚", "裙带", "海带", "紫菜", "海蜇", "青花鱼", "三文鱼", "金枪鱼",
                "鳕鱼", "鲈鱼", "带鱼", "黄鱼", "鲳鱼", "鳗鱼", "章鱼", "墨鱼", "鱿鱼",
                "对虾", "基围虾", "斑节虾", "小龙虾", "皮皮虾", "帝王蟹", "梭子蟹", "青蟹",
                "大闸蟹", "花蟹", "生蚝", "牡蛎", "花蛤", "文蛤", "北极贝", "扇贝", "鲍鱼",
                "海参", "海胆", "海螺", "蛏子", "蚬子"],
    "dessert": ["蛋糕", "饼干", "面包", "酥", "挞", "派", "布丁", "果冻", "慕斯", "冰淇淋",
                "巧克力", "糖果", "马卡龙", "可露丽", "玛德琳", "达克瓦兹", "千层", "铜锣烧",
                "大福", "曲奇", "蛋白霜", "蜂蜜蛋糕", "磅蛋糕", "镜面蛋糕", "戚风", "巴斯克",
                "提拉米苏", "舒芙蕾", "华夫饼", "松饼", "司康", "贝果", "碱水", "法棍",
                "吐司", "可颂", "丹麦", "泡芙", "蛋挞", "椰丝", "牛轧糖", "太妃糖"],
    "vegetable": ["芦笋", "豌豆", "洋蓟", "春笋", "香椿", "莴笋", "春韭", "荠菜", "番茄",
                  "黄瓜", "茄子", "辣椒", "莲藕", "茭白", "茨菇", "木耳", "香菇", "平菇",
                  "杏鲍菇", "羊肚菌", "牛肝菌", "松露", "竹荪", "银耳", "百合", "芡实",
                  "菱角", "茨实", "秋葵", "芹菜", "菠菜", "白菜", "甘蓝", "花椰菜", "西兰花",
                  "萝卜", "胡萝卜", "洋葱", "大蒜", "姜", "葱", "香菜", "薄荷", "罗勒",
                  "迷迭香", "百里香", "牛至", "鼠尾草", "薰衣草", "洋甘菊"],
    "flower": ["郁金香", "牡丹", "紫藤", "樱花", "金莲花", "风信子", "月季", "洋牡丹",
               "康乃馨", "鸢尾", "紫罗兰", "马蹄莲", "泡泡玫瑰", "食用花", "荷花", "菊花",
               "桂花", "梅花", "兰花", "百合", "向日葵", "玫瑰", "满天星", "尤加利",
               "银叶菊", "绣球", "茉莉", "栀子", "含笑", "玉兰", "海棠", "丁香"],
    "utensil": ["刀", "叉", "勺", "杯", "碗", "盘", "碟", "壶", "瓶", "罐", "锅",
                "砧板", "托盘", "蒸笼", "茶盘", "花瓶", "餐巾", "餐布", "书籍", "画框",
                "筷子", "筷架", "量杯", "油瓶", "酱油碟", "饭勺", "茶滤", "茶托",
                "茶盏", "茶杯", "汤锅", "手冲", "咖啡壶", "餐盘", "银质", "铜质",
                "不锈钢", "陶瓷", "玻璃", "木质", "竹制", "石臼", "木托盘"],
    "grain": ["米", "面", "麦", "稻", "粟", "黍", "稷", "粱", "玉米", "燕麦", "荞麦",
              "藜麦", "黑米", "红米", "糙米", "糯米", "小米", "薏米", "芡实", "莲子",
              "红豆", "绿豆", "黄豆", "黑豆", "芸豆", "扁豆", "豌豆", "蚕豆"],
    "dairy": ["牛奶", "黄油", "奶酪", "芝士", "酸奶", "奶油", "炼乳", "奶粉", "羊奶",
              "马苏里拉", "帕玛森", "布里", "蓝纹", "车达", "奶油奶酪"],
}


def _classify_subject(name):
    """根据条目名称推断类别，返回类别字符串（fruit/seafood/dessert/vegetable/flower/utensil/grain/dairy/other）。"""
    if not name:
        return "other"
    if name in _COMMON_FRUITS:
        return "fruit"
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return cat
    return "other"


def prepare_subjects(n, avoid=None, rng=None):
    """从旬物索引 374 个条目中自动选 n 个多样化主体，返回 list[str]。
    - avoid: 要排除的主体名称列表（历史去重）
    - rng: random.Random 实例
    类别配额（A 方案·脚本层保证）：
      - 水果类 ≤ 30%（避免草莓/梨/无花果等常见水果反复出现）
      - 海鲜类 ≥ 10%（保证批次中有海鲜类主体）
      - 其他类别（甜点/蔬菜/花卉/器物/谷物/奶制品等）按剩余比例均衡分配
    保证：不重复、避开 avoid、类别配额满足、批次内多样化
    """
    rng = rng or _random
    try:
        from self_skeleton import extract_all_subjects
        all_names = extract_all_subjects()
    except Exception:
        all_names = []
    if not all_names:
        return []
    avoid_set = set(avoid or [])
    # 按类别分组
    by_cat = {}
    for name in all_names:
        if name in avoid_set:
            continue
        cat = _classify_subject(name)
        by_cat.setdefault(cat, []).append(name)
    # 配额计算
    n_fruit = max(0, int(n * 0.30))  # 水果 ≤30%
    n_seafood = max(1, int(n * 0.10))  # 海鲜 ≥10%
    n_other = n - n_fruit - n_seafood  # 其他类别分配剩余
    # 其他类别池（合并甜点/蔬菜/花卉/器物/谷物/奶制品/other）
    other_pool = []
    for cat in ("dessert", "vegetable", "flower", "utensil", "grain", "dairy", "other"):
        other_pool.extend(by_cat.get(cat, []))
    chosen = []
    # 1. 先选海鲜（保证 ≥10%）
    seafood_pool = by_cat.get("seafood", [])
    if seafood_pool:
        chosen.extend(rng.sample(seafood_pool, min(n_seafood, len(seafood_pool))))
    # 2. 再选其他类别（占剩余大部分）
    if other_pool and n_other > 0:
        avail = [x for x in other_pool if x not in chosen]
        if avail:
            chosen.extend(rng.sample(avail, min(n_other, len(avail))))
    # 3. 最后选水果（≤30%）
    fruit_pool = by_cat.get("fruit", [])
    if fruit_pool and len(chosen) < n:
        remaining = n - len(chosen)
        fruit_avail = [x for x in fruit_pool if x not in chosen]
        if fruit_avail:
            chosen.extend(rng.sample(fruit_avail, min(remaining, len(fruit_avail), n_fruit)))
    # 4. 不够则从全部可用中补
    if len(chosen) < n:
        pool = [name for name in all_names if name not in avoid_set and name not in chosen]
        if pool:
            chosen.extend(rng.sample(pool, min(n - len(chosen), len(pool))))
    rng.shuffle(chosen)
    return chosen[:n]


def check_subject_diversity(briefs, avoid=None):
    """检查一批 brief 的主体多样性，返回 (issues_list, stats_dict)。
    检查项：1.一批内主体重复 2.配角与主体同类 3.主体在历史已用列表中
    """
    issues = []
    hero_names = []
    for b in briefs:
        pid = str(b.get("id", "?"))
        hero = b.get("hero", {})
        hero_name = hero.get("name", "") if isinstance(hero, dict) else ""
        hero_en = (hero.get("en", "") if isinstance(hero, dict) else "").lower()
        hero_names.append(hero_name)
        # 配角与主体同类检查
        secondary = b.get("secondary", [])
        if isinstance(secondary, list):
            for sec in secondary:
                if not isinstance(sec, dict):
                    continue
                sec_name = sec.get("name", "")
                sec_en = (sec.get("en", "") or "").lower()
                if (hero_name and sec_name == hero_name) or                    (hero_en and sec_en and any(w in sec_en for w in hero_en.split() if len(w) > 2)):
                    issues.append(f"{pid}: 配角'{sec_name}'与主体'{hero_name}'同类")
        # 历史已用检查
        if avoid and hero_name in avoid:
            issues.append(f"{pid}: 主体'{hero_name}'在历史已用列表中")
    # 一批内重复检查
    from collections import Counter
    name_counts = Counter(h for h in hero_names if h)
    duplicates = {name: count for name, count in name_counts.items() if count > 1}
    for name, count in duplicates.items():
        issues.append(f"主体'{name}'在一批内重复 {count} 次")
    stats = {
        "total": len(briefs),
        "unique_subjects": len(set(h for h in hero_names if h)),
        "duplicates": duplicates,
        "issues": len(issues),
    }
    return issues, stats

# 同时兼容 "id": "S00X" 与 'id': 'S00X'
_ID_RE = re.compile(r'["\']id["\']\s*:\s*["\']([^"\']+)["\']')


def _iter_decodes(txt):
    """从页面文本中每一个 '{' 尝试 raw_decode，yield (obj, end)。"""
    dec = json.JSONDecoder()
    for m in re.finditer(r'\{', txt):
        try:
            obj, end = dec.raw_decode(txt, m.start())
            if isinstance(obj, dict):
                yield obj, end
        except Exception:
            continue


def extract_first_json_block(page_text):
    """优先提取页面文本中第一个 ```json 代码块的内容，返回代码块内文本；找不到返回 None。
    当 DeepSeek 输出有解释文字时，代码块提取比全局扫描更精准，避免解释文字中的 '{' 干扰。
    兼容 ```json 和 ``` 两种代码块标记。"""
    if not page_text:
        return None
    # 匹配 ```json 或 ``` 开头的代码块，取第一个
    m = re.search(r'```(?:json)?\s*\n(.*?)```', page_text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def _views_ok(obj):
    vs = obj.get("views")
    return isinstance(vs, list) and len(vs) == 2 and \
        [v.get("tag") for v in vs if isinstance(v, dict)] == ["A", "B"]


def extract_brief(page_text, pid):
    """提取 id==pid 且 A/B 齐全的 brief；找不到返回 None。取最后一个匹配（最新一次回复）。"""
    if not page_text:
        return None
    hits = []
    for m in _ID_RE.finditer(page_text):
        if m.group(1) != pid:
            continue
        st = page_text.rfind('{', 0, m.start())
        if st < 0:
            continue
        try:
            obj, _ = json.JSONDecoder().raw_decode(page_text, st)
        except Exception:
            # 回退：全局扫描所有可解码对象里找 id 匹配的
            obj = None
            for o, _e in _iter_decodes(page_text):
                if o.get("id") == pid:
                    obj = o
            if obj is None:
                continue
        if isinstance(obj, dict) and obj.get("id") == pid and _views_ok(obj):
            hits.append(obj)
    return hits[-1] if hits else None


def extract_latest_brief(page_text):
    """不指定 id：返回页面里最后一个 A/B 齐全的 brief（没有则 None）。"""
    if not page_text:
        return None
    objs = [o for o, _ in _iter_decodes(page_text) if _views_ok(o) and o.get("id")]
    return objs[-1] if objs else None


# 与 validate_brief 同源的轻校验，方便浏览器 cell 里拿到 obj 后立刻自检；
# 若同目录 import 失败（路径未加 scripts），降级为只检查 A/B 齐全。
try:
    from validate_brief import brief_errors  # noqa: F401
except Exception:  # pragma: no cover
    def brief_errors(obj):
        errs = []
        if not isinstance(obj, dict):
            return ["not an object"], []
        if not _views_ok(obj):
            errs.append("views 不是完整 A/B")
        for k in ("id", "hero", "text"):
            if k not in obj:
                errs.append(f"missing {k}")
        return errs, []


def extract_brief_array(page_text, min_count=1):
    """从页面文本提取所有 A/B 齐全的 brief，返回 list[dict]（按出现顺序，同 id 取最后一个）。
    用于 external 批量数组模式：DeepSeek 一次回 N 个 brief 的 JSON 数组，本函数批量提取。
    - page_text: 页面全文（bu.get_page_text() 返回值）
    - min_count: 期望最少数量，不足时返回空列表并由调用方判断是否继续轮询
    优先从第一个 ```json 代码块提取（更精准），代码块提取失败或数量不足时回退全局扫描。
    """
    if not page_text:
        return []
    # 优先提取第一个 json 代码块内容
    block_text = extract_first_json_block(page_text)
    search_text = block_text if block_text else page_text
    # 收集所有可解码的、A/B 齐全的、有 id 的 brief
    seen = {}  # id -> (index, obj)
    order = []
    for idx, (obj, _end) in enumerate(_iter_decodes(search_text)):
        if not isinstance(obj, dict):
            continue
        if not _views_ok(obj):
            continue
        pid = obj.get("id")
        if not pid:
            continue
        if pid not in seen:
            order.append(pid)
        seen[pid] = (idx, obj)
    result = [seen[pid][1] for pid in order]
    if len(result) < min_count:
        return []  # 数量不够，调用方应继续轮询
    return result


def extract_briefs_by_ids(page_text, ids):
    """按 id 列表批量提取，返回 dict[id] -> obj（找不到的 id 不在结果里）。"""
    if not page_text or not ids:
        return {}
    id_set = set(ids)
    result = {}
    for obj, _end in _iter_decodes(page_text):
        if isinstance(obj, dict) and obj.get("id") in id_set and _views_ok(obj):
            result[obj["id"]] = obj  # 同 id 取最后一个
    return result


def land_briefs(briefs, outdir, skip_invalid=False):
    """把 brief 列表落地为 <id>_brief.json，返回 (ok_list, fail_list)。
    - briefs: list[dict]
    - outdir: 输出目录
    - skip_invalid: True 时校验失败的 brief 跳过不落地；False 时全部落地（由下游 validate 拦截）
    B7: id 重复时自动追加后缀（B001 -> B001_2）并输出警告，避免后一个覆盖前一个。
    """
    import os, json
    os.makedirs(outdir, exist_ok=True)
    ok, fail = [], []
    seen_ids = {}  # id -> 出现次数
    for b in briefs:
        pid = str(b.get("id", "unknown")).strip()
        if not pid:
            fail.append((pid, "缺少 id"))
            continue
        # B7: id 重复检测，自动追加后缀
        if pid in seen_ids:
            seen_ids[pid] += 1
            new_pid = f"{pid}_{seen_ids[pid]}"
            print(f"  [警告] id '{pid}' 重复，自动重命名为 '{new_pid}'（避免覆盖）", file=sys.stderr)
            b["id"] = new_pid
            pid = new_pid
        else:
            seen_ids[pid] = 1
        if skip_invalid and brief_errors is not None:
            errs, _ = brief_errors(b)
            if errs:
                fail.append((pid, "; ".join(errs)))
                continue
        try:
            fp = os.path.join(outdir, f"{pid}_brief.json")
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(b, f, ensure_ascii=False, indent=2)
            ok.append(pid)
        except Exception as ex:
            fail.append((pid, f"写入失败: {ex}"))
    return ok, fail


# ==================== CLI 批量落地（external / self 数组模式共用） ====================


def load_from_json(path):
    """从 JSON 文件加载 brief 列表，支持直接数组和包裹对象。"""
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("briefs", "data", "items", "results"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # 如果 dict 本身就是一个 brief
        if "id" in data and "views" in data:
            return [data]
    raise ValueError("JSON 格式不对：既不是数组，也不是包含 briefs/data 的对象")


def load_from_page_text(path, min_count=1):
    """从页面文本文件提取 brief 列表。"""
    with open(path, "r", encoding="utf-8-sig") as f:
        txt = f.read()
    briefs = extract_brief_array(txt, min_count=min_count)
    if not briefs:
        # 尝试不设 min_count 提取，看能找到几个
        all_briefs = extract_brief_array(txt, min_count=0)
        raise ValueError(f"页面文本中未提取到足够 brief（期望 >= {min_count}，实际找到 {len(all_briefs)}）")
    return briefs


def load_from_multiple(paths):
    """从多个 JSON/页面文本文件合并加载 brief 列表，同 id 取最后一个，按 id 排序。
    用于分批输出场景：DeepSeek 分 2-3 批输出，每批存一个文件，合并后统一落地。
    - paths: 文件路径列表，每个文件可以是 JSON 数组或页面文本
    - 返回: 合并去重后的 brief 列表
    """
    seen = {}  # id -> obj
    order = []
    for path in paths:
        try:
            # 先尝试按 JSON 加载
            briefs = load_from_json(path)
        except Exception:
            # JSON 失败则按页面文本加载
            try:
                briefs = load_from_page_text(path, min_count=0)
            except Exception as ex:
                print(f"  [跳过] {path}: {ex}")
                continue
        for b in briefs:
            pid = str(b.get("id", "")).strip()
            if not pid:
                continue
            if pid not in seen:
                order.append(pid)
            seen[pid] = b  # 同 id 取最后一个
    # 按 id 排序（如 B001, B002, ...）
    result = [seen[pid] for pid in sorted(order)]
    return result


def parse_expect_ids(spec):
    """解析期望 id 范围字符串，返回 id 列表。
    支持格式：
    - "B001-B020" → B001, B002, ..., B020
    - "B001,B003,B005" → B001, B003, B005
    - "B001-B010,B015" → 混合
    """
    if not spec:
        return []
    result = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = start.strip()
            end = end.strip()
            # 提取前缀和数字
            import re
            m_start = re.match(r'([A-Za-z]+)(\d+)', start)
            m_end = re.match(r'([A-Za-z]+)(\d+)', end)
            if m_start and m_end:
                prefix = m_start.group(1)
                num_start = int(m_start.group(2))
                num_end = int(m_end.group(2))
                width = len(m_start.group(2))
                for n in range(num_start, num_end + 1):
                    result.append(f"{prefix}{str(n).zfill(width)}")
            else:
                result.append(start)
                result.append(end)
        else:
            result.append(part)
    return result


def generate_report(briefs, expect_ids=None):
    """生成提取诊断报告，返回 (report_str, missing_ids, invalid_details)。
    - briefs: 提取到的 brief 列表
    - expect_ids: 期望的 id 列表（可选）
    """
    lines = []
    found_ids = [str(b.get("id", "?")) for b in briefs]
    n = len(briefs)

    lines.append(f"===== 提取诊断报告 =====")
    lines.append(f"提取到 brief 数: {n}")
    lines.append(f"提取到的 id: {', '.join(found_ids) if found_ids else '(无)'}")

    # 期望 id 检测
    missing_ids = []
    if expect_ids:
        missing_ids = [pid for pid in expect_ids if pid not in found_ids]
        extra_ids = [pid for pid in found_ids if pid not in expect_ids]
        lines.append(f"期望 id 数: {len(expect_ids)}")
        lines.append(f"缺失 id: {', '.join(missing_ids) if missing_ids else '(无)'}")
        if extra_ids:
            lines.append(f"超出期望的 id: {', '.join(extra_ids)}")
        lines.append(f"覆盖率: {len(found_ids)}/{len(expect_ids)} = {len(found_ids)/len(expect_ids)*100:.0f}%")

    # 校验失败详情
    invalid_details = []
    valid_count = 0
    error_dist = {}
    for b in briefs:
        if brief_errors is not None:
            errs, warns = brief_errors(b)
            if errs:
                pid = str(b.get("id", "?"))
                invalid_details.append((pid, "; ".join(errs)))
                for e in errs:
                    # 简化错误类型用于统计
                    etype = e.split(":")[0].split("（")[0].strip()[:30]
                    error_dist[etype] = error_dist.get(etype, 0) + 1
            else:
                valid_count += 1
        else:
            valid_count += 1

    lines.append(f"校验通过: {valid_count} / {n}")
    if invalid_details:
        lines.append(f"校验失败: {len(invalid_details)} / {n}")
        lines.append(f"失败原因分布: {dict(error_dist)}")
    else:
        lines.append(f"校验失败: 0 / {n}")

    # cast_size 自洽检查
    cast_issues = []
    for b in briefs:
        cs = b.get("cast_size")
        sec = b.get("secondary", [])
        if cs is not None and isinstance(sec, list):
            if cs != 1 + len(sec):
                cast_issues.append(f"{b.get('id', '?')}(cast_size={cs}, secondary={len(sec)}条)")
    if cast_issues:
        lines.append(f"cast_size 不自洽: {len(cast_issues)} 个 -> {', '.join(cast_issues[:5])}{'...' if len(cast_issues) > 5 else ''}")

    # pv_en 词数检查
    pv_issues = []
    for b in briefs:
        for v in b.get("views", []):
            pv = str(v.get("pv_en", ""))
            wc = len(pv.split())
            if pv and pv != "TBD" and (wc < 90 or wc > 130):
                pv_issues.append(f"{b.get('id', '?')}.{v.get('tag', '?')}={wc}词")
    if pv_issues:
        lines.append(f"pv_en 词数偏离 90-130: {len(pv_issues)} 条 -> {', '.join(pv_issues[:5])}{'...' if len(pv_issues) > 5 else ''}")

    # 主体多样性检查
    div_issues, div_stats = check_subject_diversity(briefs)
    lines.append(f"主体多样性: {div_stats['unique_subjects']}/{div_stats['total']} 个不重复主体")
    if div_issues:
        lines.append(f"主体多样性问题: {len(div_issues)} 项 -> {'; '.join(div_issues[:5])}{'...' if len(div_issues) > 5 else ''}")

    return "\n".join(lines), missing_ids, invalid_details


def summarize(b):
    """生成紧凑摘要行。"""
    pid = b.get("id", "?")
    hero = b.get("hero", {})
    hero_name = hero.get("name", "?") if isinstance(hero, dict) else "?"
    style = b.get("style", "?")
    cs = b.get("cast_size", "?")
    season = b.get("season", "?")
    lang = b.get("lang", "?")
    title = b.get("text", {}).get("title", "?") if isinstance(b.get("text"), dict) else "?"
    return pid, hero_name, style, cs, season, lang, title


def main():
    ap = argparse.ArgumentParser(description="通用 brief JSON 数组批量落地器（external/self 数组模式共用）")
    ap.add_argument("--input", help="JSON 数组文件（brief 数组或包裹对象）")
    ap.add_argument("--page-text", help="页面文本文件（自动提取所有 brief）")
    ap.add_argument("--merge", nargs="+", help="分批合并：从多个 JSON/页面文本文件合并加载，同 id 去重")
    ap.add_argument("--outdir", required=True, help="输出目录")
    ap.add_argument("--min-count", type=int, default=1, help="期望最少 brief 数量（页面文本模式用）")
    ap.add_argument("--skip-invalid", action="store_true", help="校验失败的 brief 跳过不落地")
    ap.add_argument("--batch-size", type=int, default=None, choices=[2, 5, 10, 15, 20, 30],
                    help="批量规模（仅用于提示，不强制）")
    ap.add_argument("--report", action="store_true", help="输出提取诊断报告（候选数/通过数/缺失id/校验失败分布）")
    ap.add_argument("--expect-ids", help="期望 id 范围，如 B001-B020 或 B001,B003,B005，自动检测缺失")
    ap.add_argument("--prepare-subjects", type=int, default=None,
                    help="独立模式：从旬物索引 374 个条目中自动生成 N 个多样化主体的题材清单（输出可直接粘贴到 §B2 指令）")
    ap.add_argument("--avoid-subjects", default="",
                    help="逗号分隔的已用主体列表（历史去重），prepare-subjects 时排除、落地时校验")
    ap.add_argument("--history-file", default="",
                    help="历史已用主体 JSON 文件路径（数组格式），prepare-subjects 时自动读取并排除")
    ap.add_argument("--append-history", action="store_true",
                    help="落地后把本批主体追加到 --history-file（用于下一批历史去重）")
    args = ap.parse_args()

    # --prepare-subjects 独立模式：不需要 --input/--page-text/--merge
    if args.prepare_subjects:
        avoid_list = [s.strip() for s in args.avoid_subjects.split(",") if s.strip()] if args.avoid_subjects else []
        if args.history_file and os.path.exists(args.history_file):
            try:
                with open(args.history_file, "r", encoding="utf-8-sig") as f:
                    hist = json.load(f)
                    if isinstance(hist, list):
                        avoid_list.extend(str(h) for h in hist)
            except Exception:
                pass
        rng = _random.Random()
        subjects = prepare_subjects(args.prepare_subjects, avoid=avoid_list, rng=rng)
        if not subjects:
            print("错误：未能从旬物索引生成题材清单（请确认 seasonal_produce_index.json 或 seasonal-produce-index.md 存在）。")
            sys.exit(1)
        print(f"\n===== 自动题材清单（从旬物索引 374 个条目中选择 {len(subjects)} 个多样化主体）=====")
        print(f"题材清单：{'. '.join(f'{i+1}.{s}' for i, s in enumerate(subjects))}")
        if avoid_list:
            print(f"\n已排除历史主体（{len(avoid_list)} 个）：{', '.join(avoid_list[:20])}{'...' if len(avoid_list) > 20 else ''}")
        print(f"\n【使用方法】将以上「题材清单」复制到 §B2 批量下发指令的「题材清单」字段。")
        print(f"DeepSeek 必须严格使用这些主体，不得自行替换为常见水果。")
        print(f"非常见水果类占比 >= 60%，保证主体多样性。")
        # 同时保存题材清单到 outdir（如果指定了）
        if args.outdir:
            os.makedirs(args.outdir, exist_ok=True)
            fp = os.path.join(args.outdir, "prepared_subjects.json")
            with open(fp, "w", encoding="utf-8") as f:
                json.dump({"subjects": subjects, "avoid": avoid_list}, f, ensure_ascii=False, indent=2)
            print(f"\n题材清单已保存: {fp}")
        sys.exit(0)

    if not args.input and not args.page_text and not args.merge:
        print("错误：必须提供 --input / --page-text / --merge / --prepare-subjects 之一。")
        sys.exit(1)

    outdir = os.path.abspath(args.outdir)

    # 解析期望 id
    expect_ids = parse_expect_ids(args.expect_ids) if args.expect_ids else None

    # 加载 brief 列表
    try:
        if args.merge:
            print(f"合并加载 {len(args.merge)} 个文件...")
            briefs = load_from_multiple(args.merge)
            print(f"合并后共 {len(briefs)} 个 brief（同 id 已去重）")
        elif args.input:
            briefs = load_from_json(args.input)
        else:
            briefs = load_from_page_text(args.page_text, args.min_count)
    except Exception as ex:
        print(f"错误：加载失败：{ex}")
        sys.exit(1)

    if not briefs:
        print("错误：未找到任何 brief。")
        sys.exit(1)

    n = len(briefs)
    if args.batch_size and n != args.batch_size:
        print(f"[提示] 实际 brief 数量 {n} 与 --batch-size {args.batch_size} 不一致，以实际数量 {n} 为准。")

    # 提取诊断报告
    if args.report:
        report_str, missing_ids, invalid_details = generate_report(briefs, expect_ids)
        print(report_str)
        if missing_ids:
            print(f"\n[建议] 缺失的 {len(missing_ids)} 个 id 可单独补发：只输出 {', '.join(missing_ids[:5])}{'...' if len(missing_ids) > 5 else ''} 的 brief，不要整批重发。")
        print()

    # 逐个轻校验（用于摘要，不决定是否落地，除非 --skip-invalid）
    valid_count = 0
    invalid_details = []
    for b in briefs:
        if brief_errors is not None:
            errs, warns = brief_errors(b)
            if errs:
                invalid_details.append((b.get("id", "?"), "; ".join(errs)))
            else:
                valid_count += 1
        else:
            valid_count += 1

    # 解析 avoid 列表
    avoid_list = [s.strip() for s in args.avoid_subjects.split(",") if s.strip()] if args.avoid_subjects else []
    if args.history_file and os.path.exists(args.history_file):
        try:
            with open(args.history_file, "r", encoding="utf-8-sig") as f:
                hist = json.load(f)
                if isinstance(hist, list):
                    avoid_list.extend(str(h) for h in hist)
        except Exception:
            pass

    # 主体多样性校验（落地前检查，问题标记但不阻断）
    div_issues, div_stats = check_subject_diversity(briefs, avoid=avoid_list)
    if div_issues:
        print(f"\n[主体多样性警告] {len(div_issues)} 项问题：")
        for issue in div_issues[:10]:
            print(f"  - {issue}")
        if len(div_issues) > 10:
            print(f"  ... 还有 {len(div_issues) - 10} 项")
    else:
        print(f"\n[主体多样性] {div_stats['unique_subjects']}/{div_stats['total']} 个不重复主体，无重复/同类/历史问题")

    # 落地
    ok, fail = land_briefs(briefs, outdir, skip_invalid=args.skip_invalid)

    # --append-history：把本批主体追加到历史文件
    if args.append_history and args.history_file:
        existing = []
        if os.path.exists(args.history_file):
            try:
                with open(args.history_file, "r", encoding="utf-8-sig") as f:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = []
            except Exception:
                existing = []
        new_subjects = [str(b.get("hero", {}).get("name", "")) for b in briefs if isinstance(b.get("hero"), dict)]
        existing.extend(new_subjects)
        # 去重，保留最近 100 个
        seen = set()
        deduped = []
        for s in reversed(existing):
            if s and s not in seen:
                seen.add(s)
                deduped.append(s)
        deduped = list(reversed(deduped))[-100:]
        with open(args.history_file, "w", encoding="utf-8") as f:
            json.dump(deduped, f, ensure_ascii=False, indent=2)
        print(f"\n[历史去重] 已追加 {len(new_subjects)} 个主体到 {args.history_file}（共 {len(deduped)} 个，保留最近100个）")

    # 紧凑摘要表
    print(f"\n===== 数组落地完成：落地 {len(ok)} / 失败 {len(fail)} / 总计 {n} =====")
    if args.skip_invalid:
        print(f"  [--skip-invalid 模式，校验失败的已跳过]")
    print(f"  校验通过：{valid_count} / {n}")
    print(f"\n{'id':<6} {'主体':<14} {'风格':<5} {'档位':<5} {'季节':<6} {'语言':<5} {'标题':<16} {'状态'}")
    print("-" * 80)
    for b in briefs:
        pid, hero, style, cs, season, lang, title = summarize(b)
        status = "OK" if pid in ok else "FAIL"
        hero_short = str(hero)[:12]
        title_short = str(title)[:14]
        print(f"{pid:<6} {hero_short:<14} {style:<5} {cs:<5} {season:<6} {lang:<5} {title_short:<16} {status}")

    if fail:
        print(f"\n--- 落地失败详情 ---")
        for pid, why in fail:
            print(f"  [FAIL] {pid}  -> {why}")

    if invalid_details and not args.skip_invalid:
        print(f"\n--- 校验有 error 但已落地（下游 validate_brief.py 会拦截）---")
        for pid, why in invalid_details:
            print(f"  [WARN] {pid}  -> {why}")

    print(f"\n下一步：python build_from_brief.py --batch {outdir}  （批量校验+拼装提示词）")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
