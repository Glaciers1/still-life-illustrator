# 版面、构图与通用规则（SSOT 唯一权威）
> 本文件是以下规则的【唯一权威完整版】：①比例像素换算 ②量化规则→提示词译法 ③背景颜色 ④构图/视角 ⑤三条通用画面规则（主体突出、同类疏密、边缘虚实）⑥提示词骨架 ⑦文字系统与 `overlay_text.py` 用法。
> SKILL.md 与风格档案（style-profiles.md）只保留一句话指针，**修改这些规则只改本文件**，不再到处复制。风格独有的媒介/编排手法在 style-profiles.md 对应节。
## 目录
1. 比例像素换算
2. 量化规则 → 提示词译法
3. 背景颜色规则（三风格通用，含深色自选）
4. 构图、视角与三条通用画面规则
5. 提示词骨架（拼装模块见 prompt-blocks.md）
6. 文字系统与 overlay_text 用法
## 1. 比例像素换算（长边 2048）
| 比例 | 宽×高（竖）/（横） |
|---|---|
| 1:1 | 2048×2048 |
| 4:5 | 2048×2560 |
| 3:4 | 1920×2560 |
| 2:3 | 1707×2560 |
| 9:16 | 1152×2048 |
| 4:3 横 | 2048×1536 |
| 3:2 横 | 2048×1365 |
| 16:9 横 | 2048×1152 |
非标准比例以 `inspect_image.py` 输出为准，等比缩放到长边 2048 并取偶数；用户明确给像素时从其指定。
## 2. 量化规则 → 提示词译法
模型不理解像素约束，需转成视觉描述，叠字阶段再精确兑现：
| 规则 | 提示词译法（英文更稳） |
|---|---|
| 边距 ≥12% | generous margins, subject kept away from all edges |
| 留白 ≥33% | at least one third of the frame is clean empty negative space |
| 主体 40–55% | subject occupies roughly half of the frame, never cropped by edges |
| 次元素 ≤25% | only 1–2 small accent props, each much smaller than the main subject |
| 主体突出（§4.1） | hero is the unambiguous largest, most defined, strongest-contrast element at the visual center (its edges are softened per §4.3, not hard); all props smaller and softer and grouped toward the hero, nothing competes |
| 同类疏密（§4.2） | same-kind items form ONE tight main cluster (touching, slightly overlapping), with at most 1–2 pieces set a short controlled distance within 1–2 of their own size; never evenly spread, no isolated far-flung pieces, no second focal cluster |
| 边缘虚实·默认（§4.3） | the hero itself has SOFT feathered bleeding edges (wet-on-wet, loose broken outlines, shadow side partly melting into the paper) yet its overall shape and light-side contour stay clearly readable and it keeps the strongest contrast and focal weight; secondary props are one level softer still and the background stays softest (soft, not blurred into nothing) |
| 边缘虚实·点名不柔主体 | only when explicitly requested, keep the hero's outline crisp, clean, confident and complete with no edge softening on the subject, while secondary props may stay soft |
| 文字区（一律 PIL） | leave clean blank areas with no marks for later typography: a horizontal band at top center for the title and a spot at [方位] for the two secondary lines |
| 无文字 | absolutely no text, no letters, no numbers, no watermark, no logo |
## 3. 背景颜色规则（三风格通用，含深色自选）
三风格差异只在纸面纹理（Style-1/2 水彩纸纹、Style-3 牛皮纸/色粉颗粒），不在颜色规则。
- **默认浅底**：白、米白、象牙、暖灰等浅色（#FFFFFF / #FAFAFA / #F5F1E8 / #FFFFF0 量级），低饱和、高明度，让主体跳出；纹理按各自风格保留。
- **撞色例外（自动触发，仍偏浅）**：当主体固有色与默认浅底过于接近（白蒜、白蘑菇、白梨、白葡萄酒杯、白玫瑰、浅色餐具）时，背景改用主体色的互补/对比色，**低饱和、高明度**（色相环 ±150–210°、饱和度 20–40%），例如浅绿主体配暖灰粉 #E8DCD6、橙黄主体配灰青 #DCE4E2。
- **深色背景（用户自选项，非默认，三风格通用）**：仅当用户明确要深色/暗色/夜晚/低调氛围时使用。**核心是轻盈通透、不弱化主体——深色不等于越暗越好。**
  - 饱和度：一律尽量低饱和；不用纯黑、不用高饱和荧光色；暗部保留纸面颗粒与一丝柔和反光，不糊成死黑一片；
  - **明度按"背景是否为主体互补色"分情况**：
    · **互补/强对比色背景**（如黄柠檬配藏蓝、红果配墨绿）：色相差本身托住主体，背景明度高低皆可，低明度也成立；
    · **邻近色/间接色/同系色背景**（如黄柠檬配暖棕、红果配酒红、绿果配墨绿）：缺少色相对比，背景明度要**适当抬高**——用中等偏深、带灰调的深彩色，而非极深沉色；否则"低明度＋邻近色"会把主体吞掉、画面厚重闷滞、不通透；
    · **主体极浅/近白**（奶油白蘑菇、白蒜、白瓷）：与任何深底都有强明度差，背景明度自由度大；
  - 参考深度：互补色或近白主体可用 #2E3A33 / #2C2E38 这一档；邻近色背景再提亮 1–2 档（如 #4A463F / #554A3C 量级的灰彩色），宁可轻一点不要压死；
  - 主体：提亮受光面、厚涂，保证在深底上最先被看见；
  - 文字：主标题与次要文字用奶油白/暖白；由 `overlay_text.py` 自动对比选浅色，保证清晰；
  - 正例：藏蓝×黄柠檬（互补、可深）、墨绿×奶油白蘑菇（主体近白）；反例提醒：暖深棕×黄柠檬属邻近色，棕底明度压太低会显厚重，应抬高棕底明度。
