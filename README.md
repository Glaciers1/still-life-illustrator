# Still Life Illustrator · 静物插画生成技能

把水果、美食、果盘、酒杯酒瓶、餐具器物、花植、电商产品等静态对象，画成带主标题、短诗与季节/学名、大留白的杂志风静物插画或海报。支持参考图风格提取、同主体多视角变体、先规划后渲染的 brief 协同模式，以及批量出图。

## 版本信息

**当前版本：v2.1.0**（2026-09-04）· 许可证：MIT（见 `LICENSE`）

## 变更日志

### v2.1.0（2026-09-04）—— 精简版
1. **移除 external 扩展模式**：删除 `director-contract.md`（外部 LLM 契约）与 `scripts/director_dom.py`，brief 来源统一为 self（`validate_brief.py` 的 source 校验收紧为 `self`）。
2. **移除 self-B 批量路径**：批量生成收敛为 self-A（骨架+LLM 补创意）与 v2.0 快速（`--auto-creative --build`）两条。
3. **移除 HTML 可视化面板**：删除 `panel/` 目录（panel_pro.html / start_panel.py / _run_panel.vbs / panel_config.json），不再需要面板服务器与计划任务常驻。
4. **合并 quick_batch.py 到 self_skeleton.py**：`--build`（一步拼装）、`--cast-size`（auto/large/1-6）、`--container`（8 种容器）、`--skip-validate` 并入 `self_skeleton.py`，删除 `quick_batch.py`。
5. **渲染档位仅保留正式档**：移除快速档（seedream_4.5 / 1536 / 单稿），统一默认 `seedream_5.0_pro` / 长边 2048 / 双稿。
6. **保留**：self 单张（顺滑/最控）、self-A 批量、v2.0 快速路径、全部输入方式（文本/参考图单张/参考图批量）、全部后处理（叠字/校正/色块/历史去重）、正式渲染档位。

### v2.0.0（2026-09-04）—— 前置流程优化版
1. **新增 `scripts/creative_generator.py`**：预制创意库 + 模板自动生成器。预制库优先查询，查询不到时用结构化模板自动生成 pv_en/poem/latin/title，完全跳过 LLM 补创意环节。
2. **修改 `scripts/self_skeleton.py`**：新增 `--auto-creative` 参数，生成骨架时自动调用 CreativeGenerator 填充创意字段（pv_en/poem/latin/title），不再留 TBD。版本号升级到 v2.0.0。
3. **新增 `scripts/quick_batch.py`**：快速批量出图前置脚本，整合 `self_skeleton` + `creative_generator` + `build_from_brief` 为一步，直接生成 `*_A.txt` / `*_B.txt` / `*_overlay.json`，可直接用于 image_gen。
4. **面板默认值确认**：风格（auto 批次均衡）、组合档位（auto 按概率抽样）、容器承载（auto 随机选择）均保持默认 auto。
5. **中文主体名自动检测**：creative_generator.py 自动检测中文主体名，根据旬物索引质感关键词映射为英文替代（如 creamy dessert / crispy pastry / juicy fruit），避免提示词出现中文。
6. **前置流程对比**：
   - 旧流程：self_skeleton → LLM补创意(多轮对话) → self_merge → build_from_brief → 生图（5步，约需多轮对话）
   - 新流程：quick_batch（或 self_skeleton --auto-creative + build_from_brief）→ 生图（2-3步，无需LLM补创意）

### v1.2.0（2026-09-04）—— 封装版
1. 新增 MIT LICENSE 授权许可文件
2. 更新 README.md 和 SKILL.md 版本信息与变更日志
3. 清理临时文件（outputs/、测试缓存、临时脚本）
4. 验证技能完整性（37个关键文件全部存在，7个核心脚本 --help 可运行）
5. 打包为 zip（still-life-illustrator-v1.2.0.zip，44文件，12.05 MB）

---

## 一分钟上手

**三步：① 说主体 → ② 选风格（不选自动挑）→ ③ 收到两张成品。**

