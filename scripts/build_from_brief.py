#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "3.0.0"
"""
build_from_brief.py —— 把 brief@1.1（external/self 同源）拼装成两条完整「无字」生图提示词 + 叠字参数。
【单一来源】公共技术段（PALETTE/M1/M2_EXTRA/M3/HERO/CLUSTER/EDGE/TEXT_BLANK/NO_TEXT）
运行时直接从 references/prompt-blocks.md 的 `<!--block:NAME-->` 锚点解析，不再维护第二份文字；
仅当模块库缺失或锚点损坏时回退内置 _FALLBACK 并告警。`--show-blocks` 查看每段来源（一致性自检）。
【两种模式】
  单份模式：python build_from_brief.py brief.json [--outdir DIR] [--skip-validate]
  批量模式：python build_from_brief.py --batch <目录> [--outdir DIR] [--skip-validate]
            遍历目录内所有 *_brief.json，一次校验+拼装全部 A/B 提示词与 overlay 参数，
            输出紧凑摘要表与批次均衡统计（批量并行编排，省去逐份串行等待）。
默认先跑 validate_brief.brief_errors，有致命错拒绝 build（--skip-validate 跳过）。
build_one(brief, outdir) 供其他脚本复用；build_batch(indir, outdir) 供批量复用。
用法:
    python build_from_brief.py brief.json [--outdir DIR] [--skip-validate] [--show-blocks]
    python build_from_brief.py --batch ./batch20 [--outdir ./prompts] [--skip-validate]
"""
import json, sys, os, argparse, re, glob, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from validate_brief import brief_errors
except Exception:
    brief_errors = None
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCKS_MD = os.path.normpath(os.path.join(HERE, "..", "references", "prompt-blocks.md"))
NEEDED = ["PALETTE", "M1", "M2_EXTRA", "M3", "HERO", "CLUSTER", "EDGE", "TEXT_BLANK", "NO_TEXT", "QUALITY_ANCHOR", "STATE_OVERLAY"]
_BLOCK_RE = re.compile(r"<!--block:(\w+)-->\s*`([^`]+)`", re.S)
# 应急兜底：仅当 prompt-blocks.md 缺失/锚点损坏时使用；权威文字以模块库锚点为准
_FALLBACK = {
 "PALETTE": "rich multi-hue palette; OVERALL middle-low saturation slightly grayed, vivid accent only about 10-15%, no neon",
 "M1": "naive picture-book watercolor with crayon/colored-pencil grain on textured cotton paper, simple FLAT color blocks; NO layered gradient, NO hatching; nearly flat even light with almost NO cast shadow; NO dark closed outline, bleeding watercolor edges; illustrative NOT photorealistic",
 "M2_EXTRA": "narrative editorial still-life staging, illustrative and painterly (NOT a photograph), objects held in/on a container, single directional light with a graphic cast shadow, clear depth, quiet morning mood",
 "M3": "soft pastel and oil-pastel still life on textured kraft-grain paper, built mainly from FLAT scumbled color blocks; NO closed dark outline; soft diffused near-flat light; hand-drawn warmth, NOT photorealistic",
 "HERO": "THE HERO is the unambiguous largest and most defined element at the visual center, strongest contrast (edges softened, not hard); every prop smaller, softer, subordinate; no second focal point",
 "CLUSTER": "the [same-kind items] form ONE tight main cluster — packed closely, touching and slightly overlapping, with at most one piece a short controlled step away (within 1-2 of its own size); NOT evenly spread, no far-flung pieces",
 "EDGE": "EDGE HIERARCHY: the hero itself is painted with SOFT feathered bleeding edges yet its shape and light-side contour stay clearly readable and strongest; every secondary object one level softer, background softest; NO crisp outline, NO dark edge",
 "TEXT_BLANK": "keep a clean empty horizontal band across the top center for a later title, and keep the [spot] corner as perfectly smooth, even, empty background wash identical to the background, with nothing drawn there",
 "NO_TEXT": "absolutely no text, no letters, no numbers, no watermark, no logo, NO frame, NO signature, absolutely NO TEXT on the image",
 "QUALITY_ANCHOR": "QUALITY REINFORCEMENT: hero largest most defined at center; secondary smaller softer receding with contact shadows no floating; edges soft feathered no hard outlines; blank areas empty no letters no marks; middle-low saturation with small vivid accents",
}