- **禁止（深浅皆然）**：高饱和背景、纯黑/纯白死板平涂、背景抢主体；背景永远服务于突出主体。
## 4. 构图、视角与三条通用画面规则
### 4.0 构图法与视角
- 构图法：三分法（主体落三分线交点、留白方向放文字，最通用）；黄金分割（多元素美食）；对角线（酒瓶/长形器物）；二八律（极简分子/香氛，80% 留白）；对称居中（俯视 flat lay 首选，封面感）。
- 视角配对：俯视显陈列与图案美；平视显轮廓与情绪；45° 显立体与食欲；仰视显气势。两稿只要求"视角不同、版式不同"，**无默认组合**，按主体形态与画面美感灵活搭配、避免套路化（见 SKILL 第 7 步）。
### 4.1 主体必须突出（Style-1/2/3 通用铁律）
画面有且只有一个视觉英雄，主体是第一眼焦点：
- **体量最大、刻画最实/明暗对比最强、占据视觉中心或黄金位**；
- 次元素、道具、环境在体量、数量、清晰度、色彩权重上一律让位，**不得因数量多、铺得广而稀释或盖过主体**；
- 多物件场景先定英雄再摆配料，所有配料的朝向与排布向英雄收拢、围合或指向它，不另立视觉焦点；
- 规则冲突时优先级：**主体唯一、最大且最突出 ＞ 留白 ≥33% ＞ 次元素 ≤25%**。
### 4.2 同类多物的疏密节奏（Style-1/2/3 通用铁律）
同类出现多个时，排布必须"有聚有散、聚主散辅"：
- 多数个体聚拢成**一个主簇**（彼此挨靠、少量交叠、成组），只允许极少数（0–2 个）就近点散作呼吸；
- **禁止两个极端**：全部等距分散（松散、稀释主体）、全部挤成一团（板滞）；
- **散点距离受控**：散落个体与主簇间距不超过约该物体自身 1–2 个身位；过远的孤立散点没有意义，应收回主簇或删除；散点视觉上仍向主簇/英雄呼应，不另起中心；
- 一张画面同类通常只有一个主簇，不出现多个等权中心。
### 4.3 边缘柔化/晕染（Style-1/2/3 通用，用户可选项）
主体与次元素的边缘"是否柔化、晕染纸面"是一个**可开关、可分别指定**的选项：
- **用户点名时从其指定**（不柔化主体/主体锐利、全部柔化、全部锐利、只柔化某类次元素等）；
- **用户未指定时的默认（主体也柔，用虚实梯度拉开主次）**：
  - **主体边缘默认柔化、晕染**——湿画洇边/羽化、断续松线、背光面与贴背景处局部溶入纸面；但主体形体保持完整、受光侧轮廓清晰可辨（**柔而不糊、虚而有形**）。柔化的是"边缘用笔"而非弱化主体：主体仍靠体量最大、对比最强、占据视觉中心而最突出（服务 §4.1）；
  - **次要元素边缘默认比主体再柔、再虚一档**——更松更断、用笔更省、更多溶入纸面，但整体形体与受光轮廓仍可辨；背景/环境最柔。整体梯度为 **背景最柔 ＜ 次元素 ＜ 主体柔而最完整**；
  - **只有用户明确点名"主体不柔 / 锐利清晰 / 硬边"时，主体才保持清晰锐利的完整轮廓**（用 EDGE-SUBJECT-CRISP）；
