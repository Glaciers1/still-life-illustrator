# 模式3：v2.0 快速（--auto-creative --build）

免 LLM 的一步出图模式：一条命令完成骨架 + 自动创意填充 + 批量拼装，直接生成可生图的提示词。

## 输入

- `subjects.txt`：选题清单，格式 `中文,英文`（每行一个主体）

```
牛油果,Avocado
山竹,Mangosteen
```

> 英文名为可选但推荐；省略时技能会用质感关键词映射兜底（可能回退为 "still life subject"）。

## 执行命令

```bash
# 一条命令：骨架 + auto-creative + build，batch size=2
python scripts/self_skeleton.py --subjects subjects.txt --batch-size 2 --auto-creative --build --out ./

# 后续：生图 → prep_images 校正 → overlay_text 叠字（同模式1）
```

## 可选参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `--cast-size` | auto / large / 1-6 | auto |
| `--container` | 8 种容器（bowl/plate/basket/...） | auto |
| `--skip-validate` | 跳过 brief 校验 | off |

## 输出

| 文件 | 说明 |
|------|------|
| `Q001_brief.json` / `Q002_brief.json` | 自动填充的完整 brief |
| `Q001_A_prompt.txt` ~ `Q002_B_prompt.txt` | 4 份生图提示词 |
| `Q001_overlay.json` / `Q002_overlay.json` | 叠字配置 |

## auto-creative 行为说明

- 创意字段由 `creative_generator.py` 自动填充（预制库优先 + 模板兜底）
- **latin 行**：仅当旬物索引中有大写学名时才生成；无学名则留空，叠字时跳过 latin 行（不再用小写英文名兜底）
- 无需 LLM 介入，完全离线可用
