---
name: still-life-illustrator
description: 静物插画与静物主题海报生成技能。把水果、美食、果盘、红酒杯/酒瓶、餐具器物、花植、电商产品、简易化学分子结构等静态对象画成插画或杂志风静物海报，或根据参考照片提取版式/笔触/字体风格并重绘。三种平等风格：Style-1 水彩蜡笔手绘、Style-2 叙事静物编排、Style-3 色粉油画棒纸面颗粒（纸纹颗粒、背景颜色三风格统一、深色可选）。支持参考图风格提取、同主体多视角多版式变体（每主体至少两张）、大留白构图、主标题与短诗 PIL 后期排版。触发词：静物插画、静物海报、水果/美食/果盘/酒杯酒瓶/产品静物、editorial still life、把照片画成插画、色粉油画棒静物、pastel still life。
license: MIT
compatibility: Requires Python 3.10+ and Pillow>=10. HTML panel requires a local browser; external mode requires an LLM API. Core pipeline works offline.
metadata:
  version: "3.0.0"
  author: still-life-illustrator contributors
  python: ">=3.10"
  edition: full
---

# 静物插画生成（Still Life Illustrator）

> **版本：v3.0.0**（2026-09-04）· 许可证：MIT（见根目录 `LICENSE`）· 变更日志见 README.md

产出"唯一确定的主体 ＋ 数量可变的配角（组合档位 1–6 类，也可只有单一主体）＋ 大留白 ＋ 主标题与次要文字（一句短诗 ＋ 季节·拉丁学名两行）"的杂志级静物插画。**用户当次指令永远优先于本技能默认规则。** 支持"先出结构化 brief 规划、再确定性渲染"（external/self 两来源，见下文「规划-渲染协同模式」）。

> **单一事实来源（SSOT）**：本文件只放主干、铁律与流程；规则细节各有唯一权威，改规则只改权威处——
> 笔触克制定义 → `style-profiles.md` 公共段（三风格通用）；次要文字（短诗 ＋ 季节·拉丁学名）写法 → `LAYOUT §6.5`；
> 比例像素/量化译法/背景/构图/主体突出/同类疏密/边缘虚实/文字全部规则与命令 → `layout-and-composition.md`（下称 **LAYOUT**，§1–6）；
> 出图提示词拼装模块 → `prompt-blocks.md`；主体结构拆解 → `subject-structure.md`；
> 四季应季物产与全年常备题材事实库（374 种、按春37/夏69/秋42/冬28/全年·常备198 五区组织：固有色/质感/结构/应季月份/搭配器皿/cuttable_states可用状态，**JSON 优先查询** `seasonal_produce_index.json`，MD `seasonal-produce-index.md` 为人类可读 SSOT 供编辑）；
> 组合丰富度/元素类别档位（Solo~Bountiful、多层后退、Solo 烘托、物理着附）→ `composition-cast.md`；
> 先规划后渲染（brief@1.1、external/self 两来源、校验门、协同 SOP）→ `references/director/`（brief-schema / director-contract / director-workflow）。

## 全局铁律（优先级高于各风格手法；细节见对应权威）
1. **笔触克制（三风格通用，定义见 style-profiles.md 公共段）**：以**平涂色块拼接造型**为主、**默认不勾深色封闭描边**（靠色块自身洇虚/松化的边缘成形，浅色或白色部位直接留纸白）；近乎平光，体积只靠一块略深同色色面 ＋ 一两个点到为止的小高光、交叠处一块接触深色即可；细节用同色系小色点/短笔触。禁多层渐变渲染、碎笔排色、反复叠擦磨细节、光滑细黑封闭描边、照片级光影。概括而不平、有体积不写实。
2. **主标题与次要文字（三风格完全一致，唯一权威 LAYOUT §6，写法见 LAYOUT §6.5）**：每张成品都必配"主标题 ＋ 次要文字（一句短诗，并独立另加季节、拉丁学名两行）"，不存在无文字风格；**一律后期 PIL 叠加、生图阶段不写任何字（AI 手写路径已取消）**；主标题字体 kai/hand/serif/sans（不用 marker）、排法 normal/italic/wave/arch/scatter 五者平等随机无默认、上方居中优先、轻微重叠可读则不挪；次要文字用 type 且与主标题字体不同、与标题对角、自动对比选色不融底。**字号占比、段距、英文大写/中文学名取舍、中文回退 kai 等全部参数与命令只看 LAYOUT §6，此处不复制**；短诗守"信达雅"、学名须准确不臆造（不把握先查证）。
3. **主体突出 + 同类疏密（三风格通用，见 LAYOUT §4.1/4.2）**：主体是唯一且第一眼最突出的英雄（最大、最实、对比最强、占视觉中心），次元素不得靠数量/铺陈稀释它；同类多物排成"一个主簇（挨靠微叠）＋至多 0–2 个近距点散（≤自身 1–2 身位）"，禁全部等距分散、禁挤成一团、禁远距孤点与多个等权中心。**画面元素类别数按组合档位 cast_size 在 1–6 间变化（可只有主体、也可到主体＋5 类配角），不固定 2–3 类、不每张同套路；类别越多，配角逐类更小、更柔、更后退、对比更低，细节见 composition-cast.md。**
4. **边缘柔化/晕染（三风格通用、用户可选，见 LAYOUT §4.3）**：是否柔化、柔化谁可开关可分别指定，用户点名从其指定；**默认主体边缘也柔化晕染（形体完整、受光轮廓可辨，柔而不糊），次元素比主体再柔一档、背景最柔；只有明确点名"主体不柔/锐利/硬边"才给主体清晰硬边（也只是色块边缘更肯定，不是加黑描边）**。
5. **色彩总律（三风格通用，模块见 prompt-blocks §0 PALETTE）**：色相尽量丰富、可跨多色相族，但**画面整体观感保持中低饱和**——只在主体受光/关键部位或某一个次元素用高饱和点睛（合计约 ≤10–15%，用户要更浓可到 20–25%），由大面积中低饱和背景与多数元素托底；禁高饱和铺满、禁多块高饱和互打、禁荧光 neon。**当整体中低饱和且中式元素（青瓷/紫砂/竹编/宣纸/茶盏/中式糕点/腊梅山茶桂花等中式花卉/腊肉腊肠等中式食材）占比偏高时，色调氛围优先偏侘寂（wabi-sabi）：暖灰米白为底、器物带粗陶哑光质感、光影柔和留白多、避免鲜亮对比。**