- 媒介不同手法不同：Style-1 湿画洇边、Style-2 景深虚实、Style-3 干擦飞白松线，原则一致。
- **三风格共同前提（笔触铁律，见 style-profiles.md 公共段 §1.4）**：默认都不画深色/封闭外轮廓线，形体靠色块自身边缘成形；本节的"柔化/晕染"作用的正是这些色块边缘——即便点名"主体不柔/锐利清晰"，也只是让色块边缘更肯定、完整，**而不是加一圈细黑描边**。
## 5. 提示词骨架
可拼装模块（媒介段/主体突出/疏密/边缘/景深/背景/文字留白/无文字尾）统一见 `references/prompt-blocks.md`，出图时按槽位组合，避免每次重写与漏约束。通用骨架：
```
[风格/笔触模块], [视角] view of [唯一主体+状态+固有色],
[1–2 个次元素，按 §4.1/4.2/4.3 组织], on/in [背景色+纹理],
[构图法+摆位], generous margins, ≥1/3 clean negative space,
[TEXT-BLANK：画面无字，标题与次要文字区域保持纯净平涂背景、不画任何笔画痕迹],
muted editorial color palette true to the object's real color,
high-end magazine / graphic-design aesthetic, soft natural light,
absolutely no text, no letters, no numbers, no watermark
```
例（绿葡萄俯稿）：
`watercolor and colored-pencil editorial illustration, top-down flat-lay view of one lush bunch of fresh shine-muscat green grapes with two loose berries and a single vine leaf, on warm ivory textured paper, centered symmetrical composition, generous margins, at least one third clean empty space, blank top-center band and a clean lower-right corner kept as pure smooth background, natural fresh green palette true to real grape color, high-end magazine aesthetic, soft natural light, absolutely no text no letters no watermark`
## 6. 文字系统与 overlay_text 用法（SSOT 唯一权威）
**本节是主标题与次要文字全部规则、参数、字体别名、自动对比选色与命令用法的【唯一权威完整版】，对 Style-1/2/3 一律生效、逐条完全一致：三种风格的每张成品都必配"主标题 ＋ 次要文字（一句短诗，并独立另加季节、拉丁学名两行）"，不存在无文字的风格。主标题与次要文字一律由 `overlay_text.py` 后期合成，生图阶段不生成任何文字。** 次要文字（短诗 ＋ 季节·拉丁学名）写法规范见本节 §6.5.1–6.5.3。
### 6.1 语言与文案
- **语言跟随使用者**：默认英文；用户用中文则中文。
- 主标题 = 主体名称（英文以一个词或简短词组为宜；中文 2–4 字）；因一律 PIL 叠入、不再让模型手写，故无"单词 ≤7 字母"之类拼写限制。
- 次要文字默认含两部分：**(A) 一句 2–3 行短诗**（英文每行 3–6 词、中文每小句 5–9 字，守"信达雅"，写法见 §6.5.1）；并**独立另加 (B) 两行——第一行季节、第二行拉丁学名**（写法、范例与学名准确性见 §6.5.2），用户可只保留其中一部分。**A、B 之间用一个空行分界、段距=次要字高 2.5 倍；英文排版 B＝英文大写季节＋英文大写学名，中文排版（主标题与短诗均中文）B 只留一行中文季节、不生成学名；短诗保持正常大小写。**
### 6.2 实现路径（唯一：PIL 后期合成，已取消 AI 手写）
- **主标题与次要文字一律由 `overlay_text.py` 后期叠入，生图模型不生成任何文字/字母/数字**（不再保留"AI 模型手写标题"路径）。
- 提示词统一要求画面无字：在上方居中为主标题、在对角/一侧为次要文字预留干净留白区；留白区保持与背景一致的纯净平涂、不画任何笔画/字母/痕迹（删诱导句后由生图模型留空、PIL 后期叠字）（用 prompt-blocks 的 TEXT-BLANK 与 NO_TEXT 模块）。
- 收益：字形、拼写、排版完全可控，无拼错/丑陋风险，中文与长词组同样稳定。
### 6.3 主标题排法（五种平等、每次随机，不设默认）
- `--title-style` 五选：`normal`（正立、baseline 平正、大小均匀）/ `italic`（统一微斜）/ `wave`（波浪）/ `arch`（弧形上拱）/ `scatter`（逐字大小旋转错落）。
- **五者地位完全平等、均为可选项，不设默认——每次在五者中随机选一种，normal 也只是平等选项之一、不再是默认**；用户点名排法时从其指定。
- 自由摆放 `--title-xy "45%,28%"`（块中心）、`--title-rotate`；中文 `kai` 可 `--vertical` 竖排配一枚红色小印章。
### 6.4 主标题位置与大小
- **位置：上方居中（top-center）优先级最高、默认采用**；仅当上方居中确无干净可用空间时才改其他方位。
- 主标题与主体/次元素**轻微重叠时，只要文字仍清晰可辨、主体识别与阅读不受影响（可视性、可读性成立），就保持原位，不主动挪动、也不为此重排画面；可读性受损是挪位的唯一理由。**
- 字块占版面（`--title-width`，默认 **0.30**），字距稀疏（`--letter-spacing` 默认 0.08）。
### 6.5 次要文字（短诗 ＋ 季节·拉丁学名，始终 PIL，三风格通用）
- **永远由 `overlay_text.py` 叠加、不交给生图模型**：一句短诗（写法见 §6.5.1）后接季节块；短诗与季节块之间用一个空行（`` `n`n ``）分界，一起传入 `--subtitle`；**分界处段距=次要字高的 2.5 倍（`--subtitle-section-gap` 默认 2.5）**。英文排版：空行之后的季节、学名自动转英文大写（`--no-upper-section` 可关，中文不受影响）；**中文排版（主标题与短诗均中文）：季节用中文、不生成拉丁学名**。短诗本身保持原大小写。中文次要文字因 Courier 无中文字形，脚本自动回退到 kai（楷体）渲染、不出现空心方框；正因如此，**中文排版主标题不要用 kai，改用 serif（宋体）/hand（行楷）/sans**，保证主、次字体不同（脚本按回退后的实际字体拦截相同搭配）。
- `type` 打字机体（与主标题字体**必须不同**；中文可用 sans/type）。
- 字高为主标题字高的 **18–36%**（`--subtitle-ratio`，默认 **0.25**），字距收紧（`--subtitle-tracking` 默认 -0.06）。
- 位置默认与主标题对角（`--subtitle-pos follow`）；上方次文默认落在标题带下方约 y=26% 处，避免与大标题同带交叠，其余方位按实际留白定；压主体时用 `--subtitle-xy "50%,90%"` 微调，允许与主体穿插、斜放，底线是主体与文字都清晰可读。
- **颜色必须与落点背景对比清晰、绝不融底（硬规则）**：默认省略 `--subtitle-color`，脚本采样落点背景亮度自动选深棕字（浅底）或暖白字（深底）；确需手填时浅底用 #6b6b66/灰紫/赤陶、深底用暖白，明度差不足脚本会自动纠正并提示；落点深浅不一时脚本警告，应把次要文字移到干净留白区。主标题颜色取主体固有色 HEX（`--color`）。
- 叠完必须回读确认各行文字清晰、不融底、不压主体；偏小或不清则调大 `--subtitle-ratio` 或更换落点后重叠。
#### 6.5.1 短诗写作规范（信、达、雅）
- **信**：只写与主体真实特征相关的意象（颜色、香气、触感、季节、光影），不写违背常识的内容；
- **达**：语法干净、可朗读，英文避免机翻腔与生词堆砌，中文避免口号与成语堆砌；
- **雅**：留白与余味，克制、温柔、具体；2–3 行、英文每行 3–6 词（中文每小句 5–9 字）；
- 优先从一个小切口进入（一颗果粒、一束光、一个下午），不写"大自然多么美好"式空话。
- 范例：
  - 葡萄（英）：A cluster of green sunlight, / sweet with the hush of summer.
  - 石榴（英）：Red as a secret, / each bead a small bright hour.
  - 洋葱（英）：Layer after quiet layer, / the kitchen fills with gold.
  - 葡萄（中）：把夏天的光，/ 一粒粒串甜。
  - 石榴（中）：满腹红宝石，/ 咬开是秋天的一声轻响。