def load_blocks():
    found = {}
    try:
        txt = open(BLOCKS_MD, encoding="utf-8-sig").read()
        found = {k: " ".join(v.split()) for k, v in _BLOCK_RE.findall(txt)}
    except Exception as ex:
        print(f"[warn] 读取模块库失败({ex})，公共段回退内置兜底", file=sys.stderr)
    blocks, origin = {}, {}
    for k in NEEDED:
        if found.get(k):
            blocks[k], origin[k] = found[k], "file"
        else:
            blocks[k], origin[k] = _FALLBACK[k], "FALLBACK"
    return blocks, origin
BLOCKS, BORIGIN = load_blocks()
SUB_EN = {"左上":"upper-left","右上":"upper-right","左下":"lower-left","右下":"lower-right",
          "upper-left":"upper-left","upper-right":"upper-right","lower-left":"lower-left","lower-right":"lower-right"}
# 上方两处 y=26%：落在顶部主标题条带之下，避免次文与大标题同带交叠
# 状态叠加类型 -> 英文描述（用于 STATE_OVERLAY 块 [state_type] 替换）
STATE_TYPE_MAP = {
    "halved": "halved cross-section",
    "sliced": "sliced",
    "cubed": "cut into large pieces",
    "diced": "diced into small cubes",
    "julienned": "julienned into thin strips",
    "peeled": "peeled",
    "shelled": "shelled",
}

SUB_XY = {"左上":"24%,26%","右上":"76%,26%","左下":"22%,86%","右下":"78%,86%",
          "upper-left":"24%,26%","upper-right":"76%,26%","lower-left":"22%,86%","lower-right":"78%,86%"}


def medium(style):
    if style == "S2":
        # 替换 prompt-blocks 锚点中的 [mood: ...] 占位符，避免生图时占位符原文进提示词
        extra = BLOCKS["M2_EXTRA"].replace("[mood: quiet morning / cozy candlelit night / fresh summer]", "quiet morning mood")
        return BLOCKS["M1"] + " " + extra
    if style == "S3":
        return BLOCKS["M3"]
    return BLOCKS["M1"]


def cluster(en):
    return BLOCKS["CLUSTER"].replace("[same-kind items]", en)


def text_blank(sub_blank):
    # TEXT_BLANK 模板为 "keep the [spot] corner"，替换值只给方位名词（如 "upper-left"），
    # 避免拼出 "keep the at the upper-left corner" 这类病句
    return BLOCKS["TEXT_BLANK"].replace("[spot]", SUB_EN.get(sub_blank, "upper-left"))


def build_prompt(b, v, quality_anchor=False):
    # NO_TEXT 全局否定放最前（扩散模型对首尾 token 注意力高，否定前置+正面描述在后）
    parts = [BLOCKS["NO_TEXT"], medium(b.get("style", "S1")), BLOCKS["PALETTE"]]
    # 参考图风格注入：有 ref_style 字段且非空时，自动注入到 PALETTE 之后
    ref_style = (b.get("ref_style", "") or "").strip()
    if ref_style:
        # B4: 注入前清理——去首尾标点符号，转义双引号为单引号，避免提示词语法错误
        ref_style = ref_style.strip(",.;;:，。；：\n\r\t ")
        ref_style = ref_style.replace('"', "'").replace("\n", " ").replace("\r", "")
        # 压缩多余空格
        while "  " in ref_style:
            ref_style = ref_style.replace("  ", " ")
        parts.append(f"[reference style: {ref_style}]")
    parts += [v.get("pv_en", ""), BLOCKS["HERO"]]
    # 状态叠加：hero.states 非 whole 时注入 STATE_OVERLAY 块
    _states = (b.get("hero") or {}).get("states", "whole")
    _cut_keywords = ("halved", "sliced", "cubed", "diced", "julienned", "peeled", "shelled", "cut", "cross-section", "strip", "cube")
    if _states and any(kw in _states.lower() for kw in _cut_keywords):
        _hero_en = (b.get("hero") or {}).get("en", "subject")
        # hero.en 含中文时用 text.title（英文大写）代替，避免提示词出现中文
        _cjk = lambda s: any("一" <= c <= "鿿" for c in (s or ""))
        if _cjk(_hero_en):
            _title = (b.get("text") or {}).get("title", "")
            _hero_en = _title.lower() if _title and not _cjk(_title) else "subject"
        _state_key = "halved"
        for _k in STATE_TYPE_MAP:
            if _k in _states.lower():
                _state_key = _k
                break
        _so = BLOCKS["STATE_OVERLAY"].replace("[subject]", _hero_en).replace("[state_type]", STATE_TYPE_MAP[_state_key])
        parts.append(_so)
    try:
        cnt = int(b.get("hero", {}).get("count", 1))
    except Exception:
        cnt = 1
    if cnt >= 2:
        parts.append(cluster(b["hero"].get("en", "hero items")))
    # TEXT_BLANK 只负责预留叠字区域（已去掉 no text 重复表述）；NO_TEXT 已在开头全局覆盖
    parts += [BLOCKS["EDGE"], text_blank(v.get("sub_blank", "左上"))]
    if quality_anchor:
        parts.append(BLOCKS["QUALITY_ANCHOR"])
    return " ".join(p.strip() for p in parts if p and p.strip())