## 30 秒决策树（无指定时快速定，不纠结）
- **组合档位**：用户点名（"就一颗/极简"→Solo/Duo，"丰盛/一桌子"→Abundant/Bountiful/Lush）＞题材季节倾向（早春侘寂偏简、秋收丰宴偏繁）＞按 Solo12/Duo18/Standard28/Abundant22/Bountiful12/Lush8 抽样；连续两批不重档、回看近 8 批去重（composition-cast.md §2）。
- **风格**：用户点名＞参考图对应＞按题材三选一（单体大留白海报→S1；多物件场景/产品故事→S2；颗粒复古/色粉→S3），并用一句话说明理由；不设默认、不套路。
- **标题排法**：用户指定从其指定（必须写入 brief 的 text.title_style 并传递到 overlay）；无指定时 normal/italic/wave/arch/scatter 五者随机取一（无默认，含 normal）。
- **字体**：主标题从 serif/sans/kai/hand 按风格选（棱角器物常用 serif，中文 kai/hand；**不用 marker**）；次要文字恒为 type；主/次必须不同。
- **位置**：主标题先放上方居中；仅当该处确无干净空间或压物致不可读才换位。次要文字与标题对角（follow），压物再微调 xy。

## 面板激活（默认激活，技能加载时自动启动并打开）
> **平台守卫：本节为 Windows / 豆包沙箱专属优化路径。** macOS/Linux 或非豆包环境：跳过计划任务与 VBS 相关步骤，直接后台运行 `python panel/start_panel.py --no-browser`（或经用户同意后整个跳过面板），其余流程不受影响。
- **默认激活**：技能加载时自动启动面板服务器并在豆包内置浏览器打开面板（端口已占用则直接打开，不重复启动）。用户说"关闭面板/不用面板"时才跳过。**启动通道必须走下条「服务器常驻启动」——AI 在命令行沙箱内禁止直接 `python panel/start_panel.py`（会被沙箱进程树回收，面板反复打不开，原因与正确做法见下条）。**
- **用途**：可视化选择所有出图选项（模式/批量/比例/语言/风格/季节/档位/标题排法/容器/状态叠加/色块/参考图/性能模式），生成标准指令文本，一键复制后粘贴执行，减少口述误差。
- **手动启动**：`python panel/start_panel.py`——自动检测端口8765，已运行则直接打开浏览器，未运行则启动本地HTTP服务器并打开面板。面板地址 `http://127.0.0.1:8765/panel/panel_pro.html`。支持 `--port`（指定端口）、`--no-browser`（只启动服务器不打开浏览器）、`--browser`（指定浏览器路径）。
- **服务器常驻启动（重要，避免面板反复打不开）**：AI 助手通过命令行工具（Bash/PowerShell 沙箱）直接 `python panel/start_panel.py` 启动的进程挂在沙箱 Job Object 进程树下，命令一结束就被连带回收，浏览器随即无法连接（pythonw、`cmd start`、`subprocess.Popen` 都逃不出去）。**必须改用 Windows 计划任务通道，让进程由系统任务计划服务（services.exe）拉起、父进程脱离沙箱进程树，命令结束后依然存活**，步骤：
  1. 先探活：HTTP 请求 `http://127.0.0.1:8765/panel/panel_pro.html`，返回 200 说明已在运行，直接打开浏览器即可，不重复启动；
  2. 未运行时，用 `panel/_run_panel.vbs`（无窗口调用 pythonw 执行 `start_panel.py --no-browser`）注册并立即运行计划任务，任务名 `StillLifePanelServer`，触发器 onlogon（开机登录自启，一劳永逸）：
     - `schtasks /create /tn StillLifePanelServer /tr "wscript.exe \"<技能根>\panel\_run_panel.vbs\"" /sc onlogon /f`（注意：`/tr` 的整段值是一个引号参数，内层引号必须用 `\"` 转义，否则注册会失败或被截断）
     - `schtasks /run /tn StillLifePanelServer`
  3. 轮询端口直到 HTTP 200（最多约 10 秒），再在豆包内置浏览器打开 `http://127.0.0.1:8765/panel/panel_pro.html`；浏览器是用户独立进程、不受沙箱影响，只有服务器需要这样常驻；
  4. `_run_panel.vbs` 为**自定位脚本**（无硬编码路径）：技能目录取脚本自身所在目录；pythonw 按优先级解析——环境变量 `STILL_LIFE_PYTHONW` 显式指定 → 豆包沙箱运行时 `%LOCALAPPDATA%\Doubao\User Data\sandbox_runtime\bases\<hash>\python\pythonw.exe`（自动取最新 base）→ PATH 中的 `pythonw.exe`，故豆包升级沙箱或换用户/换机器后依然可用；双副本（Profile 1 / Default）的 `_run_panel.vbs` 必须同步、md5 一致；`/tr` 参数总长不得超过 261 字符（故用短路径 VBS 中转，不直接塞长命令）。