> 示例：帮我画一组阳光玫瑰葡萄，Style-1 水彩风，出两张。

你会得到 **两张视角和排版都不同** 的插画，带主标题、一句短诗以及季节与拉丁学名两行小字，可直接保存使用。

### 指令公式

> **【主体】＋【风格】（可省）＋【氛围/场景】（可省）＋【文字语言】（可省）＋【其他要求】（可省）**

只有"主体"是必须的。例如：
- "画一颗牛油果，色粉油画棒风"
- "一瓶红酒加酒杯，暗调、藏蓝背景，高级一点"
- "把这张照片画成水彩插画"（同时发图）
- "画一篮草莓，中文标题"

---

## 三种风格

| 你想要的感觉 | 选哪个 |
|---|---|
| 温柔手绘、治愈手账/绘本感，水彩+蜡笔 | **Style-1** 水彩蜡笔 |
| 杂志大片、产品故事感、有光影和场景氛围 | **Style-2** 叙事编排 |
| 色粉/油画棒、纸面颗粒、复古温暖 | **Style-3** 色粉颗粒 |

选择困难就别选——会根据主体挑最合适的一种，并说明理由。也可以发一张喜欢的图，照着它的感觉来（自定义风格）。

---

## 你可以自由调整的一切

- **张数与视角**：默认两张、视角和排版各不相同；可指定俯视/平视/45°/仰视，或多要几张。
- **文字**：
  - 主标题默认是主体名，由后期排版叠入、字形可控；
  - 配一句短诗，空一行再附季节小字：英文排版为全大写季节+拉丁学名两行；中文排版只放一行中文季节、不附学名；也可自己给定文字；
  - 想要中文就说"用中文"。
- **颜色与背景**：默认干净浅纸色；想要深色背景直接说（藏蓝/暖深棕/墨绿/炭灰），也可指定色调。
- **主体状态**：默认最自然的单一状态；想看"整颗+切开"同框就明说。
- **画面丰盛度**：元素多少由你定——可只画单一主体（极简大留白），也可要 3–4 类、最多 5 类的丰盛组合；不指定时会轮换、不会每张都固定配两三样；无论几类，主体始终最大最突出。
- **参考照片重绘**：发图给我，会先分析配色、构图、笔触、字体，再按主体重画。
- **写实程度**：默认"色块概括、神似即可"；想更饱满说"颗粒饱满、层次多些"，想更简练说"再抽象一点、少笔触"。

---

## 进阶功能

### 规划-渲染协同模式（brief 先行）

把"创意规划"与"渲染执行"解耦：先产出一份结构化 **brief@1.1**（选物/数量/档位/双视角/文字/每稿可变画面段），过校验门后由脚本确定性补技术段再出图。比直接手写长 prompt 更可控、可复现、可只改一字段重渲染。

单一来源：

| 来源 | 说明 |
|---|---|
| **self（唯一）** | 技能自起草 brief，不依赖任何外部模型，离线可用、迁移到别的电脑照样跑；external 扩展模式已随 v2.1.0 移除 |

统一下游：`validate_brief.py` 硬校验门 → `build_from_brief.py` 拼装提示词 → 接标准出图流程。

### 批量出图

一批生成 N 个主题的插画，默认 10，可选 2/5/10/15/20/30。批量模式把固定字段交给脚本、LLM 只补创意，token 消耗降到约 1/3。

两条批量路径（self 单源）：
- **self-A（推荐，创意最个性）**：`self_skeleton.py` 选题清单→N 份骨架（创意字段 TBD）→ LLM 补创意 → `self_merge.py` 合并+自动校验
- **v2.0 快速（免 LLM）**：`self_skeleton.py --auto-creative --build` 一步完成骨架+自动创意+拼装（原 quick_batch 能力已并入本脚本）

落地后统一走 `build_from_brief.py --batch <目录>` 一次性校验+拼装全部提示词，输出批次均衡统计。

