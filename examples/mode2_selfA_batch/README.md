# 模式2：self-A 批量（骨架脚本 + LLM 补创意）

批量出图模式：self_skeleton 生成多主体骨架 → LLM 补创意（标题/视角/短诗/学名）→ self_merge 合并 → build 批量拼装。

## 选题清单（batch size=2）

| ID | 主体 | 风格 | 质感 | 季节 |
|----|------|------|------|------|
| B001 | 巴斯克芝士蛋糕 | S1 水彩蜡笔 | Lush | 初冬 |
| B002 | 阳光玫瑰葡萄 | S3 色粉颗粒 | Bountiful | 初夏 |

## 执行命令

```bash
# 1. 生成骨架（含 creative 空模板）
python scripts/self_skeleton.py --names "巴斯克芝士蛋糕,阳光玫瑰葡萄" --batch-size 2 --outdir ./skeleton

# 2. LLM 补创意：将 skeleton_creative_template.json 填为 creative_filled.json
#    （填写英文标题、A/B 差异化 pv_en、短诗两行、大写学名或留空）

# 3. 合并骨架与创意
python scripts/self_merge.py --skeleton-dir ./skeleton --creative creative_filled.json --outdir ./

# 4. 批量拼装提示词
python scripts/build_from_brief.py --batch ./ --dry-run   # 先校验
python scripts/build_from_brief.py --batch ./              # 生成 4 份提示词

# 5. 生图 → prep_images 校正 → overlay_text 叠字（同模式1）
```

## 功能版 self_skeleton 额外参数

| 参数 | 说明 |
|------|------|
| `--spec` | 批次选题清单 JSON（含全局约束） |
| `--auto-subjects` | 无主体输入时自动从旬物索引 374 条随机选择 |
| `--avoid-subjects` | 历史去重主体列表 |
| `--history` | 历史已用主体 JSON（自动排除+重复警告） |
| `--title-style` | 标题排法：auto/normal/italic/wave/arch/scatter |

## 关键文件

| 文件 | 说明 |
|------|------|
| `skeleton_creative_template.json` | self_skeleton 输出的创意空模板 |
| `creative_filled.json` | LLM 补创意后的完整文件 |
| `B001_brief.json` / `B002_brief.json` | self_merge 合并后的完整 brief |
| `B001_A_prompt.txt` ~ `B002_B_prompt.txt` | 4 份生图提示词 |
| `B001_overlay.json` / `B002_overlay.json` | 叠字配置 |

## LLM 补创意要点

- **title**：英文大写标题（如 BASQUE BURN）
- **pv_en**：A/B 两稿视角差异化描述（90-130 词，含 exactly N）
- **poem**：两行短诗（英文，与主题呼应）
- **latin**：大写学名（如 VITIS VINIFERA）；无准确学名则留空，叠字时跳过 latin 行
