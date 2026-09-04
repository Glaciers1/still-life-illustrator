# 规划-渲染协同流程（Director Workflow · 执行端唯一 SOP）

> 本文件是执行端（本技能）跑"先 brief 后渲染"的**唯一标准操作流程**，覆盖 self（唯一来源，本技能内部起草）的全流程：起草 → 校验 → 拼装 → 出图 → 叠字 → 交付，以及批量模式与历史去重。
> **self 是唯一来源（离线可用、无需任何外部模型）**；external 扩展模式已随 v2.1.0 精简移除，本文件不再描述。
> 相关文件：规范 `brief-schema.md`；脚本 `scripts/validate_brief.py`、`scripts/build_from_brief.py`、`scripts/self_skeleton.py`、`scripts/self_merge.py`、`scripts/creative_generator.py`。

## 0. 总览

```
用户输入
  └─ source=self ：内部起草 brief.json（六步，见 §2，默认离线可用）
                              │
                              ▼
              validate_brief.py（硬校验门，不过不进下一步）
                              ▼
              build_from_brief.py（本地公共段拼装：<id>_A.txt/_B.txt + <id>_overlay.json）
                              ▼
              同批双稿生图 → prep_images 校正 → Read 目检 → overlay_text 叠字 → 回读 → present 交付
```

## 1. 来源（self 唯一）

- 本技能按 §2 六步自起草 brief，**不依赖任何外部模型**，迁移到别的电脑照样跑。
- 产出统一为 source=`self` 的 brief@1.1，下游 validate/build/生图/叠字/交付完全一致，**不维护两套渲染逻辑**。

## 2. self 取数（唯一来源 · 离线可用）

### 2.1 自起草六步

1. **解析输入**：主体（唯一）、用户指定的风格/季节/语言/比例/氛围/状态叠加/档位；无指定比例默认 4:5，本批量任务常用 3:4。
2. **选题与事实**：主体或搭配在《旬物索引》（**JSON 优先** `seasonal_produce_index.json`，SSOT `seasonal-produce-index.md`）收录范围时，先查固有色/质感/结构/应季月份/搭配器皿/cuttable_states（可用状态叠加类型）；不熟悉的主体先核实，学名按 LAYOUT §6.5.2 查证、不臆造。
3. **抽样定方案（反套路，见 §2.2 抽样池）**：定 cast_size、style、A/B 视角与版式、标题排法、字体配对、配色；**先查历史去重清单（§6.3）再定**，命中就换。
4. **填 brief**：严格按 `brief-schema.md` 写出 JSON；每类数量确定、place 写清承载面、pv_en 两稿各 90–130 词且只写可变画面。
5. **过校验门**：`scripts/validate_brief.py brief.json`，报错就改到通过（不允许带病进 build）。
6. **渲染交付**：`build_from_brief.py` 出 A/B 提示词与叠字参数 → 同批双稿生图 → prep 校正 → 目检数量/档位/主体突出/物理着附 → overlay 叠字 → 回读 → present 交付。

### 2.2 抽样池（无指定时随机，不总选"最顺手"）

- **cast_size**：Solo 12% / Duo 18% / Standard 28% / Abundant 22% / Bountiful 12% / Lush 8%；题材可合理偏离（早春/侘寂/单品偏 Solo-Duo，秋收/丰宴偏 Abundant-Bountiful-Lush）。
- **style**：S1/S2/S3 平等，按题材倾向（单体大留白→S1；多物件故事→S2；颗粒复古→S3）并给一句话 style_reason。
- **视角对（A/B 必须明显不同）**：{90°正俯, 45°三分之三高角, 60°微俯, 0°平视, 微仰} 里抽两个不同向；版式 {居中对称, 三分偏心, 对角线, 80-20 极简} 两稿不同。
- **标题排法**：用户指定从其指定（写入 brief 的 text.title_style 并传递到 overlay）；无指定时 normal/italic/wave/arch/scatter 等概率（含 normal，不默认变形）；字体 serif/sans/kai/hand 按风格与语言，主/次字体必须不同（次=type）。
- **次文方位**：与主标题（上方居中）对角，按两稿元素实际空位分别定左上/右上/左下/右下。
- 随机应"轮换"而非"纯独立"：刻意让相邻批次在档位/风格/视角/配色上拉开差异。

