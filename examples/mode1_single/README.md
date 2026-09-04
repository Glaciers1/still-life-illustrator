# 模式1：self 单张·顺滑档

最基础的出图模式：一份 brief → 校验 → 拼装 A/B 双稿提示词 → 生图 → 校正 → 叠字。

## 输入

- `input_brief.json`：草莓静物 brief（S1 水彩蜡笔 / Standard 容器 / 春 / 4:5 / en）

## 执行命令

```bash
# 1. 校验 brief
python scripts/validate_brief.py input_brief.json

# 2. 拼装 A/B 双稿提示词
python scripts/build_from_brief.py input_brief.json --out ./

# 3. 生图（由宿主 Agent 的 image 工具执行，使用 output_A_prompt.txt / output_B_prompt.txt）

# 4. 伪文字检测与比例校正
python scripts/prep_images.py --text-scan --ratio 4:5 --prefix M1 --out ./

# 5. 叠字（主标题 + 短诗 + 季节）
python scripts/overlay_text.py --batch ./ -o ./
```

## 输出

| 文件 | 说明 |
|------|------|
| `output_A_prompt.txt` | A 稿生图提示词（~720 词，90° 正俯视居中对称） |
| `output_B_prompt.txt` | B 稿生图提示词（~716 词，45° 三分之三高角对角线） |
| `output_overlay.json` | 叠字配置（标题位置、短诗、季节行、字体） |

## 成品效果

- A 稿：90° 正俯视，草莓居中对称，大留白，标题上方居中
- B 稿：45° 高角，草莓对角线构图，标题上方居中

> 成品图由宿主 Agent 的 image_gen 工具生成，未纳入本仓库（每张约 6-7MB）。
