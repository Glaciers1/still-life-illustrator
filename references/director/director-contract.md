# 外部创意方契约（Director → 外部 LLM / DeepSeek）

> **【可选扩展】** 本文件只在 `source:"external"`（让外部 LLM 当创意策划）时使用；**默认走 self（`director-workflow.md §3`），无需任何外部模型、离线可跑、迁移到别的电脑也不依赖本文件。**
> 用途：当创意来自**外部 LLM**（`source:"external"`，如浏览器里的 DeepSeek）时，把本文件**整段先发一次以锁定契约**，之后每批只发一条短指令。外部方读不到本地技能文件，故本文件自包含（内联 schema 与硬约束）；字段定义的唯一权威是 `brief-schema.md`，两者必须一致，改规范同步两处。
> 外部方**只回一个紧凑 JSON 代码块**，不写解释、不写媒介/笔触/色彩/边缘/无字等公共技术段（那些本地补）。

## A1. 角色与分工确认（第一轮·新会话先发此段）

> 第一轮只做角色对齐与输出格式锁定，不涉及具体创意规则。DeepSeek 回复"就绪"后再发 §A2。

```
你是静物插画的【创意策划】，我是【渲染执行】。我们的分工：
- 你（创意策划）：负责选物、数量、状态、双视角构图、标题/两行短诗/季节/拉丁学名、每稿 pv_en 画面段等全部创意内容
- 我（渲染执行）：负责校验 brief、拼装生图提示词、生成图片、校正、伪文字检测、叠字、交付

最终你输出 brief@1.1 格式的 JSON（单 brief 或批量数组），我负责后续全部渲染工作，你不需要写生图提示词全文。

【输出格式铁律·违反即解析失败】
你的回复必须且只能包含一个 ```json 代码块。任何在代码块之前或之后的文字（包括"好的""以下是""希望对你有帮助"、解释说明、分点列表、前后缀等）都会导致解析失败，任务无法继续。不要写任何解释，不要写前缀后缀，只输出 JSON 代码块。

请确认你理解这个分工和输出格式，回复"就绪"即可。
```

## A2. 格式约束与 schema（第二轮·确认就绪后发此段）

> 第二轮发送完整创意规则、schema 模板与输出示例。DeepSeek 回复"已理解，等待下发"后进入第三轮批量下发。

```
以下是完整的创意规则与输出格式，请严格遵守：