### 参考图风格提取与 ref_style

有参考图时，`inspect_image.py` 分析尺寸/比例/主色/边缘色/风格倾向；多张参考图时第一张定版式、其余定风格。批量场景下可在 brief 中加 `ref_style` 字段，`build_from_brief.py` 会自动在提示词中注入参考风格描述，保持整批风格统一。

### 伪文字检测 + 自动重生

image_edit（有参考图）场景下，生图可能冒出伪手写文字、装饰横线或角框。`prep_images.py --text-scan` 做启发式伪文字辅助扫描（边缘密度+高对比度块+横向排列特征综合评分），配合 AI 目检主检测；发现伪文字后自动重生一次（加强无字约束提示词），最多 2 次，超过则换构图/视角。

### 色块后处理（可选）

从成品图提取 2–6 种主色，渲染方形或条形色带并标注颜色名，作为配色参考卡。**纯 PIL 实现，颜色名来自内置 `color_names.json`（168 个公认英文颜色名）最近邻匹配，禁止模型生成颜色名。**

触发：说"加色卡/配色板/提取颜色/color palette"时，在叠字完成后对 final 图执行；不点名则不做。

参数：
- `--num-colors`：2–6（默认 5）
- `--shape`：square 方形（宽=高，间距=自身宽×1.5）/ bar 条形（高:宽=0.618 黄金比，间距=0 拼接）
- `--sort`：brightness 明→暗左→右 / saturation 高饱和→低饱和 / none
- `--pos`：top 顶部 / bottom 底部 / auto 自动找低方差空白区
- `--label`：name 颜色名 / hex / hsl / none
- `--batch <目录>`：批量处理目录下 `*_final.png`，输出 `*_palette.png`

规则：>3 个色块自动分两排；色块只放背景空白区，不压主体/次元素；颜色名用打印机字体（type=Courier），默认英文；色块高度占版面 6%（可调）。

---

## 脚本工具（scripts/）

| 脚本 | 用途 |
|---|---|
| `validate_brief.py` | brief 硬校验门（字段/枚举/cast自洽/双视角差异/精确数量/语言一致/技术段污染） |
| `build_from_brief.py` | brief→A/B 完整生图提示词+叠字参数（单份/批量双模式，公共段运行时解析 prompt-blocks 锚点） |
| `self_skeleton.py` | self 批量骨架生成器（选题清单→N 份骨架，批次内档位/风格/季节/视角自动均衡，查旬物索引填固有色；`--auto-creative` 自动填创意、`--build` 一步拼装提示词） |
| `creative_generator.py` | 预制创意库+模板自动生成器（为 `--auto-creative` 填充 pv_en/poem/latin/title，跳过 LLM 补创意） |
| `self_merge.py` | self 创意字段合并器（把 LLM 补的 pv_en/poem/latin/title 合并回骨架，自动校验） |
| `prep_images.py` | 一键下载URL→校正到目标尺寸→取色（支持 --text-scan 伪文字检测） |
| `inspect_image.py` | 图片分析（尺寸/比例/主色/边缘色，支持 --summary 整批统一比例/主色板，--prompt-inject 可粘贴风格片段） |
| `overlay_text.py` | 主标题与次要文字后期合成（支持 --batch 批量叠字模式） |
| `color_palette.py` | 色块后处理（可选）：从成品图提取 2–6 主色，渲染方形/条形色带并标注颜色名；单张 + --batch 批量；颜色名来自 color_names.json 最近邻匹配，纯 PIL 实现 |
| `brief_history.py` | 历史去重（recent 8 / add，JSONL 默认落项目工作区） |

---

## 文件结构