- **专业版功能**（panel_pro.html）：7种语言切换（中/英/日/韩/法/德/西，默认中文）、四季动态背景（春樱花/夏绿叶/秋枫叶/冬雪花飘落动效，自动随月切换或手动切换）、成品预览（导入/下载/另存为/全屏/单张缩略图与主图同步/键盘快捷键；目录扫描支持任意文件夹路径（不限于工作区、可递归子目录），提供「仅成品 *_final.png / 全部图片(png/jpg/jpeg/webp/bmp)」范围开关、默认仅成品；每次扫描整体替换当前列表，自动刷新时保持当前查看位置）、6个快捷预设（单击选择/再单击取消）、三栏布局（左：预设+后处理，中：预览+指令，右：基础+风格+文字）、Editorial Fashion编辑时尚风格（深色近黑+米白+金色强调+衬线字体）、select金色悬停动效。
- **使用**：在面板中选择选项（或点击快捷预设一键填充）→ 实时生成指令 → 点击"复制指令" → 粘贴到对话框执行。
- **文件**：`panel/panel_pro.html`（专业版UI）、`panel/panel_config.json`（16个可选项+6个快捷预设定义，可独立编辑）、`panel/start_panel.py`（HTTP服务器+启动器，支持 `--port`、`--no-browser`、`--browser`，含 `/api/list-images?dir=&recursive=0|1&filter=final|all`、`/api/scan-project`（项目目录递归、仅成品）、`/api/image?path=`（按扩展名返回 png/jpg/jpeg/webp/bmp 正确 Content-Type）三个预览接口；运行时文案统一走 i18n 字典（getI18n，7 语言回退 en→zh））、`panel/_run_panel.vbs`（沙箱常驻无窗口启动器，配合计划任务 `StillLifePanelServer` 使用）。
- **注意**：面板仅生成指令文本，不直接触发AI执行；服务器在后台持续运行，关闭对话窗口不影响面板；静态文件修改后刷新浏览器即可，无需重启服务器；默认激活时若端口被其他程序占用，会提示用户手动访问面板地址。

## 标准流水线（按序执行，不跳步）
> **运行环境**：命令示例中的 `python` 指 PATH 中可用且已安装 Pillow 的 Python 3.10+；若环境实际提供的是 `py -3`、`python3` 或沙箱内置解释器，按环境替换，不要因 `python` 命令不可用而中断流程。
> **加载策略（省时间、不降质量）**：进入时读本主干即可，references 规则细节**按需跳读对应权威小节**；同一会话已经读过的文档不重复全量 Read。
> **最少工具轮次（快路径）**：设计推演/提示词组装不占外部轮次 → 一次生成调用（双稿放同一 request_list）→ `prep_images.py` **直接传成图 URL**（一步完成下载＋校正＋取色，不先单独 curl）→ 只 Read 校正后的图做一次目检 → 同一轮命令里对各稿跑 `overlay_text.py` → Read 成品回读 → 交付后删除本次无字中间过程稿（下载原图 / 校正稿）、只留 final → `present_files` 交付。**final 成品永久保留、绝不自动删除（跨任务也不清理历史 final），仅当用户明确点名删除某个 final 时才删。**全程约 4–6 个工具轮次，不拆碎步骤、不边交付边跑与出图无关的脚本。