def build_overlay(b):
    t = b["text"]
    sub_lines = list(t.get("poem", [])) + ["", t.get("season_line", "")]
    latin = (t.get("latin", "") or "").strip()
    if latin and latin.upper() != "TBD":
        sub_lines.append(latin)
    per_view = {v["tag"]: {"sub_xy": SUB_XY.get(v.get("sub_blank", "左上"), "24%,26%"),
                           "title_pos": "top-center" if "居中" in v.get("title_blank", "上方居中") else v.get("title_blank", "top-center")}
               for v in b["views"]}
    return {"common": {"title": t["title"], "title_font": t.get("title_font", "serif"),
                       "title_style": t.get("title_style", "normal"),
                       "title_size_px": t.get("title_size_px", 120),
                       "subtitle_size_px": t.get("subtitle_size_px", 20),
                       "title_width": t.get("title_width", 0.30),
                       "title_color": t.get("title_color", ""), "subtitle_lines": sub_lines,
                       "subtitle_font": "type", "sub_ratio": t.get("sub_ratio", 0.25),
                       "sub_color": t.get("sub_color", ""), "lang": b.get("lang", "zh")},
            "views": per_view}


def build_one(b, outdir, pid=None, write=True, quality_anchor=False):
    """拼装一份 brief；write=True 时把 <pid>_A/_B.txt 与 _overlay.json 写到 outdir。返回 dict。quality_anchor=True 时末尾注入质量校准段。"""
    pid = pid or b.get("id", "brief")
    prompts = {v["tag"]: build_prompt(b, v, quality_anchor=quality_anchor) for v in b["views"]}
    overlay = build_overlay(b)
    if write:
        os.makedirs(outdir, exist_ok=True)
        for tag, p in prompts.items():
            with open(os.path.join(outdir, f"{pid}_{tag}.txt"), "w", encoding="utf-8") as f:
                f.write(p)
        with open(os.path.join(outdir, f"{pid}_overlay.json"), "w", encoding="utf-8") as f:
            json.dump(overlay, f, ensure_ascii=False, indent=2)
    return {"pid": pid, "prompts": prompts, "overlay": overlay}


def _write_failure_diag(outdir, pid, stage, reason, brief=None):
    """N2: 校验/拼装失败时落盘诊断文件 <pid>.validation_failed.json，
    避免失败原因只在控制台滚动丢失。注意命名不匹配 *_brief.json，不会被批量扫描重复拾取。
    - stage: json_parse / validate / build
    - reason: 错误字符串或列表
    - brief: 原始 brief（JSON 解析失败时为 None）
    返回诊断文件路径（写入失败返回空串）。"""
    from datetime import datetime
    try:
        os.makedirs(outdir, exist_ok=True)
        diag = {
            "pid": pid,
            "stage": stage,
            "errors": reason if isinstance(reason, list) else [str(reason)],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "brief": brief,
        }
        diag_fp = os.path.join(outdir, f"{pid}.validation_failed.json")
        with open(diag_fp, "w", encoding="utf-8") as df:
            json.dump(diag, df, ensure_ascii=False, indent=2)
        return diag_fp
    except Exception as ex:
        print(f"  [warn] 诊断文件写入失败: {ex}", file=sys.stderr)
        return ""