```
still-life-illustrator/
├── SKILL.md                  # 技能主干：铁律、标准流水线9步、规划-渲染协同模式
├── README.md                 # 本文件
├── scripts/                  # 12 个 Python 工具脚本 + color_names.json
├── references/
│   ├── style-profiles.md     # 三风格完整定义（公共段笔触克制+S1/S2/S3三节）
│   ├── layout-and-composition.md  # 通用规则与文字SSOT（像素/背景/构图/三铁律/文字系统）
│   ├── prompt-blocks.md      # 出图提示词模块库（<!--block:NAME-->锚点，脚本运行时解析）
│   ├── subject-structure.md  # 主体结构分析方法与分主体速查、搭靠层级规则
│   ├── seasonal_produce_index.json  # 四季应季＋全年常备题材事实库《旬物索引》374种（五区；JSON数据库，脚本优先查询）
│   ├── seasonal-produce-index.md   # 四季应季＋全年常备题材事实库《旬物索引》374种（五区；人类可读SSOT，供编辑）
│   ├── composition-cast.md   # 组合档位SSOT（Solo~Lush六档、多层后退、物理着附）
│   ├── style-extraction.md   # 参考图提取表
│   └── director/
│       ├── brief-schema.md   # brief@1.1 唯一规划格式
│       └── director-workflow.md  # 执行端唯一SOP（self 六步起草 + 批量路径）
└── assets/fonts/             # 自有字体：内置 OFL 中文字体 LXGWWenKai-Regular.ttf（跨平台 CJK 兜底），可另放自有字体
```

---

## 场景示例

- 水果："画一串樱桃番茄，带枝叶，Style-1，两张"
- 美食甜点："一块草莓蛋糕配咖啡，暖调午后氛围，45°视角"
- 酒饮酒器："红酒瓶加高脚杯，Style-2，烛光夜晚感，深色背景"
- 电商产品："一支护手霜，旁边摆同色柑橘，干净高级的产品静物"
- 花植："一束洋甘菊插在玻璃瓶里，水彩留白，浅色背景"
- 照片转插画："把这张照片画成 Style-3 色粉风"（发图）
- 中文海报："画月饼，中文主标题'中秋'，配中文小诗与中文季节"
- 批量出图："用 self 批量模式出 20 张秋季物产静物，风格均衡轮换"

---

## 怎样效果更好

1. **主体说具体**：品种/颜色/成熟度越清楚越好（"阳光玫瑰绿葡萄"好过"水果"）。
2. **给一个氛围词**，比堆一串形容词更有用："慵懒午后""清凉夏日""安静仪式感"。
3. **想要高级感**：留白和节奏比堆料更重要——可极简到只画一个主体，也可有序地丰盛；说"极简"或"丰盛一点"据此定元素多少。
4. **一次聚焦一个主体**最出彩；同类的组合（一串葡萄+几颗散落）算一个主体。
5. **文字想自己写**就直接给；否则会配一句贴合主体、有余味的短诗，并附上季节与准确的拉丁学名（中/英文都可，学名不臆造）。

---

## 常见问题

- **一次出几张？** 默认两张不同视角版式，同批生成、风格统一；要更多直接说。
- **标题或诗能改吗？** 能，把想要的文字发给我即可；语言、竖排都可指定。
- **能画小动物/人物故事吗？** 这个技能专注静物，拟人角色和叙事绘本不在范围内。
- **文字为什么默认英文？** 英文大标题配打字机小字更出杂志感（文字都由后期排版叠入、字形可控，并非模型手写）；需要中文随时说，中文模式只配中文季节、不附拉丁学名。
- **brief 先行模式什么时候用？** 需要可复现、可只改一字段重渲染、或批量出图时用；日常单张直接说主体即可，技能会自动走标准流水线。

---

## 技术说明

基于 Seedream 5.0 Pro 生图（正式档恒定 5.0 Pro / 长边 2048 / 双稿），使用 Python + Pillow 自动完成文字排版、图片校正与可读性校验。公共提示词段以 `prompt-blocks.md` 的 `<!--block:NAME-->` 锚点为单一来源，脚本运行时解析，不维护第二份文字。最终成品输出到项目工作区，final 成品永久保留、中间过程稿可清理。脚本与规则的详细档案见 `SKILL.md` 与 `references/`。