#### 6.5.2 季节 ＋ 拉丁学名写法（在短诗之外另加，随语言模式分两种）
先定语言模式（与主标题、短诗一致）：
- **英文排版（主标题、短诗为英文）**：季节 ＋ 学名共两行，均英文大写。
- **中文排版（主标题与短诗为中文）**：只加**一行中文季节、不生成拉丁学名**（无学名行）；短诗与中文季节之间仍留 2.5 倍字高段距。
1. **季节行**：写主体当造/成熟/应季季节而非画面天气，两稿统一。主体的应季月份可查 `seasonal_produce_index.json`（JSON 优先）或 `seasonal-produce-index.md`（SSOT）的「成熟」字段作为事实依据（季节词写法与中英取舍仍以本节为准）。
   - 英文排版用**英文大写短语**：EARLY SPRING / LATE SPRING / EARLY SUMMER / HIGH SUMMER / LATE SUMMER / EARLY AUTUMN / LATE AUTUMN / EARLY WINTER；用户指定节令（如 CHRISTMAS、HARVEST）也用英文大写。
   - 中文排版用**中文季节词**：初春 / 晚春 / 初夏 / 盛夏 / 夏末 / 初秋 / 晚秋 / 初冬；用户指定节令（如秋收、中秋）从其指定。
