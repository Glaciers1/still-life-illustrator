# 组合档位（Composition Cast · 元素丰富度）

> **解决的问题**：避免每张都落入"一个主体 ＋ 固定 2–3 类配角"的死板套路。
> **不变的底线**：无论画面有几类东西，**主体（hero）永远唯一、确定、第一眼最突出**；变化的只是**配角类别数（secondary 条数，0–5）**。
> 本文件只决定"画面里有几类元素、它们如何分层聚拢"；主体突出/同类疏密/边缘柔化/色彩总律等铁律仍然全部生效（见 LAYOUT §4、prompt-blocks.md）。

## 1. 六档定义（总元素类别 = 1 主体 ＋ N 类配角）

| 档位 cast_size | 总类别 | secondary 条数 | 画面气质 | 典型题材 |
|---|---|---|---|---|
| **Solo 极简** | 1 | 0 | 大留白、单体雕塑感，靠器皿/衬底/光影/状态叠加撑画面 | 一枚果、单品海报、侘寂 |
| **Duo 双物** | 2 | 1 | 主体 ＋ 一个呼应物，干净有对话 | 果＋叶、杯＋豆 |
| **Standard 标准** | 3 | 2 | 主体 ＋ 两类配角，均衡（**不再是唯一默认**） | 常见果盘组合 |
| **Abundant 丰盛** | 4 | 3 | 主体 ＋ 三类配角，层次丰富仍有序 | 餐桌一角、采收篮 |
| **Bountiful 群像** | 5 | 4 | 主体 ＋ 四类配角，丰盛但有序 | 丰收宴、节庆长桌局部 |
| **Lush 极丰** | 6（硬上限） | 5 | 主体 ＋ 五类配角，最丰盛的市集/长桌/家宴感，靠前中后三层与逐类后退保主体 | 年节家宴、市集摊头、满桌茶点 |

- **硬上限 6 类**：超过 6 类必然稀释主体、制造第二个焦点，不再加；想更丰富应在"某一类内部增加数量/状态"，而不是继续加类别。
- `cast_size = 1 + len(secondary)`，brief 里必须显式写 `cast_size`，且与 secondary 条数自洽（校验门会拦）。

## 2. 怎么选档（无指定时）

1. **用户点名从其点名**："就画一颗""极简"→Solo/Duo；"丰盛一点""多些食材""一桌子"→Abundant/Bountiful。
2. **无点名按概率抽样**（避免总落 Standard）：Solo 12% / Duo 18% / Standard 28% / Abundant 22% / Bountiful 12% / Lush 8%。
3. **题材/季节可作合理偏离**（不是硬性）：早春、新芽、侘寂、单品广告偏 Solo/Duo；秋收、丰宴、菌菇/根茎大上市偏 Abundant/Bountiful/Lush。
4. **反重复**：连续两批不用同一档位；批量生成时回看最近 N 批（N≈8）的 `cast_size / hero / style / 视角 / 配色`，命中高度重叠就换档或换主体（批量历史去重见 `director-workflow.md §6.3`）。

## 3. 主体确定性（任何档位都不破）

- hero 只有一个，是**最大、最实、对比最强、占据视觉中心**的元素（建议占画面 30–45%；Solo 档可放大到 45–50% 以撑住空画面）。
- 类别越多，越要保证 hero 的体量/清晰度/聚焦权重明显领先；**每增加一类配角，该配角就更小、更柔、更后退、对比更低**，视觉权重严格排序：`hero > secondary① > ② > ③ > ④ > ⑤`。
- 绝不允许某个配角在大小、饱和度、清晰度上追平主体（那就是第二焦点，必须在生成前的方案里删掉或弱化）。

## 4. 多元素的空间组织（Abundant/Bountiful 必守）

- **向主体收拢，不许撒满**：每一类配角各自成一个小簇（同类仍守"一个主簇 ＋ 至多 0–2 个近距点散"，见 LAYOUT §4.2），所有小簇围绕主体、落在主体 1–2 身位内；**类别越多，分布半径越要收**，而不是摊得更开。
- **分组有疏密、不等距**：相邻小簇可挨靠微叠成"组团"，组团之间留呼吸；禁把每类东西等距摆一圈、禁均匀撒满整张桌。
- **留白不被突破**：即使 Bountiful，也至少保留 1/3 干净负空间与 ≥12% 边距（冲突时优先级：主体唯一突出 ＞ 留白 ＞ 配角数量，见 SKILL 步骤 5）。元素多就把单个元素画小、把组团压紧，而不是侵占留白和文字干净区。
- **前/中/后三层**：用 1 个前景柔化物（可选）、中景主体组团、背景大色块拉开纵深，避免六类东西全挤在同一平面。

## 5. Solo 档专项：没有配角怎么不空

