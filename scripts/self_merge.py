#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = "2.1.0"
"""
self_merge.py —— 把 LLM 补的创意字段合并回 self_skeleton.py 生成的骨架。

骨架里固定字段已填好，创意字段（views[].pv_en、text.poem、text.latin、text.title）是 TBD。
LLM 只需输出一个极紧凑的 JSON 数组（creative_template.json 格式），本脚本把它合并回骨架，
生成完整 brief@1.1，并自动跑 validate_brief 轻校验。

用法:
  python self_merge.py --skeleton-dir ./batch20 --creative ./batch20/creative_filled.json
  python self_merge.py --skeleton-dir ./batch20 --creative ./batch20/creative_filled.json --dry-run
  python self_merge.py --skeleton-dir ./batch20 --creative ./batch20/creative_filled.json --strict

创意字段格式（与 self_skeleton.py 输出的 creative_template.json 一致）:
  [
    {"id": "B001", "title": "BASQUE", "pv_en": {"A": "...90-160词...", "B": "..."},
     "poem": ["第一行", "第二行"], "latin": "BOS TAURUS"},
    ...
  ]
- title 可选，不填则保留骨架自动生成的标题
- latin 为 "TBD" 或空时保留 TBD（validate 会告警但放行）
- pv_en 两稿都必须填，否则该 brief 标记为失败
"""
import json, os, sys, argparse, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from validate_brief import brief_errors
except Exception:
    brief_errors = None


def load_creative(path):
    """加载创意字段 JSON，返回 dict[id] -> creative。"""
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, dict):
        # 支持 {"briefs": [...]} 格式
        data = data.get("briefs", [data])
    result = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        pid = item.get("id", "").strip()
        if pid:
            result[pid] = item
    return result


def merge_one(skeleton, creative):
    """把创意字段合并进骨架，返回合并后的 brief dict（新对象，不修改原骨架）。"""
    import copy
    b = copy.deepcopy(skeleton)

    # 标题（可选，不填保留骨架自动生成的）
    title = creative.get("title", "").strip()
    if title:
        b["text"]["title"] = title

    # pv_en（必须）
    pv = creative.get("pv_en", {})
    if isinstance(pv, dict):
        for v in b["views"]:
            tag = v.get("tag")
            val = pv.get(tag, "").strip()
            if val:
                v["pv_en"] = val
    elif isinstance(pv, str) and pv.strip():
        # 兼容：pv_en 是单个字符串，同时给 A/B（不推荐，但兼容）
        for v in b["views"]:
            v["pv_en"] = pv.strip()

    # 短诗（必须恰好 2 行）
    poem = creative.get("poem", [])
    if isinstance(poem, list) and len(poem) >= 2:
        b["text"]["poem"] = [str(poem[0]).strip(), str(poem[1]).strip()]
    elif isinstance(poem, str) and poem.strip():
        # 兼容：用换行分割
        lines = [l.strip() for l in poem.split("\n") if l.strip()]
        if len(lines) >= 2:
            b["text"]["poem"] = lines[:2]

    # 拉丁学名：无学名（空）则清空，build 跳过 latin 行；有值则必须为大写学名
    latin = creative.get("latin", "").strip()
    if latin:
        b["text"]["latin"] = latin.upper() if latin.upper() != "TBD" else "TBD"
    else:
        b["text"]["latin"] = ""

    # title_color（可选，LLM 可给）
    tc = creative.get("title_color", "").strip()
    if tc:
        b["text"]["title_color"] = tc

    # 删除骨架元信息（_skeleton 不是 brief-schema 标准字段）
    b.pop("_skeleton", None)

    # style_reason 从 auto 改为实际值
    if b.get("style_reason", "").startswith("auto-assigned"):
        b["style_reason"] = f"batch-balanced {b['style']} assignment"

    return b


def check_pv_en(b):
    """检查 pv_en 是否都填了且非 TBD，返回 (ok, message)。"""
    issues = []
    for v in b.get("views", []):
        tag = v.get("tag", "?")
        pv = str(v.get("pv_en", "")).strip()
        if not pv or pv == "TBD":
            issues.append(f"view {tag} pv_en 未填写")
        elif len(pv.split()) < 50:
            issues.append(f"view {tag} pv_en 仅 {len(pv.split())} 词（建议 90-160）")
    return (len(issues) == 0, "; ".join(issues))


