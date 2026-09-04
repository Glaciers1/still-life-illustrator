# Brief JSON 规范（唯一规划格式 · brief@1.1）

> 这是"先规划、后渲染"的**唯一中间格式**。无论创意来自外部 DeepSeek（`source:"external"`）还是本体技能自起草（`source:"self"`），都必须产出同一份符合本规范的 brief，再经 `scripts/validate_brief.py` 校验通过、`scripts/build_from_brief.py` 拼装成最终生图提示词。
> **分工铁律**：brief 只承载"可变创意"（选物/数量/状态/视角构图/文字/画面段 pv_en）；媒介笔触、PALETTE、HERO、CLUSTER、EDGE、TEXT-BLANK、NO_TEXT 等"不变技术段"由本地 build 脚本统一补，**brief 里禁止写这些**（防止提示词变长、风格被带偏）。

## 1. 完整字段

```json
{
  "schema": "brief@1.1",
  "id": "S00X",
  "source": "self",
  "season": "应季季节（中文：早春/春/初夏/夏/晚秋/秋/初冬/冬 等）",
  "style": "S1",
  "style_reason": "一句话风格理由",
  "ref_style": "可选：参考图风格描述字符串（由 inspect_image.py --prompt-inject 生成，如 'background color #F3EDE2; palette dominated by #E8A87C,#C38D9E; soft muted pastel palette; light background; portrait orientation'）；无参考图时留空串或省略此字段",
  "cast_size": 3,
  "ratio": "3:4",
  "lang": "en",
  "hero": { "name": "主体中文名", "en": "subject EN", "count": 2, "states": "状态叠加：从旬物索引该主体 cuttable_states 可用状态中选（共8种：whole/halved/sliced/cubed/diced/julienned/peeled/shelled）；不可切割主体（器物/花卉/香草等）只能写 whole, natural state；可切割主体如 whole + halved cross-section / whole + sliced / whole + cut into large pieces / whole + diced into small cubes / whole + julienned into thin strips / whole + peeled / whole + shelled" },
  "secondary": [
    { "name": "配角中文名", "en": "prop EN", "count": 1, "place": "相对主体的摆位与≤1-2身位距离、承载面/接触关系", "note": "柔化层级/叙事作用/比主体小多少柔多少" }
  ],
  "props": "容器/器皿/衬底/承载，纯环境不算 cast 类别；无则空串 \"\"",
  "palette": { "overall": "整体中低饱和基调", "accent": "高饱和点睛色与合计占比%（≤15%）", "bg": "#HEX" },
  "views": [
    { "tag": "A", "angle": "视角，如微俯60°", "compose": "构图法与主体落点", "title_blank": "上方居中", "sub_blank": "左上|右上|左下|右下",
      "pv_en": "本稿可变英文画面段 90-130 词，结构见 §3" },
    { "tag": "B", "angle": "必须与A明显不同的视角", "compose": "与A不同版式与落点", "title_blank": "上方居中", "sub_blank": "与A对角",
      "pv_en": "同上，视角/版式与A不同，其余设定与A一致以保证统一" }
  ],
  "text": {
    "title": "主标题（en 建议 1-2 短词、总字符≤11，过长取主体单词）",
    "title_font": "serif|sans|kai|hand",
    "title_style": "normal|italic|wave|arch|scatter",
    "title_width": 0.30,
    "title_color": "#hex",
    "poem": ["第一行", "第二行"],
    "season_line": "en→英文大写季节；zh→中文季节",
    "latin": "准确拉丁学名（英文大写）；zh 模式留空串 \"\"；拿不准填 TBD",
    "sub_ratio": 0.25,
    "sub_color": "#hex"
  },
  "color_palette": {
    "enabled": true,
    "num_colors": 5,
    "shape": "square",
    "sort": "brightness",
    "pos": "bottom",
    "label": "name"
  }
}
```

## 2. 字段约束（validate_brief.py 据此硬校验）