### 2.3 交互档位（默认顺滑，可切最控）

- **顺滑档（默认）**：内部起草、不打断用户，直接出图；交付时附一行 brief 摘要（季节/主体/档位/风格/双视角/标题）。
- **静默档（批量渲染默认，用户说"静默"/"不要中间过程"时自动切）**：不输出中间过程和环节详情（骨架生成/校验/拼装/生图/目检/叠字等步骤只在内部执行，不逐行打印），只在批次结束时输出最终结果统计（成功/失败/跳过数量及详情，格式见 §5.1）；**仅当技能运行报错时才显示报错环节和错误信息**。正常完成不暴露内部流水线步骤。
- **最控档（用户说"先看方案/先给brief/确认再画"）**：先把 brief（或中文摘要）发给用户确认/修改，确认后再 build 生图。
- 用户随时可只改 brief 某字段（换风格/档位/标题/视角）后重渲染，不必从头描述。

## 3. 校验门 → 拼装（self 单源）

```powershell
# 1) 硬校验：字段/枚举/cast 自洽/双稿差异/数量/语言一致性/技术段污染；非零退出即打回
python scripts/validate_brief.py <工作区>\S00X_brief.json
# 2) 拼装：出 A/B 完整生图提示词与叠字参数（--outdir 可指定输出位置，默认与 brief 同目录）
python scripts/build_from_brief.py <工作区>\S00X_brief.json [--outdir <工作区>]
```
- 本地公共段唯一文字源头是 `references/prompt-blocks.md` 的 `<!--block:...-->` 锚点；`build_from_brief.py` 运行时直接解析它（**单一来源、不再维护第二份**），`--show-blocks` 可核对每段来源，仅当锚点损坏才回退脚本内置兜底。
- 拼装产物：`<id>_A.txt`、`<id>_B.txt`（喂 image_gen）、`<id>_overlay.json`（叠字参数）。

## 4. 异常处理

- **校验报错**：按 `brief_errors`/validate 输出逐项改，self 就自己改。**不带病 build。**
- **数量/档位/物理着附在成图阶段才暴露**：目检发现多画/少画、悬空、第二焦点，立即只重生问题那一稿（在 pv 基础上加强 `EXACTLY N ... do NOT add`），另一稿保留。
- **公共段疑似异常**：跑 `build_from_brief.py --show-blocks`，凡标 FALLBACK 的块说明 prompt-blocks 锚点缺失/损坏，修锚点即可（无需改脚本）。

## 5. 出图与交付（接 SKILL 标准流水线步骤 7–9）

- A/B 必须**同一次 image_gen 调用的同一 request_list**，只换 pv 段，公共段逐字一致。
- **批量生图分批策略**：当一批总张数 > 15（如 batch_size 15 × A/B = 30 张）时，image_gen 每次调用的 request_list 不超过 3 张，逐批提交，避免一次性上传过多队列请求导致服务器响应异常；总张数 ≤ 15 时按常规双稿同批提交即可。
- **质量锚点（长批次防退化）**：批量渲染时 `build_from_brief.py --batch` 默认每 5 份 brief 自动在提示词末尾注入 `QUALITY_ANCHOR` 质量校准段（简短重申主体突出/边缘柔化/无文字/物理着附核心约束），防止长批次模型对重复约束注意力下降导致质量退化。可用 `--quality-anchor-every N` 调整间隔（N<=0 关闭）；单张/小批次（<5张）不注入。
- `prep_images.py --text-scan` 直接传成图 URL（一步下载+校正+取色+伪文字辅助扫描）；Read 校正图目检：数量逐项实数、cast 档位符合、主体唯一最突出、配角向主体收拢无悬空/第二焦点、边缘与色彩守铁律、**画面无 AI 直出文字（NO_TEXT 全局否定段已由 build_from_brief.py 放在提示词最前面，执行端不再额外追加 no text 否定句；image_edit 场景必做伪文字检测，发现伪文字按 SKILL 步骤 8 自动重生一次，最多 2 次，超过则换构图/视角）**。
- `overlay_text.py` 两稿一条命令叠字（参数取自 `<id>_overlay.json`），Read 成品回读后 `present_files` 交付。
- **产物与目录约定**：
  - 规则/脚本只存在于技能内；每批 brief/prompt/overlay 等过程文件放**项目工作区**（如 `director_pipeline/` 或用户指定目录），不污染技能结构。
  - final 成图输出到技能 `outputs/`，**final 永久保留、绝不自动清理**；无字中间稿（下载原图、prep 校正稿）可在交付后删除，是否清理以用户当次要求为准（当前约定：中间过程稿由用户手动删，执行端不自动删）。

