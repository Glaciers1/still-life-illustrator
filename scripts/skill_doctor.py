#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_doctor.py —— still-life-illustrator 技能自诊断脚本。

一键检查技能健康度，输出红黄绿报告：
  1. 所有 .py 脚本语法检查 (ast.parse)
  2. 所有 .md 文档引用的文件是否存在（无悬空索引）
  3. 双副本 (Profile 1 / Default) MD5 一致性
  4. prompt-blocks.md 锚点完整性 (build_from_brief 依赖的 9 个块)
  5. 旬物索引条目数健康度 (应 >= EXPECTED_INDEX_ENTRIES=350)
  6. 关键脚本可导入性 (validate_brief / build_from_brief / creative_generator / self_skeleton / self_merge)
  7. brief-schema 与 validate_brief 字段一致性 (schema 中提到的字段 validate 是否检查)

用法:
  python skill_doctor.py
  python skill_doctor.py --json    # 输出 JSON 格式报告
  python skill_doctor.py --strict  # warning 也按失败处理

退出码: 0=全部通过(可带warning) / 1=有error
"""
import os, sys, ast, hashlib, re, glob, json, argparse

# 技能根目录（skill_doctor.py 位于 scripts/ 下，根目录是上一级）——按脚本自身位置推导，跨机器/跨用户可移植
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# build_from_brief 依赖的 prompt-blocks 锚点
REQUIRED_BLOCKS = ["PALETTE", "M1", "M2_EXTRA", "M3", "HERO", "CLUSTER", "EDGE", "TEXT_BLANK", "NO_TEXT"]

# 旬物索引期望条目数（当前 SSOT 为 374 种：春37/夏69/秋42/冬28/全年·常备198；阈值留余量防批量删条）
EXPECTED_INDEX_ENTRIES = 350


class Diagnostic:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def error(self, category, msg):
        self.errors.append((category, msg))

    def warn(self, category, msg):
        self.warnings.append((category, msg))

    def ok(self, category, msg):
        self.info.append((category, msg))

    def has_errors(self):
        return len(self.errors) > 0


def check_python_syntax(diag, skill_dir):
    """1. 所有 .py 脚本语法检查"""
    py_files = sorted(glob.glob(os.path.join(skill_dir, "scripts", "*.py")))
    if not py_files:
        diag.error("语法", "scripts 目录下没有找到 .py 文件")
        return
    for fp in py_files:
        name = os.path.basename(fp)
        try:
            ast.parse(open(fp, encoding='utf-8-sig').read())
            diag.ok("语法", f"{name} 语法OK")
        except SyntaxError as e:
            diag.error("语法", f"{name} 语法错误: 行{e.lineno}: {e.msg}")


# 诊断扫描时忽略的目录（运行时缓存/输出，不参与引用与双副本检查）
IGNORE_DIRS = {".pytest_cache", "__pycache__", ".git", ".cache"}


def _walk_prune(dirs):
    """os.walk 就地剪掉忽略目录。"""
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]


def check_md_references(diag, skill_dir):
    """2. 所有 .md 文档引用的文件是否存在"""
    md_files = []
    for root, dirs, files in os.walk(skill_dir):
        _walk_prune(dirs)
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))

    # 收集技能内所有文件名（用于引用检查）
    all_filenames = set()
    for root, dirs, files in os.walk(skill_dir):
        _walk_prune(dirs)
        for f in files:
            all_filenames.add(f)

    ref_pattern = re.compile(r'([a-zA-Z0-9_\-]+\.(?:md|py|json))')
    # 运行时生成文件/命名模式白名单（不是技能内引用，不算悬空）
    RUNTIME_WHITELIST = {
        'still_life_history.json', 'brief.json', 'batch1.json', 'batch2.json',
        'briefs_array.json', 'creative_template.json', 'creative_filled.json',
        'page_text.txt', 'batch_spec.json', 'subjects.txt',
        'render_status.json', 'render_status.jsonl',
        'used_subjects.json', 'prepared_subjects.json',
        'batch_summary.json', 'creative_library.json',
    }
    # 变更日志/版本说明中明确声明"已移除/已并入"的旧文件名（历史记录，非真实悬空引用）
    REMOVED_WHITELIST = {
        'quick_batch.py', 'start_panel.py', 'director-contract.md',
        'director_dom.py', 'panel_config.json', 'panel_pro.html',
        '_run_panel.vbs', 'performance-modes.md',
    }
    dangling = []
    for mf in md_files:
        rel = os.path.relpath(mf, skill_dir)
        content = open(mf, encoding='utf-8-sig').read()
        refs = set(ref_pattern.findall(content))
        for ref in refs:
            if ref in all_filenames or ref == 'SKILL.md' or ref in RUNTIME_WHITELIST or ref in REMOVED_WHITELIST:
                continue
            # 排除 *_brief.json / *_overlay.json 等命名模式（运行时输出）
            if ref.endswith('_brief.json') or ref.endswith('_overlay.json') or ref.endswith('_A.txt') or ref.endswith('_B.txt') or ref.endswith('validation_failed.json'):
                continue
            dangling.append(f"{rel} -> {ref}")

    if dangling:
        diag.warn("引用", f"发现 {len(dangling)} 处可能的悬空引用: {dangling[:5]}")
    else:
        diag.ok("引用", f"全部 {len(md_files)} 个 .md 文件无悬空引用")


def check_dual_copy(diag, skill_dir):
    """3. 双副本 MD5 一致性（仅豆包双副本部署时检查；单副本环境自动跳过）"""
    # 另一副本 = 把路径中的 Default 段换成 Profile 1（反之亦然）
    if os.sep + "Profile 1" + os.sep in skill_dir:
        other = skill_dir.replace(os.sep + "Profile 1" + os.sep, os.sep + "Default" + os.sep)
    else:
        other = skill_dir.replace(os.sep + "Default" + os.sep, os.sep + "Profile 1" + os.sep)
    if other == skill_dir or not os.path.isdir(other):
        diag.ok("双副本", "未检测到双副本部署（单副本环境），跳过一致性检查")
        return

    all_files = []
    for root, dirs, files in os.walk(skill_dir):
        _walk_prune(dirs)
        for f in files:
            if f.endswith(('.py', '.md', '.json')):
                rel = os.path.relpath(os.path.join(root, f), skill_dir)
                all_files.append(rel)

    mismatch = []
    for rel in sorted(all_files):
        p1 = os.path.join(skill_dir, rel)
        p2 = os.path.join(other, rel)
        if not os.path.exists(p2):
            mismatch.append(f"{rel} (副本缺失)")
            continue
        h1 = hashlib.md5(open(p1, 'rb').read()).hexdigest()
        h2 = hashlib.md5(open(p2, 'rb').read()).hexdigest()
        if h1 != h2:
            mismatch.append(rel)

    if mismatch:
        diag.error("双副本", f"双副本不一致 ({len(mismatch)} 个文件): {mismatch[:5]}")
    else:
        diag.ok("双副本", f"双副本一致 ({len(all_files)} 个文件)")


def check_prompt_blocks(diag, skill_dir):
    """4. prompt-blocks.md 锚点完整性"""
    blocks_md = os.path.join(skill_dir, "references", "prompt-blocks.md")
    if not os.path.exists(blocks_md):
        diag.error("锚点", "prompt-blocks.md 不存在")
        return

    content = open(blocks_md, encoding='utf-8-sig').read()
    block_pattern = re.compile(r'<!--block:(\w+)-->')
    found_blocks = set(block_pattern.findall(content))

    missing = [b for b in REQUIRED_BLOCKS if b not in found_blocks]
    if missing:
        diag.error("锚点", f"prompt-blocks 缺少锚点: {missing}")
    else:
        diag.ok("锚点", f"prompt-blocks 全部 {len(REQUIRED_BLOCKS)} 个锚点完整")

    # 检查 M2_EXTRA 中的 [mood:] 占位符是否被正确处理
    if '[mood:' in content:
        diag.ok("锚点", "M2_EXTRA 含 [mood:] 占位符（build_from_brief 会替换）")


def check_seasonal_index(diag, skill_dir):
    """5. 旬物索引条目数健康度（JSON 优先，MD 为 SSOT）"""
    idx_md = os.path.join(skill_dir, "references", "seasonal-produce-index.md")
    idx_json = os.path.join(skill_dir, "references", "seasonal_produce_index.json")
    if not os.path.exists(idx_md) and not os.path.exists(idx_json):
        diag.error("旬物索引", "seasonal-produce-index.md 和 seasonal_produce_index.json 都不存在")
        return

    # 优先检查 JSON（脚本运行时实际使用的）
    if os.path.exists(idx_json):
        try:
            with open(idx_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            count = data.get("total", len(data.get("items", [])))
            if count >= EXPECTED_INDEX_ENTRIES:
                diag.ok("旬物索引(JSON)", f"JSON 条目数 {count} (>= {EXPECTED_INDEX_ENTRIES})")
            elif count >= 200:
                diag.warn("旬物索引(JSON)", f"JSON 条目数 {count} 偏少 (期望 >= {EXPECTED_INDEX_ENTRIES})")
            else:
                diag.error("旬物索引(JSON)", f"JSON 条目数 {count} 严重不足 (期望 >= {EXPECTED_INDEX_ENTRIES})")
        except Exception as ex:
            diag.error("旬物索引(JSON)", f"读取 JSON 失败: {ex}")

    # 同时检查 MD（SSOT，供人类编辑）
    if os.path.exists(idx_md):
        try:
            md_content = open(idx_md, encoding='utf-8-sig').read()
            entries = re.findall(r'\n###\s+', md_content)
            count = len(entries)
            if count >= EXPECTED_INDEX_ENTRIES:
                diag.ok("旬物索引(MD)", f"MD 条目数 {count} (>= {EXPECTED_INDEX_ENTRIES})")
            elif count >= 200:
                diag.warn("旬物索引(MD)", f"MD 条目数 {count} 偏少 (期望 >= {EXPECTED_INDEX_ENTRIES})")
            else:
                diag.error("旬物索引(MD)", f"MD 条目数 {count} 严重不足 (期望 >= {EXPECTED_INDEX_ENTRIES})")
        except Exception as ex:
            diag.error("旬物索引(MD)", f"读取 MD 失败: {ex}")


def check_imports(diag, skill_dir):
    """6. 关键脚本可导入性"""
    scripts_dir = os.path.join(skill_dir, "scripts")
    sys.path.insert(0, scripts_dir)
    key_modules = ["validate_brief", "build_from_brief", "creative_generator", "self_skeleton", "self_merge"]
    for mod in key_modules:
        try:
            __import__(mod)
            diag.ok("导入", f"{mod}.py 可正常导入")
        except Exception as e:
            diag.error("导入", f"{mod}.py 导入失败: {e}")
    sys.path.pop(0)


def check_schema_consistency(diag, skill_dir):
    """7. brief-schema 与 validate_brief 字段一致性"""
    schema_md = os.path.join(skill_dir, "references", "director", "brief-schema.md")
    validate_py = os.path.join(skill_dir, "scripts", "validate_brief.py")
    if not os.path.exists(schema_md) or not os.path.exists(validate_py):
        diag.warn("schema一致", "brief-schema.md 或 validate_brief.py 不存在，跳过")
        return

    schema_content = open(schema_md, encoding='utf-8-sig').read()
    validate_content = open(validate_py, encoding='utf-8-sig').read()

    # 检查 schema 中提到的顶层字段是否在 validate 中被检查
    schema_fields = re.findall(r'"(\w+)":\s*"', schema_content)
    key_fields = ["id", "season", "style", "ratio", "lang", "hero", "views", "text", "cast_size", "source"]
    unchecked = []
    for f in key_fields:
        if f not in validate_content:
            unchecked.append(f)

    if unchecked:
        diag.warn("schema一致", f"validate_brief 可能未检查字段: {unchecked}")
    else:
        diag.ok("schema一致", f"brief-schema 与 validate_brief 关键字段一致 ({len(key_fields)} 个)")


def print_report(diag, as_json=False):
    """输出诊断报告"""
    if as_json:
        report = {
            "errors": [{"category": c, "message": m} for c, m in diag.errors],
            "warnings": [{"category": c, "message": m} for c, m in diag.warnings],
            "info_count": len(diag.info),
            "status": "FAIL" if diag.errors else "PASS"
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print("=" * 60)
    print("  still-life-illustrator 技能自诊断报告")
    print("=" * 60)

    # 按类别分组
    categories = {}
    for c, m in diag.info:
        categories.setdefault(c, []).append(("OK", m))
    for c, m in diag.warnings:
        categories.setdefault(c, []).append(("WARN", m))
    for c, m in diag.errors:
        categories.setdefault(c, []).append(("ERROR", m))

    for cat in sorted(categories.keys()):
        print(f"\n--- {cat} ---")
        for level, msg in categories[cat]:
            icon = {"OK": "✅", "WARN": "⚠️", "ERROR": "❌"}[level]
            print(f"  {icon} {msg}")

    print("\n" + "=" * 60)
    total = len(diag.info) + len(diag.warnings) + len(diag.errors)
    status = "❌ FAIL" if diag.errors else "⚠️ PASS(with warnings)" if diag.warnings else "✅ ALL PASS"
    print(f"  总计: {total} 项 | 通过: {len(diag.info)} | 警告: {len(diag.warnings)} | 错误: {len(diag.errors)}")
    print(f"  状态: {status}")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser(description="still-life-illustrator 技能自诊断")
    ap.add_argument("--json", action="store_true", help="输出 JSON 格式报告")
    ap.add_argument("--strict", action="store_true", help="warning 也按失败处理")
    ap.add_argument("--skill-dir", default=SKILL_DIR, help="技能目录（默认为本脚本所在技能）")
    args = ap.parse_args()

    diag = Diagnostic()
    skill_dir = args.skill_dir

    if not os.path.exists(skill_dir):
        print(f"错误：技能目录不存在: {skill_dir}")
        sys.exit(1)

    check_python_syntax(diag, skill_dir)
    check_md_references(diag, skill_dir)
    check_dual_copy(diag, skill_dir)
    check_prompt_blocks(diag, skill_dir)
    check_seasonal_index(diag, skill_dir)
    check_imports(diag, skill_dir)
    check_schema_consistency(diag, skill_dir)

    print_report(diag, as_json=args.json)

    failed = diag.has_errors() or (args.strict and len(diag.warnings) > 0)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