def _build_one_worker(args):
    """多进程 worker：处理单个 brief 的校验和拼装，返回 (status, data)。
    必须在模块级别定义，才能被 multiprocessing.Pool pickle。"""
    fp, outdir, pid, qa, skip_validate = args
    try:
        with open(fp, "r", encoding="utf-8-sig") as f:
            b = json.load(f)
    except Exception as ex:
        return ("fail", (pid, f"JSON 解析失败: {ex}", None))
    if not skip_validate and brief_errors is not None:
        errors, _ = brief_errors(b)
        if errors:
            return ("fail", (pid, "；".join(errors), b))
    try:
        res = build_one(b, outdir, pid=b.get("id", pid), quality_anchor=qa)
        words = ",".join(f"{t}={len(p.split())}w" for t, p in res["prompts"].items())
        hero_name = (b.get("hero") or {}).get("name", "?") if isinstance(b.get("hero"), dict) else "?"
        return ("ok", (res["pid"], hero_name, b.get("style", "?"), b.get("cast_size", "?"),
                       b.get("season", "?"), words))
    except Exception as ex:
        return ("fail", (pid, "build 异常: %s" % ex, b))


def build_batch(indir, outdir="", skip_validate=False, quality_anchor_every=5, dry_run=False, parallel=0, fail_fast=False):
    """批量拼装：遍历 indir 内所有 *_brief.json，一次校验+拼装全部 A/B 提示词与 overlay 参数。
    返回 (ok_list, fail_list)，ok_list 元素为 (pid, hero, style, cast_size, season, words_str)。
    输出紧凑摘要表与批次均衡统计。
    quality_anchor_every: 每 N 份 brief 注入一次质量校准段（默认5，<=0 关闭），防长批次质量退化。
    """
    indir = os.path.abspath(indir)
    outdir = os.path.abspath(outdir or indir)
    files = sorted(p for p in glob.glob(os.path.join(indir, "*_brief.json")))
    if not files:
        print(f"目录下没有 brief json：{indir}")
        return [], []
    ok, fail = [], []
    ok_count_idx = 0
    # 并行模式：多进程处理（parallel > 0 且文件数 > 5 时启用，避免小批量进程启动开销）
    if parallel > 0 and len(files) > 5 and not dry_run and not fail_fast:
        import multiprocessing as _mp
        print(f"  [并行模式] 使用 {parallel} 进程处理 {len(files)} 个 brief...")
        # 准备任务参数
        tasks = []
        for idx, fp in enumerate(files):
            pid = os.path.splitext(os.path.basename(fp))[0]
            qa = quality_anchor_every > 0 and ((idx + 1) % quality_anchor_every == 0)
            tasks.append((fp, outdir, pid, qa, skip_validate))
        # 多进程处理
        with _mp.Pool(processes=parallel) as pool:
            results = pool.map(_build_one_worker, tasks)
        for res in results:
            if res[0] == "ok":
                ok.append(res[1])
                ok_count_idx += 1
            else:
                fpid, freason, fbrief = res[1]
                fstage = "validate" if fbrief is not None else "json_parse"
                _write_failure_diag(outdir, fpid, fstage, freason, brief=fbrief)
                fail.append((fpid, freason))
    else:
        # 串行模式（默认）
        for fp in files:
            pid = os.path.splitext(os.path.basename(fp))[0]
            try:
                with open(fp, "r", encoding="utf-8-sig") as f:
                    b = json.load(f)
            except Exception as ex:
                reason = f"JSON 解析失败: {ex}"
                _write_failure_diag(outdir, pid, "json_parse", reason)
                fail.append((pid, reason))
                if fail_fast:
                    print(f"[fail-fast] 遇到首个失败即中止: {pid}")
                    break
                continue
            if not skip_validate and brief_errors is not None:
                errors, _ = brief_errors(b)
                if errors:
                    reason = "；".join(errors)
                    _write_failure_diag(outdir, pid, "validate", errors, brief=b)
                    fail.append((pid, reason))
                    if fail_fast:
                        print(f"[fail-fast] 遇到首个失败即中止: {pid}")
                        break
                    continue
            try:
                if dry_run:
                    # dry-run 模式：只校验，不拼装
                    hero_name = (b.get("hero") or {}).get("name", "?") if isinstance(b.get("hero"), dict) else "?"
                    ok.append((b.get("id", pid), hero_name, b.get("style", "?"), b.get("cast_size", "?"),
                               b.get("season", "?"), "DRY-RUN"))
                    ok_count_idx += 1
                else:
                    qa = quality_anchor_every > 0 and ((ok_count_idx + 1) % quality_anchor_every == 0)
                    res = build_one(b, outdir, pid=b.get("id", pid), quality_anchor=qa)
                    words = ",".join(f"{t}={len(p.split())}w" for t, p in res["prompts"].items())
                    hero_name = (b.get("hero") or {}).get("name", "?") if isinstance(b.get("hero"), dict) else "?"
                    ok.append((res["pid"], hero_name, b.get("style", "?"), b.get("cast_size", "?"),
                               b.get("season", "?"), words))
                    ok_count_idx += 1
            except Exception as ex:
                reason = "build 异常: %s\n%s" % (ex, traceback.format_exc())
                _write_failure_diag(outdir, pid, "build", reason, brief=b)
                fail.append((pid, reason))
                if fail_fast:
                    print(f"[fail-fast] 遇到首个失败即中止: {pid}")
                    break
    mode_label = "DRY-RUN（仅校验，未拼装）" if dry_run else f"输出目录 {outdir}"
    print(f"\n===== 批量预备完成：成功 {len(ok)} / 失败 {len(fail)}，{mode_label} =====")
    if ok:
        print(f"\n{'id':<6} {'主体':<14} {'风格':<5} {'档位':<12} {'季节':<6} {'提示词词数'}")
        print("-" * 70)
        _cs_names = {1: "Solo", 2: "Duo", 3: "Standard", 4: "Abundant", 5: "Bountiful", 6: "Lush"}
        for pid, hero, style, cs, season, w in ok:
            print(f"  {pid:<6} {str(hero)[:12]:<14} {style:<5} {_cs_names.get(cs, str(cs)):<12} {season:<6} {w}")
    if fail:
        print(f"\n--- 失败 ({len(fail)}) ---")
        for pid, why in fail:
            print(f"  [FAIL] {pid}  -> {why}")
    # 批次均衡统计
    if ok:
        from collections import Counter
        cs_names = {1: "Solo", 2: "Duo", 3: "Standard", 4: "Abundant", 5: "Bountiful", 6: "Lush"}
        cs_dist = Counter(cs_names.get(cs, str(cs)) for _, _, _, cs, _, _ in ok)
        style_dist = Counter(style for _, _, style, _, _, _ in ok)
        season_dist = Counter(season for _, _, _, _, season, _ in ok)
        print(f"\n--- 批次均衡统计 ---")
        print(f"  档位分布: {dict(cs_dist)}")
        print(f"  风格分布: {dict(style_dist)}")
        print(f"  季节分布: {dict(season_dist)}")
    fb = [k for k in NEEDED if BORIGIN[k] == "FALLBACK"]
    if fb:
        print("[warn] 公共段回退兜底：", fb)
    return ok, fail