2. **学名行（仅英文排版生成；中文排版不生成）**：先用规范学名核对准确性（属名首字母大写、种加词小写、惯例斜体）；**叠到画面时整行全部英文大写、正体**（脚本对空行之后的行自动 `.upper()`，中文不受影响）。核对用学名 → 画面大写示例：樱桃 *Prunus avium* → PRUNUS AVIUM、葡萄 *Vitis vinifera* → VITIS VINIFERA、无花果 *Ficus carica* → FICUS CARICA、石榴 *Punica granatum* → PUNICA GRANATUM、柠檬 *Citrus limon* → CITRUS LIMON、番茄 *Solanum lycopersicum* → SOLANUM LYCOPERSICUM、香菇 *Lentinula edodes* → LENTINULA EDODES、甜椒 *Capsicum annuum* → CAPSICUM ANNUUM、黄瓜 *Cucumis sativus* → CUCUMIS SATIVUS、草莓 *Fragaria × ananassa* → FRAGARIA ANANASSA。
3. **准确性硬要求**：学名必须正确，**不臆造、不拼错属种**；不熟悉或拿不准先检索核实再写，查不到可靠学名时宁可只写季节一行并向用户说明，也不编造。
4. 季节（与学名）都要与主体真实属性一致（不反季节、不张冠李戴）；用户自拟次要文字时从其指定。
- 完整次要文字示例（短诗 ＋ 空行 ＋ 季节块）：
  英文排版（短诗 ＋ 空行 ＋ 大写季节 ＋ 大写学名）：`A handful of June,` / `bright as a red wish.` /（空行）/ `EARLY SUMMER` / `PRUNUS AVIUM`；
  中文排版（短诗 ＋ 空行 ＋ 中文季节，**无学名**）：`把初夏的光，` / `一粒粒串甜。` /（空行）/ `初夏`。