def check_poem(b):
    """检查短诗是否填了。"""
    poem = b.get("text", {}).get("poem", [])
    if not isinstance(poem, list) or len(poem) != 2:
        return False, "poem 不是恰好 2 行"
    if any(not str(p).strip() or p.strip() == "TBD" for p in poem):
        return False, "poem 有未填写行(TBD)"
    return True, ""


def main():
    ap = argparse.ArgumentParser(description="self 创意字段合并器")
    ap.add_argument("--skeleton-dir", required=True, help="骨架目录（含 *_brief.json）")
    ap.add_argument("--creative", required=True, help="LLM 补好的创意字段 JSON")
    ap.add_argument("--dry-run", action="store_true", help="只检查不写入")
    ap.add_argument("--strict", action="store_true", help="warning 也按失败处理")
    ap.add_argument("--outdir", default="", help="输出目录（默认=骨架目录，覆盖原文件）")
    args = ap.parse_args()

    skel_dir = os.path.abspath(args.skeleton_dir)
    outdir = os.path.abspath(args.outdir or skel_dir)
    os.makedirs(outdir, exist_ok=True)

    creative = load_creative(args.creative)
    if not creative:
        print("错误：创意字段 JSON 为空或格式不对。")
        sys.exit(1)

    # 找所有骨架 brief
    skel_files = sorted(p for p in glob.glob(os.path.join(skel_dir, "*_brief.json"))
                        if not p.endswith("_overlay.json"))
    if not skel_files:
        print(f"错误：骨架目录下没有找到 *_brief.json：{skel_dir}")
        sys.exit(1)

    ok, fail, missing = [], [], []
    for fp in skel_files:
        pid = os.path.splitext(os.path.basename(fp))[0].replace("_brief", "")
        try:
            with open(fp, "r", encoding="utf-8-sig") as f:
                skeleton = json.load(f)
        except Exception as ex:
            fail.append((pid, f"骨架 JSON 解析失败: {ex}"))
            continue

        if pid not in creative:
            missing.append(pid)
            fail.append((pid, "创意字段中未找到该 id"))
            continue

        try:
            merged = merge_one(skeleton, creative[pid])
        except Exception as ex:
            fail.append((pid, f"合并异常: {ex}"))
            continue

        # 创意字段完整性检查
        pv_ok, pv_msg = check_pv_en(merged)
        poem_ok, poem_msg = check_poem(merged)
        creative_issues = []
        if not pv_ok:
            creative_issues.append(pv_msg)
        if not poem_ok:
            creative_issues.append(poem_msg)

        # validate_brief 轻校验
        validate_errors, validate_warns = [], []
        if brief_errors is not None:
            validate_errors, validate_warns = brief_errors(merged)

        is_fail = bool(creative_issues) or bool(validate_errors)
        if args.strict and validate_warns:
            is_fail = True

        if is_fail:
            reasons = []
            if creative_issues:
                reasons.append("创意: " + "; ".join(creative_issues))
            if validate_errors:
                reasons.append("校验: " + "; ".join(validate_errors))
            if args.strict and validate_warns:
                reasons.append("strict警告: " + "; ".join(validate_warns))
            fail.append((pid, " | ".join(reasons)))
            continue

        # 写入
        if not args.dry_run:
            out_fp = os.path.join(outdir, f"{pid}_brief.json")
            with open(out_fp, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

        warn_str = f" ({len(validate_warns)} warn)" if validate_warns else ""
        ok.append((pid, f"合并成功{warn_str}"))

    # 摘要
    total = len(skel_files)
    print(f"\n===== 合并完成：成功 {len(ok)} / 失败 {len(fail)} / 总计 {total} =====")
    if args.dry_run:
        print("  [dry-run 模式，未写入文件]")
    print(f"\n--- 成功 ({len(ok)}) ---")
    for pid, msg in ok:
        print(f"  [OK]   {pid}  {msg}")
    if fail:
        print(f"\n--- 失败 ({len(fail)}) ---")
        for pid, why in fail:
            print(f"  [FAIL] {pid}  -> {why}")
    if missing:
        print(f"\n--- 创意字段缺失的 id ---")
        print(f"  {', '.join(missing)}")

    # 创意字段里有但骨架里没有的 id
    skel_ids = set(os.path.splitext(os.path.basename(p))[0].replace("_brief", "") for p in skel_files)
    extra_ids = [cid for cid in creative if cid not in skel_ids]
    if extra_ids:
        print(f"\n--- 创意字段中有但骨架中没有的 id（将被忽略）---")
        print(f"  {', '.join(extra_ids)}")

    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
