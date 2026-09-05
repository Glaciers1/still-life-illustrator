# 更新日志（Changelog）

完整版（Full Edition）的所有重要变更记录于此；轻量版（Lite Edition）的变更见 [lite 分支的 CHANGELOG.md](https://github.com/Glaciers1/still-life-illustrator/blob/lite/CHANGELOG.md)。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。当前最新为 **v3.0.1**。

## [v3.0.1] - 2026-09-05 · 当前

### 修复
- `panel/_run_panel.vbs`：中文（GBK）系统的 wscript 报编译错误 800A0400 —— 重写为纯 ASCII 自定位启动器（pythonw 按环境变量 → 豆包沙箱最新 base → PATH 三级解析）
- `scripts/prep_images.py`：补上缺失的 `import os`（此前 `--cache-dir` 一用即崩）
- README / SKILL.md 版本号由 v1.2.0 更正；LICENSE 署名更新为 Glaciers1

### 变更
- 色卡文档全部更正为与 `color_palette.py` 实际参数一致（`--max-colors` / `--swatch-w` / `--swatch-h` / `--pos` / `--label` / `--margin-px` / `--font` / `--batch`），移除虚构的 `--shape` / `--num-colors` / `--sort` 与 brief `color_palette` 字段
- README 文件结构树与仓库实际内容逐项统一；SKILL.md 文件索引补 `skill_doctor.py`
- 全库 UTF-8 无 BOM + LF；新增 `outputs/.gitkeep`
- 面板本地服务安全加固：`/api/*` 增加 Host / Origin 校验（仅允许本机访问）

## [v3.0.0] - 2026-09-04

### 新增
- external LLM 协同模式（`director_dom.py` + `director-contract.md`）
- self-B 批量模式、HTML 可视化面板（`panel/`）、性能渲染档位（`performance-modes.md`）
- `--auto-creative --build` 一键流水线；`--cast-size` / `--container` / `--skip-validate` 参数
- `skill_doctor.py` 自诊断；`brief_history.py` / `convert_index.py` 工具
- GitHub Actions CI；跨平台标准化（LF / shebang / `.gitattributes`）

### 变更
- auto-creative 的 latin 行要求大写学名，无学名则跳过
- 全部脚本 `__version__` 统一为 3.0.0

### 修复
- `build_from_brief.py` 中文"结构"字段泄漏进英文 `pv_en`

## [v2.0.0] - 2026-08

### 新增
- 三种平等风格：S1 水彩蜡笔 / S2 叙事编排 / S3 色粉颗粒
- brief@1.1 规划-渲染协同格式；旬物索引 374 种
- 色卡后处理；`prep_images.py` 伪文字检测；参考图风格提取

## [v1.1.0]

- 初始公开发布：三风格、brief@1.1 规划-渲染协同、批量出图、旬物索引、色块后处理、伪文字检测

[v3.0.1]: https://github.com/Glaciers1/still-life-illustrator/releases/tag/v3.0.1