Solo 不是"孤零零一个小物体"，而是把笔墨集中到主体本身，用以下手段托画面（这些算环境/承载，**不计入 secondary 类别**）：
- **承载与衬底**：从旬物索引高频搭配中随机选 1 个（不固定）——木质（wooden cutting board 木砧板 / wooden tray 木盘 / wooden bowl 木碗 / wooden fruit crate 木果筐）、白瓷（white porcelain plate 白瓷盘 / white porcelain shallow plate 白瓷浅盘 / white porcelain long platter 白瓷长盘 / white porcelain shallow bowl 白瓷浅碗 / plain white small dish 素白小碟 / plain white ceramic pot 素白陶罐）、粗陶（rustic ceramic small bowl 粗陶小碗 / rustic ceramic shallow basin 粗陶浅盆 / rustic ceramic shallow plate 粗陶浅盘 / rustic ceramic shallow bowl 粗陶浅碗 / unglazed ceramic shallow basin 素陶浅盆）、竹编（woven bamboo basket 竹编笸箩 / bamboo basket 竹编篮 / shallow bamboo basket 竹编浅筐）、玻璃（glass bowl 玻璃碗 / glass cup 玻璃杯 / glass bottle 玻璃瓶）、搪瓷盆 enamel basin、麻布袋 linen cloth bag、青瓷瓶 celadon vase、咖啡杯 coffee cup / 茶杯 tea cup；或一块布/纸、一道桌面基线，给出"安放感"；
- **主体自身状态叠加（三风格通用，可切割主体默认随机选用，共8种）**：整颗+剖半(halved) / 整颗+切片(sliced) / 整颗+切大块(cubed) / 整颗+切小丁(diced) / 整颗+切条切丝(julienned) / 整颗+剥皮(peeled，软皮) / 整颗+剥壳(shelled，硬壳/虾蟹贝坚果)（如完整三文鱼+三文鱼片/块/丁），两部分算一个主体类别（不破坏唯一性），同主体同色系有物理接触，剖面露内部结构，用内部结构丰富画面；可用状态以旬物索引cuttable_states字段为准；
- **光影与色晕**：一片柔和投影、一两笔主体同色的背景水痕、一道斑驳光；
- **一枚前景虚化**（可选）：焦外的叶/纱/器物边缘轻挡一角，增加层次；
- 主体适当放大、结构分析做足（subject-structure.md），靠形体质感而不是靠堆物。

## 6. 物理着附 / 接触合理性（所有档位，重点核查）

每个配角都必须"放得住"，这是上一轮审核（如八角悬空/贴错面）暴露的问题：
- 每个配角写清**承载面与接触关系**：放在桌面/盘中/布上，还是靠在主体侧、搭在容器沿；接触点给一小块接触阴影（contact shadow）。
- **禁悬空**（物体下方无承载面、像浮着）、**禁贴纸感**（直接糊在主体正面、无遮挡关系）；搭/靠/绕/垫遵守 subject-structure.md「搭靠层级规则」：来向去向上挡、唯一接触点受力微形变、同色前后用留白纸边/投影/点缀色分离。
- 小颗粒（八角、胡椒、散落果粒、坚果）要么落在明确的水平面上并带各自小投影，要么盛在器皿里，不粘在垂直的主体表面。

### 6.1 主体—容器匹配合理性（选承载面前必查）

承载面/容器必须与主体的物理形态适配，不能为了"好看"硬配。**用户指定容器时，主体选择必须反过来适配该容器**（如用户说"放在篮子里"就不选蛋糕/汤/液体类）。

| 主体类别 | 合理承载 | 不合理承载（避免） |
|---|---|---|
| 蛋糕/甜点/糕点 | 瓷盘、玻璃盘、纸托、石板、蛋糕架、木托盘 | 编篮、竹笸箩（会粘/漏/压坏）、深碗 |
| 汤/液体/饮品 | 碗、杯、盅、壶、玻璃杯 | 浅盘、编篮、布面（会洒） |
| 鱼/肉/海鲜 | 木砧板、白瓷长盘、烤盘、粗陶盘 | 高脚杯、小花瓶、纸托 |
| 整果/坚果/干货 | 果篮、果盘、碗、麻布袋、竹笸箩 | 高脚杯、纸托、深汤碗 |
| 叶菜/根茎菜 | 竹篮、粗陶盆、木砧板、搪瓷盆 | 玻璃高脚杯、精致瓷碟 |
| 花卉/花枝 | 花瓶、玻璃瓶、陶罐、水壶 | 浅盘、编篮（无根水会蔫） |
| 面包/烘焙 | 面包篮、木砧板、粗麻布、瓷盘 | 深碗、玻璃杯 |

- 匹配原则：**固形干货可入篮入袋，软质/流质/易碎物必须入盘入碗入杯**；容器深度与物体高度匹配（高物不搁浅盘，扁物不塞深碗）。
- 拿不准时优先选最通用的"瓷盘/木砧板/玻璃杯"三选一，不硬凹冷门容器。

## 7. 落到提示词（与 prompt-blocks.md 的衔接）

- 档位只改变 **SUBJECT 段的元素清单** 与 **§7 PROPS/DEPTH 段的规模**；MEDIUM / PALETTE / HERO / CLUSTER / EDGE / TEXT-BLANK / NO_TEXT 等公共段照常带、一字不改。
- 每类元素都写精确数量 `exactly N (count carefully)`；Solo 档不写任何 secondary，只写承载/光影。
- 多元素时在 PROPS 段补一句层级与收拢，例如：
  `all supporting groups cluster tightly around the hero within 1–2 body-lengths, each group smaller, softer and lower-contrast in order, no second focal point, generous negative space kept`
- 组装后自查：类别数==cast_size？主体是否仍明显最大最实？有无等距撒满/悬空/第二焦点？留白与文字干净区是否保住？

## 8. 反面 → 正面措辞

- "主体旁边再随便配两三样" → 先定 cast_size，再按档位列 0–5 类、每类定数量与摆位。
- "东西多显得丰富就铺开" → "multiple small groups packed tightly around the hero, rich but ordered, one clear focal point"。
- "单一主体怕空就再加点东西" → Solo 用承载/状态/光影/前景虚化托，不硬加配角。
- 配角贴主体正面/浮着 → "resting on the [surface] beside the hero with a soft contact shadow, partially tucked behind, never floating"。