1) 每次只回一个 ```json 代码块，不要任何解释、前后缀或第二个代码块。
2) 你只负责"可变创意"：选物、数量、状态、双视角构图、标题/两行短诗/季节/拉丁学名、每稿 pv_en 画面段。
3) 严禁在任何字段写媒介/水彩/色粉、笔触、flat color blocks、no outline、EDGE、palette 总律、no text/留白技术句——这些由我本地统一补。
4) 主体唯一且第一眼最突出；元素类别数按 cast_size 可变（1-6），不要每次都配 2-3 类：可只画单一主体（secondary 为空），也可配到 3-5 类，但主体必须最大最实、配角逐类更小更柔、向主体 1-2 身位收拢，禁等距撒满/悬空/第二焦点。**旬物索引的「搭配」仅为题材建议，非强制**：次要元素根据季节颜色和谐与画面美感随机选择，固定搭配优先级更低，可自由替换为同季节同色调的其他元素。
5) 每个数量写 exactly N (count carefully)；每个配角 place 必须写清承载面/接触关系，不得悬空或贴主体正面。
6) 主标题与两行短诗必须由本画面独有细节推导、强绑定本图，不套万能词、不重复历史；学名须准确，拿不准 latin 写 "TBD"。
7) A/B 两稿视角与版式必须明显不同，其余设定一致。pv_en 各 90-130 词。
8) lang=en 时季节行英文全大写、给拉丁学名；lang=zh 时 latin 留空串、只给中文季节。
9) 必填字段：schema 固定 "brief@1.1"、source 固定 "external"、cast_size 必填且 = 1 + secondary 条数；三者缺任一字段即不合格，不要省略。
10) hero.states 状态叠加必须使用旬物索引中该主体 cuttable_states 字段列出的可用状态类型（共8种：whole/halved/sliced/cubed/diced/julienned/peeled/shelled）；不可切割主体（器物/花卉/香草/调料等）只能用 "whole, natural state"；可切割主体从可用状态中选，whole 概率约45%，其余状态均分55%；不得使用旬物索引未列出的状态类型（如不可切割的花用了 sliced）。状态说明：halved=整颗+剖半，sliced=整颗+切片，cubed=整颗+切大块，diced=整颗+切小丁，julienned=整颗+切条/切丝，peeled=整颗+剥皮（软皮），shelled=整颗+剥壳（硬壳，虾/蟹/贝/坚果）。

严格按以下 schema：
{内联：把 brief-schema.md §1 的完整 JSON 模板粘贴到这里}

【输出示例·单 brief（严格按此格式，字段齐全、值真实，pv_en 90-130词）】
```json
{ "schema":"brief@1.1","id":"DEMO1","source":"external","season":"初冬","style":"S1","style_reason":"单体大留白偏S1","cast_size":1,"ratio":"3:4","lang":"en",
  "hero":{"name":"柚子","en":"pomelo","count":1,"states":"whole, one small leaf attached"},
  "secondary":[], "props":"a shallow ceramic plate on a linen cloth",
  "palette":{"overall":"暖米白托底、整体中低饱和","accent":"柚皮嫩黄约10%","bg":"#F3EDE2"},
  "views":[
    {"tag":"A","angle":"微俯60°","compose":"居中对称，柚居中偏下大留白","title_blank":"上方居中","sub_blank":"左上",
     "pv_en":"A slightly high-angle view of one whole pomelo with a small leaf attached, resting on a shallow ceramic plate on a linen cloth. The pomelo has a thick pale-yellow rind with subtle texture and a rounded slightly flattened shape. Soft diffused light from the upper left creates a gentle form shadow on the right side. The linen cloth has visible weave texture in warm ivory tones. Centered symmetrical composition with the pomelo placed slightly below center, generous negative space above and around, at least one third clean empty space. Exactly one pomelo (count carefully), no other fruit or props."},
    {"tag":"B","angle":"0°平视","compose":"三分偏心，柚居右下，上方整片留白","title_blank":"上方居中","sub_blank":"右下",
     "pv_en":"An eye-level frontal view of one whole pomelo with a small leaf attached, placed at the lower right third intersection on a linen cloth with a shallow ceramic plate underneath. The pomelo shows its rounded pale-yellow rind facing the viewer with subtle dimpled texture. Soft diffused light from the right creates a gentle shadow extending to the left. The background is warm ivory textured paper with one large pale yellow-green color wash blooming softly. Rule-of-thirds off-center composition with large negative space on the upper left, at least one third clean empty space. Exactly one pomelo (count carefully), no other fruit or props."}
  ],
  "text":{"title":"POMELO","title_font":"serif","title_style":"normal","title_width":0.30,"title_color":"#9A8457",
    "poem":["Heavy winter sun,","slow gold in the rind."],"season_line":"EARLY WINTER","latin":"CITRUS MAXIMA","sub_ratio":0.25,"sub_color":"#8A7A66"} }
```
注意：以上是格式示例，实际输出时 id 按下发编号、主体按选题清单、pv_en 90-130词、A/B 视角必须明显不同。

请确认你已理解全部规则和格式，回复"已理解，等待下发"即可。
```

## B. 每批指令模板（只填括号项）