#### 6.5.3 由画面推导·去套路（主标题同样适用）
主标题、季节、短诗都必须**先分析本图画面再决定**——先看清主体是什么（种类 / 颜色 / 形态 / 数量）与次要内容（容器、搭配物、承载面、独有细节），再据此分别推导：主标题优先直接点主体（双 / 多主体可并列，或取其最强视觉关系），不用与画面无关、换到别的图照样成立的万能集合词（逢组合就用 HARVEST 即反例）；季节依主体**真实应季**而定、不一律套 LATE SUMMER，换季交界时在相邻两季里选更贴切者；短诗从本图主体或次要物的**具体**特征找小切口（可带入该图独有细节，如网袋、切面、饮品、花器），不重复上一张的意象与惯用句式（summer light / gathered / quiet harvest 之类不连用）。三者都要与本图强绑定、不可原样套到另一张图；同一连续多图任务中，相邻作品的主标题、季节词、诗句措辞都要明显不同。
### 6.6 字体别名
- 主标题从 **kai=楷体、hand=行楷、serif=宋体/衬线、sans=雅黑/黑体** 中按风格选用（**已取消 marker 蜡笔手写**）：高级/棱角器物常用 serif，亲和/现代可用 sans，中文用 kai/hand。
- 次要文字用 **type=Courier New（打字机）**；主/次字体必须不同。
- 自有字体放 `assets/fonts/`（.ttf/.otf），缺省回退系统字体。（脚本内 marker 别名仅为向后兼容保留，规则上不再选用。）
### 6.7 命令（主标题＋次要文字一次叠入）
主标题与次要文字在同一条命令叠入；两稿各跑一次（参数一致、仅 `--subtitle-xy/--title-xy` 按各自留白微调）。
```powershell
python scripts/overlay_text.py outputs/cherry.png `
  --title "CHERRY" --title-font serif --color "#b32027" --title-width 0.30 --title-pos top-center `
  --title-style arch `
  --subtitle "A handful of June,`nbright as a red wish.`n`nEARLY SUMMER`nPRUNUS AVIUM" --subtitle-font type --subtitle-ratio 0.22 --subtitle-xy "50%,88%" `
  -o outputs/cherry_final.png
```
- 上例 `--subtitle` 依次为：短诗两行 ＋ **一个空行分界** ＋ 季节 ＋ 拉丁学名（显示 4 行，短诗与季节之间留 2.5 字高段距）；空行后的 EARLY SUMMER、PRUNUS AVIUM 自动英文大写（季节、学名固定大写，短诗保持正常大小写）；只想要季节·学名时删掉短诗两行与空行即可，反之亦然。
- `--title-style` 用户指定优先，无指定时从 normal/italic/wave/arch/scatter 随机取一（不设默认）；中文主标题 `--title-font kai`（可加 `--vertical` 与一枚红印章）；英文排版季节、学名英文大写，中文排版（主标题与短诗均中文）季节用中文、不生成学名。

---

## §7 生成后目检清单（步骤8 校验）

### 7.1 校正与目检流程

直接把成图 URL 交给 `scripts/prep_images.py --text-scan`（可一次传多个 URL），一步完成下载＋校正到目标画布＋取色＋伪文字辅助扫描，不必先单独 curl 下载；输出命名：单源就是 `--prefix` 原值（如 `prefix.png`），多源才依次加 `_A/_B`——后续 overlay 的输入文件名按此写，勿给单源误加 `_A`。

随后只对校正后的图用 Read 逐张目检（一次完成、不重复读原图）：

### 7.2 目检清单

