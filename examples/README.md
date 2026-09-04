# Examples

功能版（v3.0.0）四种出图模式的可复现演示示例。

## 模式对比

| 模式 | 目录 | LLM 介入 | 命令数 | 适用场景 |
|------|------|----------|--------|----------|
| ① self 单张·顺滑档 | [`mode1_single/`](./mode1_single/) | 否 | 5 步 | 单主体精修，完整控制 brief |
| ② self-A 批量（骨架+LLM） | [`mode2_selfA_batch/`](./mode2_selfA_batch/) | 是（补创意） | 4 步 | 多主体批量，需差异化创意 |
| ③ external 协同（LLM 直出 brief） | [`mode3_external/`](./mode3_external/) | 是（完整 brief） | 3 步 | 自由创意、复杂编排 |
| ④ HTML 可视化面板 | `panel/` | 交互 | GUI | 可视化操作批量出图 |

## HTML 面板（功能版特有）

```bash
# 启动面板服务器
python panel/start_panel.py

# 或用 VBS 一键启动（Windows）
wscript panel/_run_panel.vbs
```

面板提供：选题管理、风格选择、批量生成、进度可视化、成品预览。配置见 `panel/panel_config.json`。

## 通用后处理（所有模式共用）

```bash
# 生图后：伪文字检测 + 比例校正
python scripts/prep_images.py --text-scan --ratio <ratio> --prefix <id> --out ./

# 叠字（主标题 + 短诗 + 季节行）
python scripts/overlay_text.py --batch ./ -o ./
```

## 渲染挡位

功能版支持快速档与正式档（见 `references/performance-modes.md`）。正式档为默认推荐（5.0pro / 2048 / 双稿）。

## 成品图

成品图由宿主 Agent 的 image 生成工具产出，未纳入本仓库以控制体积。
