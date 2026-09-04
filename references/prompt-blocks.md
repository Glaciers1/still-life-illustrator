# 提示词模块库（Prompt Blocks · 拼装即用）
> 出图不再每次手写长 prompt：按下面顺序"选模块 + 填主体"拼装即可，**通用约束（主体突出/疏密/边缘/无文字）会随模块自动带上，不漏约束**。规则定义见 `layout-and-composition.md`（下称 LAYOUT）对应小节，本文件只给可直接粘贴的英文片段。
>
> **拼装顺序**：`[NO_TEXT 全局否定·放最前] + [MEDIUM] + [PALETTE 色彩总律·默认带] + [VIEW 视角] + [SUBJECT 主体+结构] + [HERO] + [CLUSTER(有同类多物时)] + [EDGE] + [PROPS/DEPTH（配角类别数按 `composition-cast.md` 组合档位：Solo=0 类只留承载/光影，Duo~Lush=1~5 类）] + [BG] + [LIGHT] + [COMPOSE 构图留白] + [TEXT-BLANK 预留叠字区域]`
> 两稿必须在**同一次调用的同一 request_list** 里提交，只换 VIEW/COMPOSE，其余模块完全一致以保证统一。
---
## 0. PALETTE 色彩总律（三风格通用、默认每张都带；色相丰富 + 局部高饱和 + 整体中低饱和）
**目标：色系尽量丰富，但画面整体观感是中低饱和——高饱和被允许，却只占小面积。**
1. **色相丰富**：可跨多个色相族铺陈（绿/黄/橙/红/紫…），不把画面限制在单一色系；
2. **允许高饱和**：主体的受光/关键部位、或**某一个次要元素**，可用较高饱和（vivid/saturated）如实画出固有色，不必把每块颜色都灰化；
3. **整体仍中低饱和**：高饱和只作小面积点睛（**合计建议 ≤ 约 10–15% 画面**），大面积背景、多数元素与中间调保持中低饱和、整体灰化一度；用"大面积低饱和托小面积高饱和"拉开层次。远看/全局统计仍是安静的中低饱和画面。
4. **侘寂优先条件**：当画面整体中低饱和、且**中式元素占比偏高**（青瓷/紫砂/竹编/宣纸/茶盏/中式糕点/腊梅·山茶·桂花等中式花卉/腊肉·腊肠等中式食材）时，色调氛围优先偏 **wabi-sabi 侘寂**：暖灰米白为底、器物带粗陶/哑光质感、光影柔和留白多、避免鲜亮对比；用 `muted earthy palette, warm gray-ivory base, matte ceramic texture, soft diffused light, generous negative space, quiet wabi-sabi atmosphere` 一句锚定。
- 边界：避免高饱和大面积铺满、避免多块高饱和互相打架；禁廉价荧光（neon，荧光≠高饱和）。用户明确要"更鲜艳/浓郁"时，高饱和占比可上调到约 20–25%，但仍以中低饱和为底、不铺满。
- 与 MEDIUM 关系：M1/M2/M3 里的 `muted/Morandi` 指**整体基调**，以本条为准——它不禁止局部高饱和，二者不冲突。
- 默认片段（机器锚点，build_from_brief.py 解析，勿删注释）：
<!--block:PALETTE-->
`rich multi-hue palette spanning several color families; the OVERALL frame stays predominantly middle-low saturation and slightly grayed, BUT selective small areas are allowed to be vivid and high-saturation — a saturated highlight on the hero or on ONE secondary element as an accent; all vivid areas together cover only about 10-15% of the frame, balanced by much larger desaturated areas, calm low-saturation read at a glance, no all-over vivid wash, no clashing saturated blocks, no neon`
- 加浓变体（用户要更鲜艳）：把片段里 `about 10%` 改为 `about 20–25%`，其余不变。
## 1. MEDIUM 媒介段（按选定风格三选一）
- **M1（Style-1 水彩蜡笔）**
  <!--block:M1-->
  `naive picture-book watercolor with crayon/colored-pencil grain on visibly textured cotton paper, built almost entirely from simple FLAT color blocks laid side by side (one local base color per part, blocks assemble the shape); a block may carry a single-pass watercolor bloom, pigment sediment or dry-crayon grain, but NO layered gradient, NO hatching, NO repeated blending or smoothing; nearly flat even light — form comes only from one slightly deeper same-hue block for the side/overlap, one small wet-in-wet warm touch near the stem or lit side, and a couple of tiny restrained highlights, with almost NO cast shadow; NO dark or closed outline — shapes are defined by the color blocks themselves, with hand-wobbly bleeding watercolor edges, water marks and light dry-brush fraying instead of clean vector edges; the ONLY allowed lines are (a) same-hue broad brushy bands enclosing a left-white interior, (b) broken dotted/dashed edge marks, or (c) at most one same-hue thick stroke separating inner structure — never a smooth thin black contour; neighboring blocks meet through a sliver of left paper-white / a reserved white line or one slightly deeper same-hue patch (which is also the contact shadow), never a black line; seeds, pits, thorns, spots, pores, veins and other details are just a few same-hue darker small dots or short dabs; white/pale parts simply leave the paper white (or one very pale wash); rounded, chunky, childlike, quiet and hand-made; a vivid high-saturation playful variant is allowed but still stays flat and blocky; illustrative, NOT photorealistic, NOT digitally smooth, NOT airbrushed`