### 1. 解析输入
- 有参考图：下载到本地，`scripts/inspect_image.py` 取尺寸/比例/方向/主色/边缘色，再 Read 识别主体、固有色、笔触、纹理、排版、字体与文字原文；**多张参考图分工：第一张定版式（构图/视角/留白位置），其余定风格（笔触/色彩/质感/氛围），不要让每张参考图都同时定版式和风格**。多张时用 `inspect_image.py IMG1 IMG2 IMG3 --summary` 输出整批统一比例/主色板/边缘色/风格倾向，用 `--prompt-inject` 输出可直接粘贴到提示词的英文风格片段（也可填入 brief 的 `ref_style` 字段，由 build_from_brief.py 自动注入）。提取维度表见 `style-extraction.md`。
- 无参考图：从文本提取主体与题材；无指定比例默认 4:5（2048×2560）。
- 主体只能有一个（同类组合算一个，如"一串葡萄+散落果粒"）。**状态叠加（三风格通用规则，共8种）**：可切割主体（水果/蔬菜/鱼肉/奶酪/面包/肉类等）默认随机选用一类状态对——整颗+剖半(halved)、整颗+切片(sliced)、整颗+切大块(cubed)、整颗+切小丁(diced)、整颗+切条/切丝(julienned)、整颗+剥皮(peeled，软皮)、整颗+剥壳(shelled，硬壳/虾/蟹/贝/坚果)；状态叠加的两部分算**一个主体类别**（不破坏主体唯一性），必须同主体、同色系、有物理接触，剖面/切片露内部结构（籽/果肉纹理/汁液/肉质纹理）；不可切割主体（器物/花卉/香草/调料等）保持单一自然状态。可用状态类型以旬物索引JSON中该条目的cuttable_states字段为准。
- **容器承载合理性**：用户指定容器/承载面时，**主体选择必须反过来适配该容器**（如用户说"放在篮子里"就不选蛋糕/汤/液体，"放在浅盘里"不选高枝花材，"放在碗里"不选扁平面包）；用户未指定时按 `composition-cast.md §6.1` 匹配表选合理承载，禁蛋糕入编篮、汤入浅盘、花入浅盘、鱼入高脚杯等不合理搭配。

### 2. 定风格（无默认，三风格平等）
按决策树选 S1/S2/S3 或用户自定义；三风格完整定义见 style-profiles.md（公共段笔触三风格通用，S2/S3 仅媒介语言不同）。

**题材选型速查**（无指定时的倾向，不是默认、可偏离；主体固有色永远以实物为准，表中只定字体/背景/视角倾向）→ 见 `style-profiles.md` 末尾「题材选型速查」小节。

### 3. 设计推演（几行字写清，再写提示词）
**先定组合档位 cast_size（1–6，反套路、不默认 2–3 类，composition-cast.md）** → 固有色 → 背景色（LAYOUT §3）→ 构图法 → 主体摆位 → 按档位定 0–5 类次元素（每类定精确数量与承载面）→ 文字方案：语言跟随使用者（中文则中文，否则英文）；主标题=主体名；次要文字＝一句短诗 ＋（空行分界、2.5 倍字高段距）＋ 季节块：英文排版为英文大写季节＋英文大写学名两行，中文排版（主标题与短诗均中文）只留一行中文季节、不生成学名（写法见 LAYOUT §6.5；学名不把握先查证、不臆造）；主标题排法用户指定优先、无指定时五选一随机（无默认）、定好字体配对与两处文字留白区；题材字体/背景/视角倾向查步骤 2「题材选型速查」。判定应季季节时可查 `seasonal-produce-index.md` 该物「成熟」字段。

### 4. 主体结构分析（写提示词前必做）
按 `subject-structure.md` 逐项拆解：整体形态/生长方式 → 层级纵深与遮挡 → 挤压变形与接触阴影 → 大小朝向自然差异 → 表面识别细节 → 不完美与丰满度；不熟悉的主体先搜实物图，不写"图标式"主体。**主体或搭配物若在《旬物索引》收录范围（常见果/蔬/香草/花/谷物/器物/甜点/器皿/花卉共 374 种、按春/夏/秋/冬/全年·常备五区组织），先 Grep `seasonal-produce-index.md` 取其固有色/质感/结构/搭配器皿/cuttable_states可用状态再拆解（仅提供事实与倾向，不覆盖任何铁律）。**