### 5.1 批量渲染自动重试 SOP（失败不整批重发，单张自愈）

批量渲染时任何一张失败都**不中断整批**，按以下规则单张自愈，连续失败上限后跳过并记录：

| 失败场景 | 检测方式 | 自动重试动作 | 重试上限 | 超过上限处理 |
|---|---|---|---|---|
| **渲染失败**（image_gen 报错/超时/返回空） | 工具返回错误或无 URL | 重试 1 次，重试时**换 pv_en 描述**：加强主体突出句、简化配角数量、去掉可能触发安全过滤的词 | 1 次 | 标记 SKIP，记录原因，继续下一张 |
| **伪文字命中**（prep_images --text-scan 检测到 ≥80% 置信文字区域） | prep_images 输出 [警告] | 自动重生 1 次：在 pv_en 末尾追加 `keep the reserved blank areas completely empty and texture-free, no marks no letters`，其余不变 | 2 次 | 换构图/视角后再重生 1 次，仍失败则标记 SKIP |
| **目检不合格**（数量错/档位错/主体不突出/悬空/第二焦点） | Read 校正图人工目检 | **只重生问题那一稿**（A 或 B），另一稿保留；在 pv 基础上加强约束：数量错加 `EXACTLY N ... do NOT add`，悬空加 `resting firmly on the surface with visible contact shadow`，主体不突出加 `hero occupies center frame, all props visibly smaller and receding` | 2 次 | 标记 SKIP，记录具体不合格项 |

**重试状态记录**（批量时必做，放项目工作区 `render_status.jsonl`，每行一条 JSON）：
```json
{"id":"B003","tag":"A","status":"retry","reason":"pseudo-text detected","attempt":1,"timestamp":"..."}
{"id":"B003","tag":"A","status":"ok","attempt":2,"timestamp":"..."}
{"id":"B007","tag":"B","status":"skip","reason":"render failed after 1 retry","attempt":1,"timestamp":"..."}
```

**批次结束统一报告**（不逐张打断用户）：
```
===== 批量渲染完成 =====
  总计: 20 brief × 2 稿 = 40 张
  成功: 38 张（其中 5 张经 1 次重试后成功）
  跳过: 2 张（B007_B 渲染失败 / B012_A 伪文字 2 次仍命中）
  跳过详情:
    - B007_B: render failed after 1 retry (image_gen timeout)
    - B012_A: pseudo-text detected after 2 retries,建议换构图后手动重渲
```

- 跳过的图**不整批重发**，只单独补发跳过的 id（用户确认后）。
- 重试时 A/B 两稿**独立计数**（A 失败不影响 B）。

## 6. 批量（一批 N 个 brief，默认 10，可选 2/5/10/15/20/30）

> 批量规模：`--batch-size 2|5|10|15|20|30`，默认 10。一批 = N 个主题、每个 A/B 两稿。**brief 生成阶段批量做掉，成图阶段仍逐份走完校验→出图→目检→叠字→交付**（依次交付，不一次堆多批成图）。