- **M2（Style-2 叙事编排）= M1 笔触 + 编排**：先用 M1 全文，再接：
  <!--block:M2_EXTRA-->
  `narrative editorial still-life staging, illustrative and painterly (NOT a photograph), one hero whose color is repeated on one matching natural element, objects held in/on a container, single directional light with a graphic cast shadow, clear foreground/middle/background depth, [mood: quiet morning / cozy candlelit night / fresh summer]`
- **M3（Style-3 色粉油画棒）**
  <!--block:M3-->
  `soft pastel and oil-pastel still life on visibly textured kraft-grain paper, built mainly from FLAT scumbled color blocks laid side by side (one local base color per part, a single dry pass letting paper fiber and chalky grain show through); NO closed dark outline — shapes form from the dry color blocks themselves, with loose broken colored-pencil marks that never fully close as mere hints (never a smooth sealed contour); soft diffused near-flat light with no hard shadows — volume comes only from one slightly deeper same-hue scumbled block plus a couple of tiny light-crayon highlights (light/mid/shade in just one or two same-hue blocks each, fewest strokes, no burnished gradient, no piling grain for detail); white/pale parts simply reserve the paper or one opaque light-crayon pass; details are a few same-hue darker small dabs or short dry strokes; neighboring blocks meet via a sliver of reserved paper or one slightly deeper same-hue patch, never a black line; thick opaque crayon only describes covering power on pale objects, not multi-layer buildup; hand-drawn warmth, NOT watercolor, NOT digital smooth, NOT photorealistic`
## 2. VIEW 视角（两稿各选一个、互不相同）
- 正俯视：`straight top-down flat-lay (90-degree) view`
- 45°：`three-quarter high-angle (about 45-degree) view`
- 平视：`eye-level frontal view`
- 微仰（瓶/高物）：`slight low-angle view`
## 3. SUBJECT 主体 + 结构（按 subject-structure.md 结论填）
`ONE single [subject] as the hero: [整体形态], [几层遮挡/谁挡谁], natural size/orientation variation (parts differ 15–30%, not identical), slightly deeper saturated contact shadows where parts meet or overlap, [表面识别特征，点到为止], suggested in a few flat color blocks`
- 状态叠加（三风格通用，可切割主体默认随机选用一类，共8种）：`one whole [subject] together with one [halved cross-section / sliced / cut into large pieces / diced into small cubes / julienned into thin strips / peeled / shelled] [subject] showing [inner structure: seeds, flesh texture, juice, meat grain], both on the same surface, touching or adjacent, same color family, counted as ONE hero category not two props`
  <!--block:STATE_OVERLAY-->
  `one whole [subject] together with one [state_type] [subject] showing [inner structure: seeds, flesh texture, juice, meat grain], both on the same surface, touching or adjacent, same color family, counted as ONE hero category not two props, realistic natural proportions not exaggerated`