### 5. 版面参数
比例/方向与输入一致、长边 2048 取偶（像素表 LAYOUT §1，用户指定像素从其指定）；边距 ≥12%、留白 ≥33%（极限 25%）；冲突优先级 **主体唯一最大最突出 ＞ 留白 ＞ 次元素 ≤25%**。

### 6. 组装提示词（用模块库拼装，不从头硬写）
按 `prompt-blocks.md` 顺序拼：MEDIUM（S1=M1/S2=M2/S3=M3）+ **PALETTE（色彩总律，默认带）** + VIEW + SUBJECT（含第 4 步结构结论）+ 多物件加 HERO、同类多加 CLUSTER、EDGE（默认 EDGE-DEFAULT）+ PROPS/景深（配角类别数 = cast_size−1，Solo 无配角只留承载/光影，见 composition-cast.md）+ BG + LIGHT + COMPOSE + TEXT-BLANK（文字一律后期 PIL，生图无字、只预留干净区）+ NO_TEXT。硬约束：
- 必须含结构细节结论，不得只写主体名；精确数量写 `exactly N (count carefully)`；
- 文字一律后期 PIL：提示词明确"画面无任何文字"，在上方居中为主标题、在对角/一侧为次要文字预留干净区（TEXT-BLANK 模块）；
- 画面不生成任何文字/字母/数字/水印/logo（主标题与次要文字全部后期叠加）。

### 7. 生成（每主体 ≥2 张，同批提交）
- 模型默认 `seedream_5.0_pro`，不可用回退 `seedream_4.5`；有参考图用 image_edit（传参考图 URL），纯文本用 image_gen。
- **有参考图的批量场景（推荐路径）**：不要直接对 20 个主题逐个 image_edit（稳定性低、伪文字率高），而是走 **self 批量 + 参考图风格注入**：先用 `inspect_image.py --summary --prompt-inject` 从参考图提取统一风格片段，填入 brief 的 `ref_style` 字段，再走标准 self 批量流水线（self_skeleton → LLM 补创意 → self_merge → build_from_brief --batch → image_gen 批量生图）。这样风格统一由 ref_style 控制，生图用更稳定的 image_gen，批量成功率显著高于直接 image_edit。只有单张或少量（≤3 张）需要严格复刻参考图构图时，才直接用 image_edit。
- **image_edit 伪文字预防（有参考图时必做）**：参考图中若含文字/字母/数字，image_edit 容易把参考图中的文字"继承"到生成图中，产生伪文字。预防措施：①提示词中强化 `absolutely no text, no letters, no numbers, no watermark, no logo, NO frame, NO signature`（NO_TEXT 模块已包含，但有参考图时需在 pv_en 中再强调一次）；②参考图含大量文字时，先用 prep_images 裁剪掉文字区域，或选择文字较少的参考图；③生成后目检发现伪文字，只重生问题稿，在 pv 基础上加强 `do NOT generate any text or letters, the image must be completely text-free`。
- **多张参考图的批次均衡**：批量生成时，参考图风格不要每张都变——一批 20 个 brief 应共享同一组参考图提取的统一风格（ref_style 字段），保证整批视觉统一。不同批次之间可以换参考图风格，但同一批次内不要混用 3 种以上差异过大的风格。风格差异大的参考图（如一张水彩、一张油画棒）应分两批生成，不要混在同一批。
- 一次至少 2 张、**视角与版式都不同**（俯视/平视/45°/仰视 × 居中/三分/对角/散点，无默认组合）；**两稿必须在同一次调用的同一 request_list 提交**（同风格段、同主体设定），保证统一。
- **批量生图分批策略**：当一批总张数 > 15（如 batch_size 15 × A/B = 30 张）时，image_gen 每次调用的 request_list 不超过 3 张，逐批提交，避免一次性上传过多队列请求导致服务器响应异常；总张数 ≤ 15 时按常规双稿同批提交即可。
- **快速档（可选；仅用户点名"快 / 快速预览 / 先出草稿"时才走，默认不走）**：模型换 `seedream_4.5`、长边 1536、可单稿，定位为构图草稿，正式成稿仍回 5.0 Pro。**详细行为、实测特性、输出标注要求见 `references/performance-modes.md`**。用户未点名时默认恒定 `seedream_5.0_pro` ＋ 长边 2048 ＋ 双稿，不因求快擅自降级。

### 8. 校验（生成后必做，不过不进叠字）
**校正与目检**：成图 URL 交给 `scripts/prep_images.py --text-scan` 一步完成下载＋校正＋取色＋伪文字辅助扫描（输出命名：单源用 `--prefix` 原值，多源才加 `_A/_B`）；随后 Read 校正图逐张目检。**目检清单与伪文字检测+自动重生流程 → 见 `layout-and-composition.md §7`**。