- **主体唯一且最大**、第一眼最突出，配料向英雄收拢；同类"一个主簇＋近距点散"、无等距散排/远距孤点；
- **边缘虚实**符合指定（默认主体柔化但形可辨、次元素更柔，柔而不糊；点名不柔才给主体硬边）；
- **固有色**符合实物、色彩总律已执行（色相丰富但整体中低饱和、高饱和只小面积点睛）；
- **笔触**守 style-profiles.md 公共段——平涂色块成形、无深色封闭描边、近乎平光（一块略深同色＋一点高光、基本无落地投影）、不多层渐变；
- **层级遮挡**与接触深色到位；状态叠加自然（若用）；
- **配角类别数**与 cast 档位一致（0–5 类）、逐类更小更柔、向主体 1–2 身位收拢、无等距撒满/远距孤点、每个配角有明确承载面不悬空、无第二焦点；
- **留白边距**充足；背景规则已执行；
- **数量逐项实数**（几橙几柠等，不符立即重生成该张）；
- **画面无任何 AI 直出文字/字母**（主标题与次要文字都在后期叠）。

### 7.3 伪文字检测 + 自动重生

（image_edit 场景必做，image_gen 场景建议做）

1. **辅助检测**：`prep_images.py --text-scan` 启发式扫描疑似文字区域（边缘密度/高对比度块横向排列特征），输出警告（仅辅助提示，以 AI 目检为准）；
2. **AI 目检（主检测）**：Read 校正图，仔细检查是否有文字/字母/数字/水印/logo/装饰横线/角框/伪手写文字/标签/签名，特别关注画面边缘、角落、主体表面、背景纹理处；
3. **发现伪文字后自动重生一次**：不修改其他设定，只在 pv_en 末尾加强文字否定约束，用加强后的提示词重新生成该张（另一稿保留）。加强提示词模板：
   `do NOT generate any text, letters, numbers, watermarks, logos, signatures, frames, labels, tags, or handwriting; the image must be completely text-free with zero characters; no printed text, no handwritten text, no decorative lettering, no numbers anywhere`
4. **重生后再次目检**：文字消失则继续流程；仍有文字则再重生一次（最多 2 次），第二次可同时换视角或减少复杂元素；超过 2 次仍有文字则换思路（换构图/换视角/减少元素/换主体），或接受并在后期用修复工具去除。


---

## §8 色块后处理（可选，用户点名"色卡/配色板/提取颜色"才做）

### 8.1 用途与触发

- **用途**：从成品图动态提取主色（默认最多 10 种），渲染单条横向色块带，可选标注颜色名/HEX，作为配色参考卡附在成品上或独立输出。**纯 PIL 实现，颜色名来自内置 `color_names.json` 最近邻匹配，禁止模型生成颜色名**。
- **触发**：用户说"加色卡/配色板/提取颜色/color palette"时，在叠字完成后对 final 图执行；不点名则不做。

### 8.2 命令与参数

```
python scripts/color_palette.py <final图> --max-colors 10 --pos auto --label name -o <输出>
```

- `--max-colors`：最多提取主色数量（默认 10；排除背景色并去重后取前 N）
- `--pos`：top 顶部 / bottom 底部 / auto 自动在上下留白带中选更干净的一侧（默认）
- `--label`：none 不标注（默认）/ name 颜色名 / hex
- `--swatch-w` / `--swatch-h`：单色块尺寸(px)，默认 90×20
- `--margin-px`：色带距上下边界边距(px)，默认 120
- `--font`：标注字体，默认 type=Courier（仅 `--label` 非 none 时生效）
- `--batch <目录>`：批量处理目录下 `*_final.png`（直接覆盖原文件）

### 8.3 规则

- 色带为单条横向排列，按明→暗左→右排序（块数 = 提取主色数，上限 `--max-colors`）；
- `--pos auto` 自动在上下留白带中选更干净的一侧，不压主体/次元素，也可强制 top/bottom；
- 颜色名/HEX 标注用打印机字体（type=Courier），默认不标注（--label none）；
- 色块尺寸固定像素（默认 90×20，`--swatch-w/--swatch-h` 可调），不随版面比例缩放。