def show_blocks():
    print(f"模块库: {BLOCKS_MD}")
    for k in NEEDED:
        print(f"[{BORIGIN[k]:8s}] {k:10s} {len(BLOCKS[k].split())} words | {BLOCKS[k][:70]}...")
    fb = [k for k in NEEDED if BORIGIN[k] == "FALLBACK"]
    print("全部来自 file，单一来源 OK" if not fb else f"!! 回退兜底的块: {fb}（请检查锚点）")


def main():
    ap = argparse.ArgumentParser(description="brief→A/B提示词+叠字参数（单份或批量）")
    ap.add_argument("brief", nargs="?", help="单份 brief.json（与 --batch 二选一）")
    ap.add_argument("--batch", help="批量模式：指定 brief 目录，遍历所有 *_brief.json 一次拼装")
    ap.add_argument("--outdir", default="", help="输出目录（单份默认=brief所在目录；批量默认=--batch目录）")
    ap.add_argument("--skip-validate", action="store_true", help="跳过 validate_brief 校验")
    ap.add_argument("--show-blocks", action="store_true", help="查看公共段来源（一致性自检）")
    ap.add_argument("--quality-anchor-every", type=int, default=5,
                    help="批量模式：每 N 份 brief 注入一次质量校准段（默认5，<=0 关闭），防长批次质量退化")
    ap.add_argument("--parallel", type=int, default=0,
                    help="批量模式多进程并行数（默认0=串行；>0时启用多进程，建议值=CPU核心数，30张以上批量推荐）")
    ap.add_argument("--dry-run", action="store_true",
                    help="只输出将处理的文件列表与校验结果，不实际拼装提示词（便于调试）")
    ap.add_argument("--fail-fast", action="store_true",
                    help="批量模式遇到第一个失败立即中止（默认失败继续：处理完其余 brief 后统一汇总，并为每个失败落盘 .validation_failed.json）")
    ap.add_argument("--rebuild", default="",
                    help="单张重渲染：从 --batch 目录中读取指定 id 的 brief，只重建该 id 的 A/B 提示词（如 --rebuild B003）")
    args = ap.parse_args()
    if args.show_blocks:
        show_blocks()
        return
    # D4: 单张重渲染模式（从批量目录中读取指定 id 的 brief）
    if args.rebuild:
        if not args.batch:
            print("错误：--rebuild 必须配合 --batch <目录> 使用")
            sys.exit(1)
        import glob as _glob
        # 精确匹配
        brief_path = os.path.join(args.batch, f"{args.rebuild}_brief.json")
        if not os.path.exists(brief_path):
            # 模糊匹配
            matches = sorted(_glob.glob(os.path.join(args.batch, f"*{args.rebuild}*_brief.json")))
            if matches:
                brief_path = matches[0]
                print(f"[提示] 精确匹配未找到，使用模糊匹配: {os.path.basename(brief_path)}")
            else:
                print(f"错误：目录 {args.batch} 中未找到 id={args.rebuild} 的 brief")
                sys.exit(1)
        with open(brief_path, "r", encoding="utf-8-sig") as f:
            b = json.load(f)
        if brief_errors is not None and not args.skip_validate:
            errors, warns = brief_errors(b)
            for x in warns:
                print("  [validate WARN]", x)
            if errors:
                for x in errors:
                    print("  [validate ERROR]", x)
                print("校验未通过，已拒绝 rebuild；修正 brief 后重试（或 --skip-validate 强制）。")
                sys.exit(1)
        outdir = args.outdir or args.batch
        res = build_one(b, outdir)
        print(f"[OK] 已重建 {args.rebuild} 的 A/B 提示词，输出目录: {outdir}")
        for tag, p in res["prompts"].items():
            print(f"\n===== PROMPT {tag} (words={len(p.split())}) =====\n{p}")
        print("\n===== OVERLAY ARGS =====")
        print(json.dumps(res["overlay"], ensure_ascii=False, indent=2))
        sys.exit(0)
    # 批量模式
    if args.batch:
        ok, fail = build_batch(args.batch, outdir=args.outdir, skip_validate=args.skip_validate,
                               quality_anchor_every=args.quality_anchor_every, dry_run=args.dry_run,
                               parallel=args.parallel, fail_fast=args.fail_fast)
        sys.exit(1 if fail else 0)
    # 单份模式
    if not args.brief:
        ap.error("缺少 brief.json（或用 --batch <目录> 批量模式，或用 --show-blocks 查看公共段）")
    with open(args.brief, "r", encoding="utf-8-sig") as f:
        b = json.load(f)
    if brief_errors is not None and not args.skip_validate:
        errors, warns = brief_errors(b)
        for x in warns:
            print("  [validate WARN]", x)
        if errors:
            for x in errors:
                print("  [validate ERROR]", x)
            print("校验未通过，已拒绝 build；修正 brief 后重试（或 --skip-validate 强制）。")
            sys.exit(1)
    if any(o == "FALLBACK" for o in BORIGIN.values()):
        print("[warn] 部分公共段回退兜底：", [k for k in NEEDED if BORIGIN[k] == "FALLBACK"], file=sys.stderr)
    outdir = args.outdir or os.path.dirname(os.path.abspath(args.brief))
    res = build_one(b, outdir)
    print("=== BRIEF META ===")
    for k in ["id", "source", "season", "style", "style_reason", "cast_size", "ratio", "lang"]:
        print(f"{k}: {b.get(k)}")
    print("hero:", b.get("hero")); print("secondary:", b.get("secondary")); print("palette:", b.get("palette"))
    for tag, p in res["prompts"].items():
        print(f"\n===== PROMPT {tag} (words={len(p.split())}) =====\n{p}")
    print("\n===== OVERLAY ARGS =====")
    print(json.dumps(res["overlay"], ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