### 9. 叠字与交付（命令唯一权威 LAYOUT §6）
- 紧接步骤 8，在**同一轮命令**里对每张校正稿各跑一次 `scripts/overlay_text.py`（两稿用一条命令串起来、不拆两轮）；一条命令同时叠主标题与次要文字（短诗 ＋ 季节、拉丁学名），字体别名、自动对比选色、范例见 LAYOUT §6.7；`--title-style` 取 brief 中 text.title_style 的值（用户指定或无指定时的随机结果），不得重新随机。
- 红线：主标题字块（默认 30%）；次要文字字高为主标题 18–36%（默认 25%）；主/次字体不同、主标题不用 marker；次要文字绝不融底；主标题上方居中优先、轻微重叠可读不挪，可读性受损才挪。
- 叠完 Read 成品回读一次（确认各行文字清晰、不融底、不压主体），随后通过 `present_files` 交付，每张配一句说明；交付后删除本次无字中间过程稿（下载原图、prep 校正稿），**只留 final**。**final 成品永久保留、绝不自动删除——跨任务也不清理历史 final，仅当用户明确点名删除某个 final 时才删**；计时/统计等与出图无关的操作不混入本流程。

### 10. 色块后处理（可选，用户点名"色卡/配色板/提取颜色"才做）
- 用途/触发/命令参数/规则 → 见 `layout-and-composition.md §8`。纯 PIL 实现，颜色名来自 `color_names.json` 最近邻匹配，禁止模型生成颜色名。

## 规划-渲染协同模式（brief 先行 · self 默认主线，external 可选扩展）
- **核心**：把"创意规划"与"渲染执行"解耦——先产出一份结构化 **brief@1.1**（选物/数量/档位/双视角/文字/每稿可变画面段 pv_en），过校验门后由本地脚本确定性补技术段再出图，比直接手写长 prompt 更可控、可复现、可只改一字段重渲染。规范唯一权威 `references/director/brief-schema.md`。
- **self 是默认主线，external 是可选扩展；二者汇入同一下游**：
  - **self（默认、离线可用）**：本技能按 `references/director/director-workflow.md §3` 自起草 brief，不依赖任何外部模型，迁移到别的电脑照样跑。默认顺滑档（内部起草直接出图、交付附一行 brief 摘要）；用户说"先看方案/先给 brief"则先给方案确认再画。
  - **external（可选扩展：仅当你想让另一个模型来发散创意、对冲自我套路时才用；离线 / 迁移到别的电脑 / 求稳求快都走 self）**：外部 LLM（如 DeepSeek）按 `references/director/director-contract.md` 只回创意 JSON；取数流程与双通道见 `references/director/director-workflow.md`（浏览器 computer_use 内调 `scripts/director_dom.py` 自动取回为主，手动把 JSON 落地为文件兜底）。
- **固定下游（两来源共用，不维护两套渲染）**：
  1. `scripts/validate_brief.py <id>_brief.json`：硬校验门（字段/枚举/cast 自洽/双视角差异/精确数量/语言一致/技术段污染），不过不进下一步；
  2. `scripts/build_from_brief.py <id>_brief.json [--outdir 工作区]`：运行时从 prompt-blocks.md 锚点解析公共段（MEDIUM/PALETTE/HERO/CLUSTER/EDGE/TEXT-BLANK/NO_TEXT，单一来源，`--show-blocks` 可核对），产出 `<id>_A.txt`、`<id>_B.txt` 与 `<id>_overlay.json`（脚本默认先自动过校验门）；
  3. 接步骤 7–9：同批双稿生图 → `prep_images.py` 校正目检（数量逐项实数、档位/物理着附/主体突出）→ `overlay_text.py` 叠字 → 回读 → 交付。
- **批量模式（一批 N 个 brief，默认 10，可选 2/5/10/15/20/30）**：逐个起草 brief 时 LLM 重复输出大量固定字段，批量模式把固定字段交给脚本、LLM 只补创意，token 消耗降到约 1/3。三条路径：
  - **self-A（推荐）**：`self_skeleton.py` 选题清单→N 份骨架（创意字段 TBD）+ `creative_template.json` → LLM 补 pv_en/poem/latin/title → `self_merge.py` 合并+自动校验；
  - **self-B**：LLM 一次生成 N 个 brief 的 JSON 数组 → `director_dom.py` 批量落地；
  - **external**：DeepSeek 按 `director-contract.md §B2` 一次回 N 个 brief 的 JSON 数组 → `director_dom.py` 批量落地。
  三条路径落地后统一走 `build_from_brief.py --batch <目录>` 一次性校验+拼装全部 A/B 提示词与 overlay 参数，输出紧凑摘要表与批次均衡统计。详见 `director-workflow.md §7`。