### 6.1 brief 批量生成（self 单源两条路径）

**路径 self-A：脚本骨架 + LLM 补创意（推荐，token 最省、创意最个性）**

三步流水线：选题清单 → self_skeleton.py 生成 N 份骨架（创意字段 TBD）+ creative_template.json → LLM 补全创意字段 → self_merge.py 合并回骨架 + 自动校验。

**步骤 1：生成骨架**
```powershell
# 方式一：选题清单 JSON（推荐，可带全局约束和英文名）
python scripts/self_skeleton.py --spec batch_spec.json --outdir <工作区>
# 方式二：简单文本，每行一个主体中文名（可含英文名逗号分隔）
python scripts/self_skeleton.py --subjects subjects.txt --batch-size 20 --outdir <工作区>
# 方式三：命令行直接列主体
python scripts/self_skeleton.py --names "巴斯克芝士蛋糕,马卡龙,可露丽" --outdir <工作区>
```
- 脚本自动分配 id（B001-B0NN）、按概率抽 cast_size 并保证批次内档位均衡、S1/S2/S3 风格均衡、春夏秋冬季节均衡、A/B 视角对明显不同、标题排法/字体/次文方位随机。
- 自动查《旬物索引》取固有色/应季/搭配，填充 palette 和 props 建议。
- 创意字段留 TBD：`views[].pv_en = "TBD"`、`text.poem = ["TBD","TBD"]`、`text.latin = "TBD"`、`text.title` 从主体英文名自动生成（可改）。
- 输出 `creative_template.json`：LLM 补创意的紧凑格式模板；终端打印紧凑摘要表 + 批次均衡统计。

**选题清单 JSON 格式：**
```json
{
  "batch_size": 20,
  "global": {"style": "auto", "lang": "en", "ratio": "3:4", "season": "auto"},
  "subjects": [
    {"name": "巴斯克芝士蛋糕", "en": "basque cheesecake"},
    {"name": "马卡龙", "en": "macaron"}
  ]
}
```
- `style`/`season` 设为 `"auto"` 时脚本批次均衡分配；设为具体值则全批固定。
- `subjects` 也可以是字符串列表（`["巴斯克芝士蛋糕", "马卡龙"]`），脚本自动用小写当英文名。

**步骤 2：LLM 补创意字段**
把 `creative_template.json` 发给 LLM，指令：
```
按 brief-schema.md 的 pv_en 写法（90-130词，只写可变画面 VIEW/HERO/SECONDARY/PROPS/BG/LIGHT/COMPOSE，不写技术段），
补全下面 JSON 数组中每个条目的 pv_en(A/B 两稿视角不同)、poem(两行短诗，由本图独有细节推导)、
latin(准确拉丁学名英文大写，拿不准填 TBD)。title 已自动生成，不满意可改。只输出补全后的 JSON 数组。
```
- LLM 输出的就是填好的 `creative_template.json` 格式，不需要输出完整 brief。
- 这一步 LLM 的输出量约为完整 brief 的 1/3（固定字段不再重复）。

**步骤 3：合并 + 校验**
```powershell
python scripts/self_merge.py --skeleton-dir <工作区> --creative <工作区>/creative_filled.json
```
- 把创意字段合并回骨架，生成完整 brief@1.1，覆盖原骨架文件。
- 自动检查 pv_en 是否填了且词数合理、poem 是否恰好两行、跑 validate_brief 轻校验。
- 输出成功/失败摘要表；失败的标注原因（pv_en 未填/校验错误等）。
- `--dry-run` 只检查不写入；`--strict` 把 warning 也当失败。

**路径 v2.0 快速：self_skeleton --auto-creative --build（免 LLM，一步出提示词）**