## 文件生命周期

| 阶段 | 文件模式 | 保留策略 |
|------|----------|----------|
| **brief 规划** | `*_brief.json` | 过程文件，交付后可删除（用户要求不保留时） |
| **提示词拼装** | `*_A.txt` / `*_B.txt` | 过程文件，交付后可删除 |
| **叠字参数** | `*_overlay.json` | 过程文件，交付后可删除 |
| **原始生图** | `*_A.png` / `*_B.png`（未校正） | 中间稿，校正后删除 |
| **校正稿** | `*_A.png` / `*_B.png`（校正后，prep_images 输出） | 中间稿，叠字后删除 |
| **final 成品** | `*_A_final.png` / `*_B_final.png`（叠字后） | **永久保留**，跨任务不清除，仅明确删除指令才清理 |
| **色块输出（可选）** | `*_palette.png`（color_palette.py 输出，含色带与颜色名） | 用户点名色块功能时生成，与 final 同级保留 |

> **默认行为**：final 成品永久保留；brief/prompt/overlay 等过程文件不保留（用户明确要求时）；校正稿等中间稿在叠字完成后删除。

## 容错、重试与失败处理

技能在网络、批量、字体、文字可读性等环节都内置了兜底，尽量不让单点失败拖垮整批：

| 环节 | 策略 |
|------|------|
| **网络下载** | `prep_images.py` 下载 URL 时连接/读取超时 30s；失败自动重试（共尝试 3 次，重试间隔 1s→2s）；`--cache-dir` 按 URL 的 MD5 缓存原图，避免重复下载 |
| **批量失败策略** | `build_from_brief.py --batch` 默认「失败继续」：某个 brief 出错只跳过它、继续处理其余，最后统一汇总成功/失败；加 `--fail-fast` 则遇到第一个失败立即中止 |
| **失败诊断文件** | 每个失败的 brief 落盘 `<id>_brief.validation_failed.json`，内含失败阶段（json_parse/validate/build）、错误列表、时间戳与原始 brief，方便排查；该命名不匹配 `*_brief.json`，不会被批量扫描重复拾取 |
| **字体回退** | `overlay_text.py` 按别名链在 assets/fonts 与系统字体目录查找（Linux/macOS 递归子目录、大小写不敏感），系统字体全缺失时落到内置的霞鹜文楷（assets/fonts/LXGWWenKai-Regular.ttf，含完整中文字形），再兜底 PIL 默认字体而不崩溃；西文字体遇中文自动回退楷体，避免空心方框 |
| **文字可读性** | 按 WCAG 相对亮度计算文字与背景对比度，不足 4.5:1 时自动切换深棕/暖白，防止文字与背景同色「消失」 |
| **公共段兜底** | `prompt-blocks.md` 锚点缺失/损坏时回退内置 `_FALLBACK` 段并告警，不直接崩溃；`--show-blocks` 可自检每段来源 |
| **历史去重** | `self_skeleton.py --history` 持久化已用主体（保留最近 100 个），跨会话排除重复主体与常见水果堆叠 |

> 依赖见根目录 `requirements.txt`（仅 Pillow；URL 下载走 Python 标准库 urllib，无需 requests 等额外依赖）。开发依赖（pytest 等）可用 `make install-dev` 安装，`make test` 跑单元测试、`make doctor` 跑技能自诊断。
>
> **Windows 无 make 时的等价命令**（在技能根目录执行，`py` 按实际环境可换成 `python`/`python3`）：
>
> | make 目标 | PowerShell / CMD 等价 |
> |---|---|
> | `make install` | `py -m pip install -r requirements.txt` |
> | `make install-dev` | `py -m pip install -r requirements.txt pytest flake8 black` |
> | `make test` | `py -m pytest tests/ -v` |
> | `make lint` | `py -m flake8 scripts/ --config=.flake8` |
> | `make doctor` | `py scripts\skill_doctor.py` |