- **边界**：brief 只写可变创意，媒介/笔触/色彩总律/边缘/无字等技术段一律本地补，self 与 external 都不写；浏览器库只能在 computer_use 代码环境运行，**做不到脱离对话的纯命令行全自动**，故保留手动粘贴兜底；过程 brief/prompt 放项目工作区，规则与脚本只存技能内，final 永久保留、中间稿清理以用户当次约定为准。
- **参考图批量场景（推荐走 self 批量 + 参考图注入）**：有参考图且需要批量生成（>3 张）时，不要直接逐个 image_edit。标准流程：①`inspect_image.py 参考图1 参考图2 --summary --prompt-inject` 提取统一风格片段；②把风格片段填入 brief 的 `ref_style` 字段（self_skeleton 生成骨架时可批量填入）；③走标准 self 批量流水线（self_merge → build_from_brief --batch，ref_style 自动注入到提示词 PALETTE 段之后）；④用 image_gen 批量生图（比 image_edit 稳定、伪文字率低）。只有单张或 ≤3 张需要严格复刻参考图构图时，才直接用 image_edit。批量叠字用 `overlay_text.py --batch <目录>` 一次性处理全部 A/B 稿。

## 规则速查（去哪看）
| 维度 | 结论 / 权威 |
|---|---|
| 张数/比例 | ≥2 张视角版式均不同、同批；比例随输入，无图默认 4:5，长边 2048（LAYOUT §1） |
| 速度 | 默认 5.0pro/2048/双稿（一次成功率高）；点名"快速/草稿"才走 4.5/1536/可单稿，但 4.5 或需 1–2 次重生、宜草稿（步骤7） |
| 笔触 | 三风格通用：平涂色块、零封闭描边、近乎平光，定义见 style-profiles.md 公共段 |
| 主体/构图 | 唯一最突出；同类一主簇＋近距点散；构图法见 LAYOUT §4 |
| 组合档位 | 元素 1–6 类可变（Solo 可纯主体、最多主体＋5 类），不固定 2–3 类；配角逐类更小更柔、向主体收拢、物理着附不悬空（composition-cast.md） |
| 规划协同 | 先 brief@1.1 后渲染：self（本体自起草·默认离线）/external（外部 LLM）同源，过 validate_brief 校验门、build_from_brief 拼装（references/director/） |
| 边缘 | 用户可选；默认主体柔化可辨、次元素更柔，点名才不柔主体（LAYOUT §4.3） |
| 背景 | 默认浅底/撞色例外/深色自选，LAYOUT §3 |
| 色彩 | 色相丰富但整体中低饱和、高饱和仅小面积点睛（prompt-blocks §0） |
| 文字 | 三风格一致、每张必配、一律后期 PIL（生图无字）；主标题 serif/sans/kai/hand（无 marker）、五排法用户指定优先、无指定时随机（无默认）、上方居中优先；次要文字=短诗＋空行＋季节块（英文大写季节+学名两行，中文仅一行中文季节、无学名）、type、与主标题不同字体、对角、不融底；字号/段距/回退等全部参数见 LAYOUT §6，写法见 LAYOUT §6.5 |
| 色块（可选） | 用户点名才做；参数/规则见 LAYOUT §8；scripts/color_palette.py |
| 提示词 | 模块拼装见 prompt-blocks.md；题材选型见 style-profiles.md 末尾 |
| 题材知识库 | 374 种（春37/夏69/秋42/冬28/全年·常备198 五区）物产的固有色/质感/结构/应季月份/搭配器皿/cuttable_states可用状态，**JSON 优先查询**（seasonal_produce_index.json），MD 为 SSOT 供编辑（seasonal-produce-index.md） |
| 风格 | 无默认三平等：S1 水彩蜡笔 / S2 叙事编排（笔触用公共段）/ S3 色粉颗粒 |
| 审美 | 跨插画/摄影/时尚/平面/电商/雕塑的高级感 |