## 4. HERO 主体突出（多物件场景必带，LAYOUT §4.1）
<!--block:HERO-->
`THE HERO is the unambiguous largest and most defined element at the visual center (about one third of frame), with the strongest contrast and focal weight (its edges are softened per EDGE, not hard); every prop is smaller, softer and subordinate, oriented/grouped toward the hero; nothing competes or sets up a second focal point`
## 5. CLUSTER 同类疏密（同类≥2 个时必带，LAYOUT §4.2）
<!--block:CLUSTER-->
`the [same-kind items] form ONE tight main cluster — packed closely, touching and slightly overlapping as a single compact group, with at most one piece set a short controlled step away (within 1–2 of its own size); NOT evenly spread apart, NOT one solid heap, no isolated far-flung pieces`
- 精确数量：在前面写明 `exactly three ... and exactly two ...`，并在词后括注 `(count carefully)`。
## 6. EDGE 边缘虚实（默认模块，LAYOUT §4.3）
- **EDGE-DEFAULT（默认：主体柔化可辨、次元素更柔、背景最柔）**
  <!--block:EDGE-->
  `EDGE HIERARCHY: the hero itself is painted with SOFT feathered bleeding edges — loose broken outlines, shadow-side edges feathering and partly melting into the paper — yet its overall shape and light-side contour stay clearly readable and it keeps the strongest contrast and focal weight; every secondary object is one level softer still (more broken, more faded), and the background/ambient is softest; soft, not blurred into nothing`
- **EDGE-SUBJECT-CRISP（仅用户点名“主体不柔/锐利清晰”时替换上者）**
  `keep the hero subject's outline crisp, clean, confident and complete, with no edge softening on the subject, while secondary props keep soft bleeding edges; the subject stays clearly defined`
- **EDGE-ALL-CRISP（仅用户点名全部锐利时）**：`all objects have clean confident outlines, no softening`
## 7. PROPS / DEPTH 次元素·容器·景深（配角类别数按组合档位，见 composition-cast.md）
> 配角**不再固定 1–2 类**：先按 `composition-cast.md` 定 cast_size（1–6），secondary = cast_size−1 类（Solo 时为 0 类）。每类都写精确数量、承载面与"比主体更小更柔"。
- **Solo（0 类配角）**：不写任何 accent prop，只用下面的容器承载/光影/前景虚化托画面，主体可放大到 45–50%。
- **Duo（1 类）**：`one small accent ([name], exactly N), clearly smaller and softer than the hero, resting on [surface] within one body-length with a soft contact shadow`
- **Standard（2 类）**：`two small accents ([a] exactly N, [b] exactly N), each smaller and softer, grouped close around the hero within 1–2 body-lengths`
- **Abundant / Bountiful / Lush（3–5 类）**：逐类列出 `exactly N`，并必带收拢层级句：
  `all supporting groups cluster tightly around the hero within 1–2 body-lengths, each group in order smaller, softer and lower-contrast than the last, no second focal point, generous negative space kept`（类别越多、分布半径越收，禁等距撒满，仍保 ≥1/3 留白）