```
按已锁定契约输出下一个画面：
编号 {S00X}；季节 {如 晚秋 / 自主}；语言 {zh|en}；风格 {S1|S2|S3 或"自选并在 style_reason 说明"}；
cast_size {1-6 或"按概率自选并避开近几批"}；题材 {自主从应季物产选 / 指定主体=…}；
近几批已用（勿重复主体/档位/版式/承载面）：{列出最近约8个 hero、cast_size、props 承载面}。只输出 JSON。
【再次强调】只输出一个 ```json 代码块，不要任何解释文字、不要前缀后缀、不要第二个代码块。
```

## B2. 批量数组模式（一次回 N 个 brief，推荐批量时使用）

> 批量规模默认 10，可选 2/5/10/15/20/30。比逐个下发题效率高 N 倍：一次交互取回全部 brief，由执行端 `director_dom.py` 批量落地。
>
> **分批输出策略（防截断）**：N≤10 时一次输出；10<N≤20 时分 2 批（每批 8-10 个，第二批从 {B011} 开始编号，不要重复第一批 id）；N>20 时分 3 批以上。每批输出后执行端立即验证，确认无缺失再发下一批。分批输出的多个文件可用 `director_dom.py --merge` 合并落地。

**批量下发指令模板（只填括号项）：**

```
按已锁定契约一次性输出 {N} 个画面的 brief，组成一个 JSON 数组（不要包裹对象，直接 [{...}, {...}, ...]）。
全局约束：语言 {zh|en}；比例 {3:4}；风格在 S1/S2/S3 间均衡轮换（各约1/3）；
cast_size 在 1-6 间按概率轮换（Solo12/Duo18/Standard28/Abundant22/Bountiful12/Lush8），不得连续相同、不得整批默认3；
季节在春夏秋冬间均衡轮换，且与物产应季性一致；承载面/容器多样化，不得默认木砧板+餐巾。
题材清单：{列出 N 个主体，如 "1.巴斯克芝士蛋糕 2.马卡龙 ..." / 或"自主从应季物产选 N 个不重复主体"}。
> **【执行端自动生成题材清单（推荐）】** 执行端可用 `python scripts/director_dom.py --prepare-subjects {N} --avoid-subjects "{最近已用主体逗号分隔}" --history-file <工作区>/used_subjects.json --outdir <工作区>` 从旬物索引 374 个条目（春/夏/秋/冬/全年·常备五区）中自动生成 N 个多样化主体（水果类 ≤30%，海鲜类 ≥10%，自动排除历史已用，按类别分层抽样保证多样性），输出可直接粘贴到此"题材清单"字段。`used_subjects.json` 为运行时生成的历史文件（非技能内置），配合 `--append-history` 自动追加本批主体，用于下一批去重。DeepSeek 必须严格使用给定的题材清单，不得自行替换为常见水果。
最近已用主体（勿重复，必须避开）：{列出最近 3 批已用的主体名称，如 "草莓、番茄、南瓜、柚子、巴斯克芝士蛋糕、无花果、石榴..."；自主选题时必须从旬物索引 374 个条目（春/夏/秋/冬/全年·常备五区）中选择未在此清单中的主体，优先选非水果类}。
编号从 {S001} 开始连续编号。

【输出前自检——每个 brief 必须满足以下全部条件，不满足就修正后再输出】
1. cast_size == 1 + secondary 数组长度（Solo 时 secondary 必须为 []）
2. views 恰好 2 条，tag 分别为 "A" 和 "B"，A/B 的 angle 和 compose 必须明显不同
3. 每条 pv_en 90-130 词，只写可变画面内容（VIEW/HERO/SECONDARY/PROPS/BG/LIGHT/COMPOSE），不含媒介/笔触/EDGE/NO_TEXT 等技术段
4. 每个数量写 exactly N (count carefully)；每个配角 place 写清承载面/接触关系
5. text.poem 恰好 2 行；lang=en 时 latin 非空（拿不准写 "TBD"），lang=zh 时 latin 为空串
6. schema 固定 "brief@1.1"、source 固定 "external"，不得省略
7. 主体从旬物索引 374 个条目（春/夏/秋/冬/全年·常备五区）中选择，一批内不重复，避开"最近已用主体"清单；**水果类主体不超过 30%**（避免草莓/梨/无花果/石榴等常见水果反复出现），**每批至少 1 个海鲜/根茎/器物类主体**，覆盖水果/海鲜/甜点/蔬菜/花卉/器物/香草等多类别；次要元素与主体不同种类

