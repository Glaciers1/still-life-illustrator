#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "3.0.0"
"""
validate_brief.py —— Brief JSON 硬校验门（brief@1.1，唯一规划格式）。
在 build_from_brief.py 之前必须通过：errors 致命（退出码 1，不允许进 build）；warnings 仅提示。
纯标准库，可在普通命令行与浏览器 computer_use 代码环境复用（director_dom.brief_errors 即本文件函数）。

用法:
    python validate_brief.py brief.json
    python validate_brief.py brief.json --strict     # warning 也按致命处理
退出码: 0=通过(可带 warning) / 1=有 error(--strict 时含 warning)
"""
import json, sys, argparse, re

STYLES = {"S1", "S2", "S3"}
LANGS = {"zh", "en"}
FONTS = {"serif", "sans", "kai", "hand"}
TSTYLES = {"normal", "italic", "wave", "arch", "scatter"}
SUB_BLANKS = {"左上", "右上", "左下", "右下", "upper-left", "upper-right", "lower-left", "lower-right"}
# pv_en 里禁止夹带的"本地技术段"关键词（命中给 warning，提示创意越界写了渲染技术段）
TECH_LEAK = ["watercolor", "oil-pastel", "pastel", "crayon", "flat color block", "color blocks",
             "no outline", "closed outline", "edge hierarchy", "no text", "no letters",
             "kraft", "cotton paper", "scumbled", "bleeding edge"]
HEX = re.compile(r"^#?[0-9a-fA-F]{6}$")


def _is_hex(v):
    return isinstance(v, str) and bool(HEX.match(v.strip()))