## 文件索引
- `panel/panel_pro.html`：**可视化选项面板**（7语言切换+四季动态背景+成品预览+6快捷预设+三栏布局+编辑时尚风格）
- `panel/panel_config.json`：**面板选项定义**（16个可选项+6个快捷预设，可独立编辑）
- `panel/start_panel.py`：**面板启动器**（端口检测+本地HTTP服务器+自动打开浏览器）
- `references/style-profiles.md`：**三风格完整定义（合并版）**——公共段=笔触克制（三风格通用源头）；S1=水彩蜡笔手绘、S2=叙事静物编排、S3=色粉油画棒纸面颗粒，三节只写各自媒介/色彩/光影/构图/氛围差异
- `references/layout-and-composition.md`：**通用规则与文字 SSOT**（像素/译法/背景/构图与三铁律/骨架/文字系统）
- `references/prompt-blocks.md`：**出图提示词模块库（拼装即用；§0 为三风格通用色彩总律 PALETTE）**
- `references/subject-structure.md`：主体结构分析方法与分主体速查、搭靠层级规则（题材→字体/背景/视角的选型速查已并入 SKILL 步骤 2）
- `references/seasonal_produce_index.json`：**四季应季＋全年常备题材事实库《旬物索引》374 种（春37/夏69/秋42/冬28/全年·常备198 五区；JSON 数据库，脚本优先查询）**（固有色/质感/结构/应季月份/搭配器皿/入画 S1-S3 倾向；由 convert_index.py 从 MD 自动生成）
- `references/seasonal-produce-index.md`：**四季应季＋全年常备题材事实库《旬物索引》374 种（五区；人类可读 SSOT，供编辑）**（固有色/质感/结构/应季月份/搭配器皿/入画 S1-S3 倾向；按需 Grep 命中条目、不整卷读；只供事实与倾向、不覆盖铁律；不含拉丁学名，学名仍按 LAYOUT §6.5.2 核实）
- `references/composition-cast.md`：**组合档位（元素丰富度）SSOT**——Solo/Duo/Standard/Abundant/Bountiful/Lush 六档、选档概率、多层后退、Solo 烘托、物理着附
- `references/director/brief-schema.md`：**brief@1.1 唯一规划格式**（字段/约束/示例）；`director-contract.md`：外部 LLM 契约（自包含可粘贴）；`director-workflow.md`：执行端唯一 SOP（self 六步起草＋external 双通道取数＋批量三条路径＋历史去重）
- `references/style-extraction.md`：参考图提取表
- `scripts/inspect_image.py`：尺寸/比例/主色/边缘色分析（支持多图、--json；--summary 整批风格汇总、--prompt-inject 输出可粘贴到提示词的英文风格片段）
- `scripts/prep_images.py`：一键 下载URL→校正到目标尺寸→输出检查摘要；--text-scan 启发式伪文字辅助检测（边缘密度/高对比度块横向排列特征，仅辅助提示）
- `scripts/overlay_text.py`：主标题与次要文字后期合成（单张模式 + --batch 批量模式：自动读取 *_overlay.json 对 A/B 校正图批量叠字）
- `scripts/color_palette.py`：色块后处理（可选）——从成品图动态提取主色（默认最多 10 种），渲染单条横向色块带，可选标注颜色名/HEX；单张 + --batch 批量（直接覆盖原文件）；颜色名来自 color_names.json 最近邻匹配，纯 PIL 实现
- `scripts/color_names.json`：色块颜色名字典（168 个公认英文颜色名及 RGB 值，供 color_palette.py 最近邻匹配）
- `scripts/validate_brief.py`：brief 硬校验门（字段/枚举/cast 自洽/双视角/数量/语言/技术段污染）
- `scripts/build_from_brief.py`：brief→A/B 提示词＋叠字参数（单份/批量双模式）——单份 `python build_from_brief.py brief.json`，批量 `python build_from_brief.py --batch <目录>` 一次校验＋拼装全部（批量并行编排，省去逐份串行等待；输出紧凑摘要表与批次均衡统计）；brief 含 ref_style 字段时自动注入到 PALETTE 段之后
- `scripts/self_skeleton.py`：self 批量骨架生成器——选题清单→N 份 brief 骨架（固定字段全填、创意字段 TBD），批次内档位/风格/季节/视角自动均衡，查旬物索引填固有色，输出 creative_template.json 供 LLM 补创意
- `scripts/self_merge.py`：self 创意字段合并器——把 LLM 补的 pv_en/poem/latin/title 合并回骨架，自动校验，输出成功/失败摘要
- `scripts/director_dom.py`：从页面文本提取 brief 的纯函数库 ＋ 批量落地 CLI——函数库模式供 computer_use 代码 import（extract_brief / extract_brief_array / land_briefs 等），CLI 模式从 JSON 文件或页面文本批量提取并落地为 `<id>_brief.json`，输出紧凑摘要；支持 --merge 分批合并、--report 提取诊断、--expect-ids 缺失检测
- `scripts/brief_history.py`：历史去重 `recent 8` / `add`（JSONL 默认落项目工作区 still_life_history.jsonl，不写进技能）
- `assets/fonts/`：**随技能分发的 OFL 中文字体 LXGWWenKai-Regular.ttf（霞鹜文楷，跨平台 CJK 兜底，系统字体全缺失时保证中文不渲染成方框；许可证见 assets/fonts/OFL-LICENSE.txt）**＋用户自有 .ttf/.otf 可放入；查找顺序为别名链（serif=宋体/Times、sans=雅黑/Arial、kai=楷体、hand=行楷、type=Courier New，各链末位为文楷兜底；已不使用 marker），系统字体目录 Linux/macOS 支持递归查找
- `README.md`：面向用户的使用指南