| 字段 | 约束 |
|---|---|
| `schema` | 固定 `brief@1.1`（旧会话缺省视为 1.0，仍可跑但会提示升级） |
| `source` | `external` / `self` 二选一，必填 |
| `id` | 非空字符串，用作输出文件前缀 |
| `season` / `style` / `lang` / `ratio` | style∈{S1,S2,S3}；lang∈{zh,en}；ratio 形如 `3:4`/`4:5`/`1:1` |
| `ref_style` | **可选**字符串，无参考图时省略或空串；有参考图时填 `inspect_image.py --prompt-inject` 输出的英文风格片段；build_from_brief.py 拼装时自动注入到 PALETTE 段之后，不影响其他模块 |
| `cast_size` | 整数 1–6，且 **`cast_size == 1 + len(secondary)`**（Solo=1，secondary 必须为 `[]`） |
| `hero` | 唯一；`count≥1`；`name/en/states` 非空；不允许第二个等权主体；**`states` 必须从旬物索引该主体 `cuttable_states` 可用状态中选择**（共8种：whole/halved/sliced/cubed/diced/julienned/peeled/shelled）；不可切割主体（器物/花卉/香草/调料等）固定 `"whole, natural state"`；可切割主体（水果/蔬菜/鱼片/甜点/奶制品/肉类等）从可用状态中选，whole 概率约45%，其余状态均分55%；状态叠加的两部分（完整+切割）算一个主体类别；状态适用：shelled=虾/蟹/贝/坚果（去硬壳），julienned=根茎/黄瓜/肉类/奶酪（切条），diced=根茎/瓜果/肉类/奶酪（切丁），cubed=瓜果/面包/甜点（切块），peeled=柑橘/土豆/洋葱（剥皮），halved=瓜果/核果（剖半） |
| `secondary` | 数组，**0–5 条**（这是反套路关键：不再写死 1–2）；每条需 `name/en/count/place`，`place` 必须交代承载面或接触关系（禁悬空）；**搭配非强制**：旬物索引的搭配仅为建议，次要元素根据季节颜色和谐与画面美感随机选择，固定搭配优先级更低 |
| `props` | 字符串，可为空；只写容器/衬底/承载环境，**不计入 cast_size** |
| `palette.bg` | `#hex`；accent 占比 ≤15%（要更浓可 20–25%，需在 overall 说明） |
| `views` | 恰好 2 条，tag 依次 A/B；`angle`、`compose` 两稿不得雷同（相似度高会告警）；`pv_en` 各 90–130 词，且都含 `exactly N (count carefully)` 式精确数量 |
| `text.title` | 非空；`title_font∈{serif,sans,kai,hand}`（无 marker）；`title_style` 五选一 |
| `text.poem` | 恰好 2 行 |
| `color_palette` | **可选**对象，省略或 enabled=false 则不渲染色块；num_colors∈{2,3,4,5,6}；shape∈{square,bar}；sort∈{brightness,saturation,none}；pos∈{top,bottom,auto}；label∈{name,hex,hsl,none}；由 scripts/color_palette.py 在叠字后后处理，不侵入生图提示词 |
| `text` 语言一致性 | lang=en：`season_line` 全大写、`latin` 非空（TBD 仅告警放行）；lang=zh：`latin` 必须为空串、只留中文季节 |
| 应避免项 | pv_en/任意字段应避免出现媒介笔触、flat color blocks、no outline、EDGE、PALETTE、no text 等技术段措辞（本地补；命中给 warning，不阻断） |

## 3. `pv_en` 写法（只写"这张图可变的画面"，90–130 词）

按序覆盖：**VIEW 视角 → HERO 主体（exactly N (count carefully)、状态、点到为止的结构）→ SECONDARY 各物精确数量/摆位距离/承载面/比主体更柔 → PROPS 承载 → BG 背景 → LIGHT 光线 → COMPOSE 构图与留白**。
- 每类物体数量与 brief 的 hero.count / secondary[].count 完全一致（Solo 不出现任何配角）。
- 多元素（Abundant/Bountiful）补一句"各组向主体 1–2 身位内收拢、逐类更小更柔、无第二焦点"。
- 不写：媒介/水彩/色粉、笔触、平涂、零描边、EDGE 层级、色彩总律、无字留白、NO_TEXT（本地模块统一补）。

## 4. 最小合法示例

**Solo（cast_size=1，secondary 为空）**
```json
{ "schema":"brief@1.1","id":"DEMO1","source":"self","season":"初冬","style":"S1","cast_size":1,"ratio":"3:4","lang":"en",
  "hero":{"name":"柚子","en":"pomelo","count":1,"states":"whole, one small leaf attached"},
  "secondary":[], "props":"a shallow ceramic plate on a linen cloth",
  "palette":{"overall":"暖米白托底、整体中低饱和","accent":"柚皮嫩黄约10%","bg":"#F3EDE2"},
  "views":[ /* A: 微俯60°, 柚居中偏下, 大留白; B: 平视, 柚居下, 上方整片留白 —— pv_en 略 */ ],
  "text":{"title":"POMELO","title_font":"serif","title_style":"normal","title_width":0.30,"title_color":"#9A8457",
    "poem":["Heavy winter sun,","slow gold in the rind."],"season_line":"EARLY WINTER","latin":"CITRUS MAXIMA","sub_ratio":0.25,"sub_color":"#8A7A66"} }
```

**Abundant（cast_size=4，secondary 三类）**
```json
{ "schema":"brief@1.1","id":"DEMO4","source":"self","season":"晚秋","style":"S2","cast_size":4,"ratio":"3:4","lang":"en",
  "hero":{"name":"南瓜","en":"small pumpkin","count":1,"states":"whole with short stem"},
  "secondary":[
    {"name":"板栗","en":"chestnuts","count":5,"place":"盛在主体左前的小铁碟里、贴住主簇","note":"更小更柔"},
    {"name":"干菊枝","en":"dried chrysanthemum sprig","count":1,"place":"斜搭在南瓜右后、被南瓜挡住下半","note":"最柔、退后"},
    {"name":"肉桂棒","en":"cinnamon sticks","count":2,"place":"平放在南瓜正前布面、带接触影","note":"小而柔"}],
  "props":"旧木桌面 + 亚麻餐布",
  "palette":{"overall":"暖棕米灰整体中低饱和","accent":"南瓜橙约12%","bg":"#EFE6D6"},
  "views":[ /* A/B 视角版式不同，pv_en 略 */ ],
  "text":{"title":"HARVEST NEST","title_font":"serif","title_style":"arch","title_width":0.4,"title_color":"#A8632A",
    "poem":["The table keeps what","the short sun leaves behind."],"season_line":"LATE AUTUMN","latin":"CUCURBITA PEPO","sub_ratio":0.25,"sub_color":"#83705A"} }
```
