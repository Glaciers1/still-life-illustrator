# 模式3：external 协同模式（LLM 直接生成 brief 数组）

功能版特有模式：由外部 LLM 按 `brief@1.1` schema 直接生成 brief JSON 数组，`director_dom.py` 批量落地为单独 brief 文件，再走 build → 生图 → 后处理。

## 输入

- `input_brief_array.json`：LLM 输出的 brief JSON 数组（可含多个主体）

## 执行命令

```bash
# 1. 批量落地 brief 数组（校验 + 去重 + 逐个落盘）
python scripts/director_dom.py --input input_brief_array.json --outdir ./output --skip-invalid --report

# 2. 批量拼装提示词
python scripts/build_from_brief.py --batch ./output --dry-run   # 先校验
python scripts/build_from_brief.py --batch ./output              # 生成 A/B 提示词

# 3. 生图 → prep_images 校正 → overlay_text 叠字（同模式1）
```

## director_dom.py 关键参数

| 参数 | 说明 |
|------|------|
| `--input` | JSON 数组文件（brief 数组或包裹对象） |
| `--page-text` | 页面文本文件（自动提取所有 brief） |
| `--merge` | 分批合并多个 JSON/页面文本，同 id 去重 |
| `--outdir` | 输出目录（required） |
| `--skip-invalid` | 校验失败的 brief 跳过不落地 |
| `--report` | 输出提取诊断报告（候选数/通过数/缺失id） |
| `--avoid-subjects` | 历史去重主体列表 |
| `--history-file` | 历史已用主体 JSON |

## 与 self-A 模式的区别

| 维度 | self-A 批量（模式2） | external 协同（模式3） |
|------|---------------------|----------------------|
| 骨架生成 | self_skeleton.py 自动生成 | 无，LLM 直接生成完整 brief |
| LLM 角色 | 补创意字段（pv_en/poem/latin） | 生成完整 brief 数组 |
| 校验时机 | self_merge 后 validate | director_dom 落地时 validate |
| 适用场景 | 批量标准化出图 | 自由创意、复杂编排 |

## 注意

- external 模式要求 LLM 输出严格符合 `brief@1.1` schema（见 `references/director/brief-schema.md`）
- `director-contract.md` 定义了 LLM 输出契约
- latin 必须为大写学名；无学名则留空，叠字时跳过 latin 行