def _similar(a, b):
    """非常轻量的相似度：相同 token 的 Jaccard，用于判 A/B 视角/构图是否雷同。"""
    sa, sb = set((a or "").lower().split()), set((b or "").lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def brief_errors(b):
    """返回 (errors, warnings)。b 为 dict。供 build_from_brief / director_dom 复用。"""
    e, w = [], []
    if not isinstance(b, dict):
        return ["brief 不是 JSON 对象"], []

    # ---- 顶层必填与枚举 ----
    for k in ["id", "season", "style", "ratio", "lang", "hero", "views", "text"]:
        if k not in b:
            e.append(f"缺少顶层字段: {k}")
    if b.get("schema") != "brief@1.1":
        w.append('schema 非 "brief@1.1"（旧版可跑，建议升级）')
    if b.get("source") not in ("external", "self"):
        e.append('source 必须是 "external" 或 "self"')
    if b.get("style") not in STYLES:
        e.append(f"style 非法: {b.get('style')}（应 S1/S2/S3）")
    if b.get("lang") not in LANGS:
        e.append(f"lang 非法: {b.get('lang')}（应 zh/en）")
    if not re.match(r"^\d+:\d+$", str(b.get("ratio", ""))):
        e.append(f"ratio 非法: {b.get('ratio')}（应如 3:4）")

    # ---- 组合档位 cast_size ----
    sec = b.get("secondary", [])
    if sec is None:
        sec = []
    if not isinstance(sec, list):
        e.append("secondary 必须是数组")
        sec = []
    cs = b.get("cast_size")
    if not isinstance(cs, int) or not (1 <= cs <= 6):
        e.append(f"cast_size 必须是 1-6 的整数，当前: {cs!r}")
    else:
        if cs != 1 + len(sec):
            e.append(f"cast_size={cs} 与 secondary 条数={len(sec)} 不自洽（应 cast_size == 1 + 条数）")
    if len(sec) > 5:
        e.append(f"secondary 最多 5 类（Lush 上限），当前 {len(sec)} 类")
    for i, s in enumerate(sec):
        if not isinstance(s, dict):
            e.append(f"secondary[{i}] 不是对象")
            continue
        for k in ["name", "en", "place"]:
            if not str(s.get(k, "")).strip():
                e.append(f"secondary[{i}] 缺少 {k}")
        if not isinstance(s.get("count"), int) or s.get("count", 0) < 1:
            e.append(f"secondary[{i}].count 必须是 >=1 整数")
        place = str(s.get("place", ""))
        if place and not re.search(r"(上|旁|前|后|里|中|边|面|间|around|beside|behind|front|in |on |rest|cluster|身位|碟|盘|篮|布|桌)", place):
            w.append(f"secondary[{i}].place 未明显交代承载面/接触关系，注意不得悬空")

    # ---- 主体 ----
    h = b.get("hero", {})
    if isinstance(h, dict):
        for k in ["name", "en", "states"]:
            if not str(h.get(k, "")).strip():
                e.append(f"hero 缺少 {k}")
        if not isinstance(h.get("count"), int) or h.get("count", 0) < 1:
            e.append("hero.count 必须是 >=1 整数")

    # ---- 配色 ----
    pal = b.get("palette", {})
    if isinstance(pal, dict):
        if not _is_hex(pal.get("bg", "")):
            w.append(f"palette.bg 不是标准 #HEX: {pal.get('bg')!r}")
    else:
        w.append("palette 缺失或非对象")

    # ---- 双稿 ----
    vs = b.get("views", [])
    if not isinstance(vs, list) or len(vs) != 2:
        e.append("views 必须恰好 2 条（A/B）")
    else:
        tags = [v.get("tag") for v in vs]
        if tags != ["A", "B"]:
            e.append(f"views 的 tag 应依次为 A、B，当前 {tags}")
        for v in vs:
            tag = v.get("tag", "?")
            if v.get("sub_blank") not in SUB_BLANKS:
                w.append(f"view {tag} 的 sub_blank 非标准方位: {v.get('sub_blank')!r}")
            pv = str(v.get("pv_en", ""))
            n = len(pv.split())
            if not (90 <= n <= 130):
                w.append(f"view {tag} pv_en 词数 {n} 超出建议区间 90-130")
            low = pv.lower()
            if "exactly" not in low and "count" not in low:
                w.append(f"view {tag} pv_en 未写 'exactly N (count carefully)' 精确数量")
            for kw in TECH_LEAK:
                if kw in low:
                    w.append(f"view {tag} pv_en 疑似夹带本地技术段词 '{kw}'（应只写可变画面）")
                    break
        if len(vs) == 2:
            if _similar(vs[0].get("angle", ""), vs[1].get("angle", "")) > 0.6:
                e.append("A/B 两稿 angle 过于雷同，视角必须明显不同")
            if _similar(vs[0].get("compose", ""), vs[1].get("compose", "")) > 0.75:
                w.append("A/B 两稿 compose 相似度偏高，注意版式/落点要不同")

    # ---- 文字 ----
    t = b.get("text", {})
    if isinstance(t, dict):
        if not str(t.get("title", "")).strip():
            e.append("text.title 为空")
        if t.get("title_font") not in FONTS:
            e.append(f"title_font 非法: {t.get('title_font')}（serif/sans/kai/hand，无 marker）")
        if t.get("title_style") not in TSTYLES:
            e.append(f"title_style 非法: {t.get('title_style')}")
        poem = t.get("poem", [])
        if not isinstance(poem, list) or len(poem) != 2:
            e.append("text.poem 必须恰好 2 行")
        lang = b.get("lang")
        latin = str(t.get("latin", "") or "").strip()
        season = str(t.get("season_line", "") or "").strip()
        if lang == "en":
            if not season:
                e.append("en 模式 season_line 不能为空（英文大写季节）")
            elif season != season.upper():
                w.append("en 模式 season_line 建议全大写")
            if not latin:
                pass  # 空 latin 合法：叠字时跳过 latin 行（无学名则不显示）
            elif latin.upper() == "TBD":
                w.append("latin=TBD：交付前需补准确学名，或留空跳过 latin 行")
            elif latin != latin.upper():
                e.append("en 模式 latin 必须为大写学名（如 PUNICA GRANATUM）；无学名可留空跳过")
        elif lang == "zh":
            if latin:
                e.append("zh 模式 latin 必须为空串（中文排版不附学名）")
            if not season:
                e.append("zh 模式 season_line 不能为空（中文季节）")
    return e, w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    ap.add_argument("--strict", action="store_true", help="warning 也按致命处理")
    args = ap.parse_args()
    with open(args.brief, "r", encoding="utf-8-sig") as f:
        b = json.load(f)
    errors, warnings = brief_errors(b)
    print(f"== validate {args.brief} :: {b.get('id','?')} | source={b.get('source')} "
          f"| style={b.get('style')} | cast_size={b.get('cast_size')} ==")
    for x in warnings:
        print("  [WARN]", x)
    for x in errors:
        print("  [ERROR]", x)
    fatal = len(errors) > 0 or (args.strict and len(warnings) > 0)
    if fatal:
        print(f"RESULT: FAIL（{len(errors)} error / {len(warnings)} warning）")
        sys.exit(1)
    print(f"RESULT: PASS（{len(warnings)} warning，可进入 build）")
    sys.exit(0)


if __name__ == "__main__":
    main()