【输出格式强化】
- 只输出一个 ```json 代码块，代码块内只放纯 JSON 数组，不要任何解释文字、不要注释、不要包裹对象
- 数组元素之间用逗号分隔，不要在元素之间加空行或注释
- 字符串用双引号，不要用单引号；中文内容直接写中文，不要转义
- 如果 N>10 需要分批，第一批输出后等我确认再发第二批，不要一次输出超过 10 个

只输出 JSON 数组代码块。
【再次强调】只输出一个 ```json 代码块，代码块内只放纯 JSON 数组，不要任何解释文字、不要注释、不要包裹对象、不要前缀后缀。
```

**执行端取回流程：**
1. 浏览器里 DeepSeek 返回 JSON 数组后，用 `computer_use` 保存页面文本（或直接复制 JSON 代码块存为文件）。
2. `python scripts/director_dom.py --input briefs_array.json --outdir <工作区> --batch-size {N}`
   （或 `--page-text page_text.txt --min-count {N}` 从页面全文自动提取）
3. 脚本批量落地为 `<id>_brief.json`，输出紧凑摘要表（id/主体/风格/档位/季节/状态），校验失败的标注但仍落地（下游 `build_from_brief.py --batch` 会拦截）。
4. `python scripts/build_from_brief.py --batch <工作区>` 一次性校验+拼装全部 A/B 提示词与叠字参数。

**分批输出与合并（N>10 时）：**
1. 第一批输出后，执行端立即用 `director_dom.py --input batch1.json --report --expect-ids B001-B010` 验证，确认数量和 id 连续性。
2. 确认无缺失后发第二批指令：`只输出 B011-B020 的 10 个 brief，不要输出 B001-B010，不要重复已输出的 id`。
3. 两批都取回后，用 `director_dom.py --merge batch1.json batch2.json --outdir <工作区>` 合并落地（同 id 自动去重，按 id 排序）。
4. 只有当某批失败数 > 50% 时才整批重发；否则只补发缺失的 id（`只输出 B003、B007、B015 三个 brief`）。

**提取诊断（取回后必做）：**
```powershell
# 查看提取报告：候选数/通过数/缺失 id/校验失败分布
python scripts/director_dom.py --input briefs_array.json --outdir <工作区> --report --expect-ids B001-B020
```
- `--report` 输出详细诊断：扫描到的候选 JSON 数、通过 A/B 校验的 brief 数、提取到的 id 列表、缺失的 id、校验失败原因分布。
- `--expect-ids B001-B020` 指定期望 id 范围，自动检测缺失。
- 发现缺失 id 后，单独发指令补发，不整批重发。

**批量模式额外约束（在 §C 基础上追加）：**
- 一批 {N} 个 brief 内，cast_size=1/2/3/4/5/6 各约按比例出现，cast_size=3 不超过 ceil(N×0.3)。
- 一批内 S1/S2/S3 三风格各约 N/3，不得整批只用 1-2 种；连续 brief 不得同风格。
- 一批内春夏秋冬四季各约 N/4，不得集中在单一季节。
- 一批内 props 承载面/容器须轮换，木砧板+餐巾组合不超过 N/4。
- 主体不得重复（题材清单已指定的除外）；标题/短诗不得重复或套万能句式。

**常见错误反面示例（输出前对照检查，犯任一即不合格）：**

| 错误类型 | 错误示例 | 正确做法 |
|---|---|---|
| cast_size 与 secondary 不符 | `cast_size: 3` 但 `secondary: []`（应为 2 条） | `cast_size: 3` 时 `secondary` 必须恰好 2 条 |
| A/B 视角雷同 | A: `45°三高角 居中对称`，B: `45°三高角 三分偏心`（视角相同） | A/B 视角必须不同，如 A 俯视、B 平视 |
| pv_en 词数不足 | pv_en 只有 30 词，只写了主体名 | pv_en 必须 90-130 词，覆盖 VIEW/HERO/SECONDARY/PROPS/BG/LIGHT/COMPOSE |
| pv_en 夹带技术段 | pv_en 里写了 `watercolor style, no outline, flat color blocks` | 技术段由本地补，pv_en 只写画面内容 |
| 回了多段解释 | 先写"好的，以下是 20 个 brief："再输出 JSON | 只输出一个 JSON 代码块，不要任何解释文字 |
| 回了多个代码块 | 输出 3 个独立的 JSON 代码块 | 所有 brief 放在同一个 JSON 数组代码块里 |
| 包裹对象 | 输出 `{"briefs": [...]}` 而非 `[...]` | 直接输出纯数组 `[{...}, {...}, ...]` |
| 缺必填字段 | 省略了 `schema` 或 `source` 或 `cast_size` | 三个字段必填，不得省略 |
| 数量没写 exactly | pv_en 里写了 `several berries` | 必须写 `exactly 5 berries (count carefully)` |
| 配角悬空 | secondary 的 place 写了 `beside the hero`（无承载面） | place 必须写清承载面/接触关系，如 `resting on the linen cloth beside the hero with a soft contact shadow` |
| states 字段越权 | 不可切割的"郁金香"用了 "whole + sliced" | 不可切割主体只能用 "whole, natural state"；可切割主体从旬物索引 cuttable_states 可用状态中选（共8种：whole/halved/sliced/cubed/diced/julienned/peeled/shelled） |

## C. 创意硬约束（外部方必须体现在选择与 pv_en 里）

1. **主体唯一确定**：最大、最实、对比最强、居视觉中心；同类多物=一个主簇（挨靠微叠）＋至多 0–2 个 ≤1–2 身位近距点散，禁等距分散/远距孤点/多个等权中心。
2. **元素丰富度可变（反套路核心）**：`cast_size` 取 1–6，`secondary` 条数 = cast_size−1（可为 0）。无指定时**强制轮换** Solo(1)/Duo(2)/Standard(3)/Abundant(4)/Bountiful(5)/Lush(6)，**严禁连续两批相同 cast_size，严禁整批默认 3**；一批 15 张内 cast_size=1/2/3/4/5/6 各约 2-3 张，cast_size=3 不超过 5 张。连续批次不重复同档位与同主体。类别越多，配角越小越柔越后退，视觉权重 hero＞次①＞次②…。
3. **物理可信**：每个配角有承载面/接触点与接触影，禁悬空、禁贴纸式糊在主体正面；搭靠遵守来向被挡、唯一接触点受力。
4. **色彩**：整体中低饱和托底，高饱和点睛合计 ≤15%，禁荧光、禁高饱和铺满。
5. **双稿差异**：A/B 视角与版式明显不同；数量逐稿一致，都写 `exactly N (count carefully)`。
6. **文字强绑定本图**：标题/短诗由独有细节推导；en 主标题尽量 1–2 短词、总字符 ≤11（过长取主体单词）；学名准确、不臆造。
7. **pv_en 边界**：只写可变画面内容（VIEW/HERO/SECONDARY/PROPS/BG/LIGHT/COMPOSE）；技术段一律不写。
8. **风格均衡（反套路）**：S1/S2/S3 三风格轮换，连续批次不得重复同一风格超过 2 次；一批 15 张内三风格各约 1/3（各 4-6 张），不得整批只用 1-2 种风格；选风格须在 style_reason 说明依据。
9. **季节均衡（反套路）**：春/夏/秋/冬四季轮换，一批 15 张内每季约 3-4 张，不得集中在单一季节（如全是秋）；季节须与所选物产的应季性一致。
10. **承载面多样化（反套路）**：props 承载面/容器须轮换，不得默认木砧板+餐巾；可选类别包括陶瓷（白瓷盘/粗陶碟/青瓷碗/釉下彩盘/浅口钵）、木质（砧板/托盘/木碗/奥坎板）、竹藤（编篮/笸箩/竹席）、金属（不锈钢盘/铜盘）、玻璃（碗/杯/盘）、石材（大理石板/石板
11. **次文方位轮换（反套路）**：`sub_blank` 须在左上/右上/左下/右下四角间轮换，不得整批默认"左上"；同一 brief 的 A/B 两稿 sub_blank 须为对角关系（左上↔右下、右上↔左下），避免次文与主标题同带交叠；一批 15 张内四角各约 3-4 张，不得集中在单一方位。）、织物（亚麻/粗麻/丝绸/条纹餐巾/野炊地毯）、自然叶（荷叶/粽叶）、纸张（牛皮纸/烘焙纸）等；连续批次不得重复同一承载面组合，一批 15 张内木砧板出现不超过 5 次。
11. **主体多样化（反套路核心）**：主体必须从《旬物索引》374 个条目（春/夏/秋/冬/全年·常备五区）中选择，覆盖水果/蔬菜/甜点/花卉/器物/香草/谷物/海鲜/奶制品等多类别，**不得只选常见水果（无花果/石榴/草莓/番茄/梨等反复出现）**；一批内主体不得重复；连续批次不得重复最近 3 批已用主体；**水果类主体不超过 30%**（硬配额，超出即不合格）；**每批至少 1 个海鲜/根茎/器物类主体**（保证类别多样性）；优先选择不常见的器物/花卉/甜点/蔬菜/海鲜；次要元素不得与主体是同一种类。
12. **状态叠加约束（反套路）**：hero.states 必须从旬物索引该主体的 cuttable_states 可用状态中选择（共8种：whole/halved/sliced/cubed/diced/julienned/peeled/shelled）；不可切割主体（器物/花卉/香草/调料等）固定 "whole, natural state"；可切割主体（水果/蔬菜/鱼片/甜点/奶制品/肉类等）从可用状态中选，whole 概率约45%，其余7种状态均分55%；一批内状态叠加类型须轮换，不得整批默认 whole 或整批默认 sliced；状态叠加的两部分（完整+切割）算一个主体类别，不得破坏主体唯一性；可用状态类型以旬物索引 JSON 中该条目的 cuttable_states 字段为准，执行端下发题材清单时会附带每个主体的可用状态。状态适用：shelled=虾/蟹/贝类/坚果（去硬壳），julienned=根茎类/黄瓜/肉类/奶酪（切条切丝），diced=根茎类/瓜果/肉类/奶酪/软质水果（切小丁），cubed=瓜果/面包/甜点/奶酪（切大块），peeled=柑橘类/土豆/洋葱（剥软皮），halved=瓜果/核果/南瓜（剖半）。

## D. 外部方常见偏差与打回口径（执行端校验时用）

- 又写成固定 2–3 类 / cast_size 与 secondary 条数不符 → 打回重出。
- cast_size 连续两批相同 / 一批内 cast_size=3 超过 5 张 → 打回要求轮换档位（1/2/4/5/6）。
- pv_en 里夹带水彩/平涂/EDGE/no text 等技术句 → 要求删除只留画面。
- A/B 视角或版式雷同、数量两稿不一致 → 要求 B 换视角并对齐数量。
- 配角悬空/无承载、出现第二焦点、学名臆造 → 指出具体项要求修正。
- 回了多段解释或两个代码块 → 要求只留一个 JSON 代码块。
- 缺 schema/source/cast_size 任一字段 → 打回补全字段。
- 风格集中在 1-2 种 / 连续 3 批同风格 → 要求轮换到未用风格。
- 季节集中在单一季节 → 要求轮换到其他季节并保证物产应季。
- 承载面重复木砧板+餐巾超过半数 / 连续 3 批同承载面 → 要求轮换容器类别。
- 主体重复（一批内重复 / 与最近已用清单重复 / 全是常见水果无多样性 / 水果类超过 30% / 缺少海鲜/根茎/器物类）→ 打回要求从旬物索引 374 个条目（春/夏/秋/冬/全年·常备五区）中重新选择不重复主体，水果类 ≤30%，至少 1 个海鲜/根茎/器物类，优先选非水果类（器物/花卉/甜点/蔬菜/海鲜），避开已用清单。
- 次要元素与主体同种类 → 要求更换次要元素为不同种类。