原 quick_batch 能力已并入 self_skeleton.py，跳过 LLM 补创意，由 CreativeGenerator（预制库优先 + 模板兜底）自动填充创意字段并直接拼装出可生图的提示词：
```powershell
# 一步：骨架 + 自动创意 + 拼装（产出 *_A.txt / *_B.txt / *_overlay.json / batch_summary.json）
python scripts/self_skeleton.py --names "栗子蛋糕,法棍" --auto-creative --build --outdir <工作区>
# 可固定档位与容器：
python scripts/self_skeleton.py --names "栗子蛋糕" --auto-creative --build --cast-size 3 --container bamboo --outdir <工作区>
# 不拼装、只要填好创意的 brief（再手动 build_from_brief）：
python scripts/self_skeleton.py --names "栗子蛋糕" --auto-creative --outdir <工作区>
```
- `--cast-size`：auto/large/1-6（默认 auto 均衡；large=Abundant~Lush 4-6 大档位）。
- `--container`：auto/ceramic/wood/bamboo/metal/glass/stone/fabric（写入 brief._container_override）。
- `--skip-validate`：拼装时跳过 brief 校验（默认过校验门）。
- 创意模板由 `creative_generator.py` 生成：主体在预制库 `references/creative_library.json` 命中则复用精修创意（仅换视角/构图），否则按季节短诗池 + 视角/构图/容器池 + 旬物索引质感/结构自动组装。
- **局限**：主体不在《旬物索引》时，模板退化为通用结构描述（无"多汁/酥脆"等精准刻画）；建议索引外主体用 `subjects.txt`"中文,英文"格式提供英文名，创意更精准。

### 6.2 批量校验 + 拼装（两条路径共用下游）

```powershell
python scripts/build_from_brief.py --batch <工作区>
```
- 一次性校验＋拼装全部 N 份 brief 的 A/B 提示词与 overlay 参数（有错只报告、不中断其余）。
- 输出紧凑摘要表（id/主体/风格/档位/季节/提示词词数）+ 批次均衡统计（档位/风格/季节分布）。
- 之后逐份生图时，下一份提示词早已备好——上一份在生图等待期间即可推进下一份的目检/叠字准备，把串行等待藏起来。

### 6.3 历史去重（批量时必做，脚本自动维护）

- 历史是一份 JSONL，默认放**项目工作区** `still_life_history.jsonl`（环境变量 `STILL_LIFE_HISTORY` 或 `--file` 可改路径；不写进技能目录）。
- **起草前**：`python scripts/brief_history.py recent 8` 回看最近 8 条；**主体、cast_size、风格、视角对、主色、标题措辞**任一高度重叠就换一项，优先换主体或档位。
- **每批交付后**：逐个 `python scripts/brief_history.py add <id>_brief.json` 追加一条（同 id 自动去重）。
- 标题/短诗禁用万能套话与最近已用句式（如反复出现的 "LATE SUMMER"、同一句式），由本图独有细节新拟。

### 6.4 批量效率对比

| 方式 | brief 生成轮次 | LLM 输出 token | 适用场景 |
|---|---|---|---|
| 逐个起草（旧） | N 次 | 约 N×完整 brief | 小批量（<5）、需要逐个确认 |
| self-A 骨架+补创意 | 2 次（骨架脚本+补创意） | 约 N×1/3 brief | 大批量、创意要个性 |
| v2.0 快速（--auto-creative --build） | 1 次（纯脚本） | 0（免 LLM） | 求快求稳、创意套路可接受 |

### 6.5 批量模式通用约定

- **批量规模**：`--batch-size 2|5|10|15|20|30`，默认 10。实际数量以主体列表为准，不一致时脚本提示。
- **批次均衡**：骨架生成器自动保证 cast_size/style/season/视角在批次内均衡分布，输出统计供核对。
- **历史去重**：批量起草前仍需 `python scripts/brief_history.py recent 8` 回看，批量交付后逐个 `add`。
- **下游不变**：无论 self-A 还是 v2.0 快速路径，落地后的 brief 都走完全相同的 `build_from_brief.py --batch → 生图 → prep → 目检 → overlay → 交付` 流水线。
