# Examples

三种出图模式的可复现演示示例。每种模式包含输入文件、执行命令、示例输出（提示词 + 叠字配置）。

## 模式对比

| 模式 | 目录 | LLM 介入 | 命令数 | 适用场景 |
|------|------|----------|--------|----------|
| ① self 单张·顺滑档 | [`mode1_single/`](./mode1_single/) | 否 | 5 步 | 单主体精修，完整控制 brief |
| ② self-A 批量（骨架+LLM） | [`mode2_selfA_batch/`](./mode2_selfA_batch/) | 是（补创意） | 4 步 | 多主体批量，需差异化创意 |
| ③ v2.0 快速（--auto-creative） | [`mode3_quick_auto/`](./mode3_quick_auto/) | 否 | 1 步 | 快速批量，免 LLM 离线出图 |

## 通用后处理（三模式共用）

```bash
# 生图后：伪文字检测 + 比例校正
python scripts/prep_images.py --text-scan --ratio <ratio> --prefix <id> --out ./

# 叠字（主标题 + 短诗 + 季节行）
python scripts/overlay_text.py --batch ./ -o ./
```

## 成品图

成品图由宿主 Agent 的 image 生成工具产出（每张约 6-7MB），未纳入本仓库以控制体积。
各模式 README 中描述了成品构图与效果。
