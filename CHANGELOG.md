# 更新日志（Changelog）

轻量版（Lite Edition）的所有重要变更记录于此；完整版（Full Edition）的变更见 [main 分支的 CHANGELOG.md](https://github.com/Glaciers1/still-life-illustrator/blob/main/CHANGELOG.md)。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。当前最新为 **v2.1.1**。

## [v2.1.1] - 2026-09-05 · 当前

### 修复
- 移植完整版全套修复：`scripts/prep_images.py` 缺 `import os`（`--cache-dir` 崩溃）、README/SKILL.md 版本号更正

### 变更
- 色卡文档全部更正为与 `color_palette.py` 实际参数一致（移除虚构的 `--shape` / `--num-colors` / `--sort`）
- README 文件结构树与仓库实际内容逐项统一；SKILL.md 文件索引补 `skill_doctor.py`
- LICENSE 署名更新为 Glaciers1；全库 UTF-8 无 BOM + LF

## [v2.1.0] - 2026-09-04

### 新增
- `--auto-creative --build` 一键流水线（由 `quick_batch.py` 合并入 `self_skeleton.py`）
- `--cast-size`（auto/large/1-6）、`--container`（8 种容器）、`--skip-validate` 参数
- `skill_doctor.py` 自诊断（24 项）；`convert_index.py` 索引转换器；`brief_history.py` 历史去重
- CI 工作流（pytest + skill_doctor + flake8，Python 3.10–3.12）；跨平台合规（LF / shebang / `.gitattributes`）

### 变更（精简，BREAKING）
- 移除 external 来源模式：`source` 校验收紧为 `self`
- 移除 self-B 批量模式；移除 HTML 可视化面板（`panel/`）
- 移除 `quick_batch.py`（能力并入 `self_skeleton.py --build`）；移除快速渲染档（仅保留正式档 5.0pro / 2048 / 双稿）
- auto-creative 的 latin 行要求大写学名，无学名则跳过
- `creative_generator.py`：修复中文"结构"字段泄漏进英文 `pv_en`；新增 `extract_structure_size_en()`
- 全部脚本 `__version__` 统一为 2.1.0；文本文件统一 LF

### 移除
- `scripts/director_dom.py`、`scripts/quick_batch.py`
- `references/director-contract.md`、`references/performance-modes.md`
- `panel/` 目录（panel_pro.html / start_panel.py / _run_panel.vbs / panel_config.json）

## [v2.0.0] - 2026-08

### 新增
- 三种平等风格：S1 水彩蜡笔 / S2 叙事编排 / S3 色粉颗粒
- brief@1.1 规划-渲染协同格式；旬物索引 374 种
- 色卡后处理；`prep_images.py` 伪文字检测；参考图风格提取

## [v1.1.0]

- 初始公开发布：三风格、brief@1.1 规划-渲染协同、批量出图、旬物索引、色块后处理、伪文字检测

[v2.1.1]: https://github.com/Glaciers1/still-life-illustrator/releases/tag/v2.1.1
