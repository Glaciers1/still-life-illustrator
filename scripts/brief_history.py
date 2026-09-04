#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brief_history.py —— 已出 brief 的轻量历史，用于批量时自动去重（主体/档位/风格/视角/标题）。

历史是一个 JSONL（每行一条摘要），默认放在【项目工作区】而非技能内，避免污染技能结构：
  路径优先级：--file 参数  >  环境变量 STILL_LIFE_HISTORY  >  当前工作目录/still_life_history.jsonl

用法:
  python brief_history.py add  <brief.json> [--file H.jsonl]   # 追加一条（同 id 自动去重）
  python brief_history.py recent [N] [--file H.jsonl]          # 打印最近 N 条（默认 8）
  python brief_history.py path                                 # 打印将使用的历史路径
起草新 brief 前先 `recent 8`，主体/档位/风格/视角对/标题任一高度重叠就换一项。
"""
import json, os, argparse, datetime


def default_path():
    return os.environ.get("STILL_LIFE_HISTORY") or os.path.join(os.getcwd(), "still_life_history.jsonl")


def summarize(b):
    """从一份 brief 提取去重所需的最小摘要。"""
    hero = b.get("hero", {})
    return {
        "id": b.get("id"),
        "ts": datetime.date.today().isoformat(),
        "season": b.get("season"),
        "hero_en": hero.get("en"), "hero_zh": hero.get("zh"),
        "cast_size": b.get("cast_size"), "style": b.get("style"), "lang": b.get("lang"),
        "views": [f"{v.get('tag')}:{(v.get('pv_en') or '')[:36]}" for v in b.get("views", [])],
        "title": (b.get("text") or {}).get("title"),
    }


def _read_all(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def cmd_add(args):
    path = args.file or default_path()
    with open(args.brief, "r", encoding="utf-8-sig") as f:
        b = json.load(f)
    rows = _read_all(path)
    nid = b.get("id")
    if any(r.get("id") == nid for r in rows):
        print(f"[skip] id={nid} 已在历史中，不重复追加（{path}）"); return
    rec = summarize(b)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[add] {nid} -> {path}（共 {len(rows)+1} 条）")


def cmd_recent(args):
    path = args.file or default_path()
    rows = _read_all(path)
    n = args.n or 8
    tail = rows[-n:]
    if not tail:
        print(f"历史为空：{path}"); return
    print(f"最近 {len(tail)} 条（来源 {path}）：")
    for r in tail:
        print(f"  {str(r.get('id')):6s} | {str(r.get('season')):6s} | {str(r.get('style')):3s} | cast {r.get('cast_size')} | "
              f"{str(r.get('hero_en')):22s} | {str(r.get('title')):14s} | {len(r.get('views', []))} views")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("add"); pa.add_argument("brief"); pa.add_argument("--file")
    pr = sub.add_parser("recent"); pr.add_argument("n", type=int, nargs="?"); pr.add_argument("--file")
    sub.add_parser("path")
    args = ap.parse_args()
    if args.cmd == "add":
        cmd_add(args)
    elif args.cmd == "recent":
        cmd_recent(args)
    else:
        print(default_path())

if __name__ == "__main__":
    main()