- 容器承载（不算配角类别，任何档位可用；清单依据旬物索引 374 条（五区）高频搭配，每次随机选 1 个）：`held in/on a [wooden cutting board / white porcelain plate / white porcelain shallow plate / white porcelain long platter / white porcelain shallow bowl / rustic ceramic small bowl / rustic ceramic shallow basin / rustic ceramic shallow plate / woven bamboo basket / shallow bamboo basket / plain white small dish / plain white ceramic pot / glass bowl / glass cup / glass bottle / enamel basin / linen cloth bag / celadon vase / wooden tray / wooden bowl / wooden fruit crate / coffee cup / tea cup / unglazed ceramic shallow basin ...] that catches the hero, believable contact point and soft contact shadow`
- 前景虚化：`one soft out-of-focus [veil/leaf/petal/rim] entering at [edge], heavily blurred, no inner detail, translucent tint bleeding into the paper, framing the view`
- 背景虚化：`blurred soft [scene] background as broad color patches, no fine detail`
- **物理着附（每类配角必守）**：写清放在哪个水平面/器皿里/靠在谁身上，接触点给 contact shadow；禁悬空、禁贴纸式糊在主体正面。
- 搭靠/穿插须遵守 subject-structure.md「搭靠层级规则」（来向被挡、唯一接触点受力、同色前后分离、垂挂一侧）。
- **容器承载合理性**：容器必须适配主体物理形态——蛋糕/甜点→瓷盘/玻璃盘/纸托/石板（不入编篮、不进深碗）；汤/液体→碗/杯/盅（不入浅盘、不搁布面）；花卉→花瓶/玻璃瓶（不入浅盘）；整果/坚果→果篮/果盘/碗（不进高脚杯）。完整匹配表见 composition-cast.md §6.1；用户指定容器时，主体选择必须反过来适配该容器。
## 8. BG 背景（规则见 LAYOUT §3）
- BG-LIGHT（默认）：`on warm ivory textured paper (or [指定浅色]), with one or two large pale [subject-hue] color-washes blooming softly with feathered bleeding edges`
- BG-COMP（主体偏白撞色）：`on a muted low-saturation complementary paper [#HEX], high-key, making the pale subject stand out`
- BG-DEEP（仅用户要深色）：`on a desaturated deep [#HEX] background kept airy and translucent (not pure black, no neon), hero lit to stand out, leave clean areas for light-colored typography`
- Style-3 追加：`with a low dry-brushed ground band in the lower quarter as baseline`
## 9. LIGHT 光影（Style-2/有环境时）
- 硬侧光+图形影：`single hard side light, crisp cast shadow used as a graphic shape ([window-grid / branch / blind shadow])`
- 斑驳光：`dappled sunlight through foliage, a few irregular soft-edged warm-light and cool-shadow washes`
- 散光（Style-3 默认）：`soft diffused light, no hard shadow, a small dry shadow under each object`
- 夜晚：`cozy candlelit night, surroundings darkened but the hero stays the brightest, airy not heavy`
## 10. COMPOSE 构图与留白
`[centered symmetrical / rule-of-thirds off-center / diagonal / 80-20 minimal] composition, generous margins (subject away from all edges), at least one third clean empty negative space`
## 11. TEXT-BLANK 无字留白（唯一方式，规则见 LAYOUT §6）
主标题与次要文字一律后期 PIL 叠加，**生图阶段不生成任何文字**，统一用本段预留两处干净区：
<!--block:TEXT_BLANK-->
`keep a clean empty horizontal band across the top center for a later title, and keep the [spot] corner as perfectly smooth, even, empty background wash identical to the background, with nothing drawn there`
（中文标题同样走后期，不在画面写字。）
## 12. NO_TEXT 全局否定（必带·建议放提示词最前）
<!--block:NO_TEXT-->
`absolutely no text, no letters, no numbers, no watermark, no logo, NO frame, NO signature, absolutely NO TEXT on the image`
## 13. QUALITY_ANCHOR 质量校准段（长批次每5张自动注入一次，防质量退化）
> 长批次渲染时，模型对重复约束的注意力会逐渐下降，导致主体不突出、边缘变硬、伪文字增多。每5张在提示词末尾注入本段，简短重申核心约束，相当于"质量校准"。单张/小批次（<5张）不需要注入。
<!--block:QUALITY_ANCHOR-->
`QUALITY REINFORCEMENT: hero remains the unambiguous largest and most defined element at the visual center with strongest contrast; every secondary object visibly smaller, softer and receding toward the hero within 1-2 body-lengths, resting firmly on the surface with contact shadows, no floating no second focal point; edges stay soft feathered and bleeding, no hard outlines, background softest; the reserved blank areas remain completely empty and texture-free, no letters no marks no watermark; overall frame stays middle-low saturation with only small vivid accents, calm and quiet read`
---
## 组装范例（Style-2 · 香水英雄 · 两稿同批）
> NO_TEXT(全局否定前置) + M2 + VIEW + SUBJECT(香水瓶) + HERO + CLUSTER(柑橘青柠) + EDGE-DEFAULT + PROPS(佛手花枝/波点毯/白纱前景/草地) + BG-LIGHT + 斑驳光 + COMPOSE + TEXT-BLANK。两稿只把 VIEW 与摆位换成 `45°瓶直立、果簇瓶脚左前` / `90°瓶居中、果簇瓶上方`，其余逐字一致。完整实例可回看本会话 PARFUM 野炊图。
## 速记：哪些模块"必带"
- 任何图：NO_TEXT（全局否定·放最前）、MEDIUM、VIEW、SUBJECT、COMPOSE、TEXT-BLANK（预留叠字区域）。
- 多物件：HERO；同类多件：CLUSTER；想拉开主次：EDGE-DEFAULT（已为默认）。
- 有环境/承载：PROPS + BG + LIGHT；**Solo 单一主体大留白：不写配角，只用承载/光影/前景虚化，BG-LIGHT 即可**。
- 配角类别数由组合档位 cast_size 决定（1–6、secondary 0–5 类，见 composition-cast.md），不固定 1–2 类；多元素必带"向主体收拢、逐类更小更柔、无第二焦点"句。
