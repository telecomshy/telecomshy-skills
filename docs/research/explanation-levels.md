# 由浅入深的讲解：理论、格式与「避免过度解释」调研

> 范围：为 `answer-style` 技能设计「渐进、分层讲解（由浅入深）」提供理论依据与设计约束。重点回答：**一节课/一段讲解应该从哪开始、如何逐层展开，以及哪些原则支持「砍长度、别堆料」。**
> 调研日期（access date）：2026-09-14。
> 方法：**以一手来源为准**——优先原始论文、出版社 DOI 页、作者/大学页面。Wikipedia 在调研网络环境下不可达，故改用 DOI 解析（`https://doi.org/...` 返回规范题录）、`instructionaldesign.org`、作者主页与大学学报页等替代；每条主张均给出可核验 URL。**流行方法（费曼技巧、ELI5、Wired 5 Levels）明确标注为「非正式理论」。**
> 结论先行见 §0；理论逐条见 §1；**理论 → 设计杠杆对照表**见 §2；设计启示见 §3。

---

## 0. 结论速览（TL;DR）

1. **形状**：理想讲解 = **先给一个「认知缩影 / epitome」**（用小而完整的核心案例点出本质），再**逐层细化（progressive elaboration）、逐层降维到机制**；每层只加一层复杂度，上一层是下一层的承重。（Reigeluth 细化理论；Ausubel 先行组织者）
2. **方向**：从**具体 → 抽象**（concreteness fading），但必须**显式地把具体属性「褪掉」**；只停在具体会上瘾且伤迁移。（Goldstone & Son；Fyfe et al.）
3. **砍长度是被理论支持的，不是偷懒**：**coherence**（删无关素材）、**redundancy**（别重复同义信息）、**segmenting**（分段、学习者控速）、**expertise reversal**（对高手，给新手的脚手架反而有害）——四者共同论证「少即是多」。（Mayer；Sweller/Kalyuga）
4. **层级不是「讲多少」，而是「连得多深」**：SOLO 的 relational / extended abstract 关心的是**结构连接**而非字数；堆事实（multistructural）常比 relational 更长却没更深。（Biggs & Collis）
5. **不要一次讲全，而是「邀请下钻」**：把更深的层做成**可选的下一层**（progressive disclosure），而不是前置铺满——这同时满足 segmenting、learner control、ZPD 的「脚手架渐撤」。（Mayer；Reigeluth；Wood/Bruner/Ross）
6. **两个张力必须承认**：(a) Ausubel 主张「一般→具体」，Reigeluth/具体渐变主张「具体/简单→复杂」——解法是 epitome 同时做到「简单且完整」；(b) Bjork 的「合意困难 / 流畅性错觉」警告：让讲解**顺滑到只产生「学会了」的错觉**是危险的，所以短要短在删冗余，而不是短在替用户把思考全做完。

---

## 1. 理论逐条

### 1.1 Reigeluth 细化理论（Elaboration Theory）

- **核心**：教学应按**复杂度递增**组织；教程序性任务时先给**最简单的完整版本**，后续再给更多版本。每节课都应提示此前学过的全部版本（summary / synthesis）。关键点是让学习者先建立**有意义的上下文**，后续观念才能挂靠（assimilate）。[^elab]
- **epitome（缩影 / 概要实例）**：第一课不是「摘要」也不是「抽象」，而是**用少量基本/代表性观念在「应用层」呈现一个完整缩影**，只选一种内容类型（概念 / 程序 / 原理）。例如经济学先讲**供需定律**这一个原理，再把它细化为弹性、垄断、限价等。[^elab]
- **七个策略成分**：细化序列（elaborative sequence）、学习前置序列、summary、synthesis、类比、认知策略、**学习者控制（learner control）**。其中细化序列最关键。[^elab]
- **"缩放"直觉**：先看**整头大象的最简形态**，再一层层 zoom-in。理论自称是 Ausubel（先行组织者）与 Bruner（螺旋课程）的延伸。[^elab]

### 1.2 具体→抽象渐变（Concreteness Fading）

- **主张**：光争论「具体好还是抽象好」没意义；应**先具体，再显式、逐步地「褪」到抽象**，兼取两者之长。四项收益：(1) 用已懂的具体物帮助解释不透明符号；(2) 提供具身经验为抽象奠基；(3) 建立可回忆的心像，符号失去意义时兜底；(4) 引导学习者**剥掉无关的具体属性**、提炼可泛化的结构。[^fade]
- **顺序（方向）很重要**：`具体 → 抽象` 优于反向，且优于「只具体」或「只抽象」。Fyfe 等系统综述即推荐这一序列。[^fade]（相关的 McNeil & Fyfe 2012 在数学情境中支持该序列促进迁移。）[^mcfyfe]
- **容易被忽略的边界**：Goldstone & Son 发现**理想化（idealized，接近抽象）的模拟比纯具体模拟更能迁移**——说明「具体」必须服务于抽象，而不是终点。[^goldson]

### 1.3 认知负荷理论（Cognitive Load Theory, Sweller）

- **工作记忆有限、图式（schema）是知识单元**：学习 = 长时记忆图式的改变；教学应设计为**降低工作记忆负荷**以促成图式获得。[^clt]
- **三类负荷**（Sweller 等 1998 提出并区分）：**intrinsic**（材料固有 + 取决于学习者专长）、**extraneous**（由不良设计引入、纯浪费）、**germane**（用于图式建构的有效努力）。[^sweller98]
- **直接支持「砍」的四条行为建议**（instructionaldesign 总结自 Sweller）：换掉高负荷的 means-ends 解题、改用 **worked examples / goal-free problems**；**物理整合**多来源信息以减少搜索；**减少冗余（reduce redundancy）**；在信息非冗余时用双通道。[^clt]
- **冗余效应（redundancy effect）**：同一信息以多种冗余形式呈现会**增加**负荷、降低学习（专家尤甚）。[^clt][^mayer03]
- **范例效应 + 淡出（worked-example effect & fading）**：初学者看**worked examples** 比做等价题目学得更好；随着专长增长，应从「完整范例 → 补全型（completion）→ 独立解题」**逐步淡出**。[^swcooper][^renkl]
- **专长逆转效应（expertise reversal effect）**：**对新手有效的教学支持，会对有经验者产生反效果**；因此不存在对所有人都最优的讲解——这正是「分层讲解」的理论依据。[^kalyuga]

### 1.4 Mayer 多媒体学习认知理论（特定四原则）

- **机制**：学习 = 选择、组织、整合；对应三类认知加工。[^mayer03][^mayer14]
- **coherence（一致性）**：**排除无关素材**（无关词、图、声）比纳入更好。[^mayer03][^mayer14]
- **signaling（信号/线索）**：加入**强调核心材料组织结构的线索**（标题、高亮、指示词）更好。[^mayer03][^mayer14]
- **segmenting（分段）**：把内容切成**学习者可控制节奏的小段**，优于一次性连续呈现。[^mayer03][^mayer14]
- **pre-training（预训练）**：先让学习者知道**关键概念的名称与特征（前置项）**再上主课，更好——≈「先教承重前置术语」。[^mayer03][^mayer14]
- （同一文献中的 redundancy 原则：**图 + 旁白**优于「图 + 旁白 + 同文屏幕文字」。）[^mayer03]

### 1.5 SOLO 分类学（Biggs & Collis）

- **五个层级**（描述**回应质量**的结构，而非学习者或题目难度）：**prestructural**（抓不到点）→ **unistructural**（一个相关点）→ **multistructural**（多个点但未连接）→ **relational**（点连成解释）→ **extended abstract**（泛化到情境之外、可迁移）。[^solo]
- **关键洞察**：**长度不揭示层级**。multistructural 答案（堆事实）常比 relational（连成因果链）更长，却没更深；判断深度看的是「because / so / 因此 / 意味着」这类**连接词**，不是信息量。[^solo]
- 对讲解的直接含义：**要深，就加连接（因果），不是加材料**；relational 只需在 extended abstract 时才跨情境泛化。[^solo]

### 1.6 Bloom 修订版分类学（Anderson & Krathwohl）

- 2001 年修订把**名词改动词**，六个认知层级：**remember → understand → apply → analyze → evaluate → create**（create 被移到最高），并新增**知识维度**（事实 / 概念 / 程序 / 元认知）。[^krathwohl][^andkrath]
- 对讲解的含义：可用于**标注目标层级**（是想让人「记得」还是「会判断/创造」）；同时作者自己警告**层级不是严格阶梯**，「create 不一定比 analyze 难」，应作粗略指南。[^andkrath]

### 1.7 Ausubel 同化理论与先行组织者（Subsumption & Advance Organizers）

- **学习首先取决于学习者已知什么**（Ausubel 名言，见下）；有意义的接受学习 = 新材料与已有认知结构做**实质性的、非逐字的**联系（subsumption）。[^ausubel]
- **先行组织者（advance organizer）**：在正式材料**之前**给出，**抽象/概括/包摄程度更高**，作用是充当「新旧知识之间的包摄桥梁」——**区别于同层级的 overview/summary**。[^ausubel]
- **渐进分化（progressive differentiation）**：**先呈现最一般的观念，再逐步分化细节**；材料应通过比较与交叉引用把新旧知识整合起来。[^ausubel]

### 1.8 Vygotsky 最近发展区（ZPD）与教学脚手架

- **ZPD** = 「独立解决问题的实际水平」与「在成人指导或与更有能力同伴合作下可能达到的水平」之间的**距离**（Vygotsky 1978, p.86）；教学应落在这一**略超独立能力**的区间。[^zpd]
- **脚手架（scaffolding）** 由 **Wood, Bruner & Ross (1976)** 提出：通过**控制那些一开始超出学习者能力的任务要素**，让其专注于力所能及的部分；支持应**随能力增长而渐撤（contingent + fading）**。Vygotsky 本人未用「scaffolding」一词，是后来被连到 ZPD 的。[^zpd][^wbr]
- 对讲解的含义：**先给足脚手架，再淡出**；支持要**实时匹配**当前水平（contingent），而不是固定剂量。

### 1.9 费曼技巧（Feynman Technique）——流行方法，非正式理论

- 四步：(1) 选定概念、写下已知；(2) **讲给一个 12 岁孩子听**（用最简单的话）；(3) 复盘、回源补漏、重写；(4) 测试并归档。[^feynman]
- 价值内核：**复杂度与术语常常掩盖「没懂」**；能讲简单才算真懂。它是**学习方法（popular method）**，不是经实验检验的教学理论。[^feynman]

### 1.10 分级讲解格式（Leveled Explanation Formats）

- **WIRED「5 Levels」**：一位专家向**五类递进专业度的人**（儿童 → 青少年 → 大学生 → 研究生 → 领域专家）讲同一主题，逐级换词汇与抽象度。属**媒体呈现格式**，非理论。[^wired]
- **ELI5 / "explain like I'm 5"**：源自 Reddit r/explainlikeimfive；默认受众 = 5 岁，要求用最朴素语言。[^reddit]
- **开源技能 `DreambigOu/ELI5` 的结构**（本仓库同生态参考）：
  - **Step 1 识别受众**：按 **年龄**（5 / 10 / 15 / 20–30 / 40+）、**学历**（5th grade / middle / high / college / grad）、**职位**（manager / engineer / designer / director / colleague / PM）、**关系**（配偶 / 父母 / 孩子 / 朋友）分成不同档。[^eli5skill]
  - **Step 3 结构**：`用一句话说 what → 一个类比 → 按受众层级加细节 → 以 so what 收尾`；**默认 Age 5**。[^eli5skill]
  - **语言校准**：简单受众「零术语、一句一个意思、具体优先」；技术受众「用术语、讲 trade-off / 边界、要**简洁**」；商业受众「先讲影响、量化、跳过实现」。[^eli5skill]
  - **明确提醒**：「长度要匹配受众」「极复杂且受众很外行时，**可 ruthless 简化**，80% 准确胜过 100% 准确但讲丢」。[^eli5skill]
- 与本技能 v1/v2 教训吻合：ELI5 明确把**长度**设为受众函数，而不是越全越好。

### 1.11 类比与结构映射（Gentner）

- **结构映射（structure-mapping）**：类比 = 把**关系结构**（尤其高阶关系）从 base 映射到 target，**而非表面属性**；判断好坏看**系统性（systematicity）**。[^gentner83]
- **表面相似 vs 结构相似**：人们常被**表面相似**触发类比，却做错映射，从而产生误解；**类比更应看关系结构是否对齐**，而非「长得像不像」。[^gentner97]
- 讲解含义：类比是脚手架，**只保留能对齐机制的那一个**，并点明「哪不像」（边界），然后**退回机制**；多个或花哨的类比容易诱发表面相似、掩盖结构。

### 1.12 合意困难（Desirable Difficulties）vs 流畅性错觉（Bjork）

- **合意困难**：某些训练条件在训练期间**表现更差**，但带来更好的**长期保持与迁移**（如间隔、交错、测试、生成、变式练习）。[^bjork]
- **流畅性错觉 / 元认知误判**：人们用**主观流畅度**当作「学会没学会」的线索，而该线索常被误导——massed/流畅的学**感觉**更有效，实际保持更差；人们也低估遗忘。[^bjork]
- 讲解含义：**「好懂」是必要但危险的信号**。(a) 不要把「顺滑」当成理解了；(b) 但也不该为难度而难度——只有**germane**（指向图式建构）的难才"合意"，冗余/无关的难是 extraneous。[^bjork][^sweller98]

### 1.13 知识诅咒 / 专家盲区（Curse of Knowledge）

- **定义**：知道得越多，越难准确理解信息较少者的视角；专家会**默认「我觉得显然」的东西对新手也显然**，于是**跳过承重的那一步**。[^cok]
- **经典证据（tapping study，Newton 1990）**：敲击者预估听者能猜出旋律的比例约 **50%**，实际仅 **2.5%**。[^cok]
- 术语由 **Camerer, Loewenstein & Weber (1989)** 提出；机制包括**抑制控制失败**与**流畅性错误归因**；又称 **curse of expertise**。[^cok][^camerer]
- 讲解含义：必须**显式假设「他可能不知道」**并核对前置；反过来说，也不能对新手过度假设「一定不知道」而对高手啰嗦（见 expertise reversal）。

---

## 2. 理论 → 设计杠杆对照表

| 理论 | 给本技能的具体杠杆 |
| --- | --- |
| Reigeluth 细化理论 | **以 epitome 开篇**（小而完整的核心实例），再**逐层 zoom-in**；每层回顾上一层；保留 **learner control**。 |
| 具体渐变 | 第 1 层用**具体实例**；之后**显式褪去**具体属性，落到通用机制。 |
| CLT：冗余效应 | **删重复信息**；同一内容不要「正文 + 复述 + 总结」三连。 |
| CLT：范例 + 淡出 | 先用**跟着走的 worked example**，再淡出为自检 / 补全，而不是一开始就抛抽象定义。 |
| CLT：专长逆转 | **分层**而非一套讲到底；给新手的东西不要塞进给高手的答案。 |
| CLT：intrinsic/extraneous/germane | 判断「这段难有没有用」：只加**指向图式**的难，删无关的难。 |
| Mayer：coherence | **默认删掉**与主线无关的趣闻、旁枝、seductive details。 |
| Mayer：signaling | 用**一句话主线 / 小标题 / 连接词**标出结构，让读者抓得住骨架。 |
| Mayer：segmenting | 把讲解**切成层**，一层一个认知动作，允许读者停。 |
| Mayer：pre-training | **只补真正承重的前置**（名称 + 特征），不补「以防万一」。 |
| SOLO | 深度 = **连接（因果）**，不是事实数；relational 才是「讲会」的下限，extended abstract 才跨情境。 |
| Bloom 修订版 | 用动词**标注目标层级**（remember…create），并据此决定要不要展开。 |
| Ausubel | **先锚定到已知**；必要时先给一句**高概括的先行组织者**做桥；再渐进分化。 |
| Vygotsky / 脚手架 | 支持**按当前水平给、并渐撤**；一次只给刚好够越过的帮助。 |
| 费曼技巧 | 用「**讲给 12 岁**」当**自检**：讲不清处就是断点。（非正式理论） |
| ELI5 / 5 Levels | **受众档位化、默认最低档、长度随受众**；分层标签化。 |
| Gentner 结构映射 | **至多一个类比**，只对关系结构，必须给边界并**退回机制**。 |
| Bjork 合意困难 / 流畅性 | 不把「顺滑」当学会；结尾留一个**生成性动作**（自检 / 迁移题），别替读者做完。 |
| 知识诅咒 | 写作前**显式诊断已知/卡点**，假设「可能不知道」；避免「显然/当然」。 |

---

## 3. 设计启示（Design implications）

### 3.1 理论支持的「由浅入深」形状（层级顺序）

综合 Reigeluth（epitome → 细化）、具体渐变（具体 → 抽象）、Mayer（segmenting / pre-training）、SOLO（结构层级）与 Feynman（先讲简单）：

- **L0 一句话本质（crux）**：用日常话点出 idea 的本质 + 那句「解锁整个概念的关键句」。对应 SOLO **unistructural**；对应 epitome 的「骨架」。
- **L1 具体最小实例 + 承重前置**：给一个**能亲手跑的最小具体案例**，并只补**承重的前置**（不懂它就全塌的那个）。对应具体渐变的「起于具体」、Mayer pre-training、Ausubel 的锚定。[^fade][^mayer03]
- **L2 因果机制**：按「发生了什么 → 为什么下一步必然发生 → 结果」推进，**逐层褪去具体、落到抽象机制**。对应 SOLO **relational**、concreteness fading 的 fade、Reigeluth 的 progressive elaboration。[^fade][^solo]
- **L3 边界 / 权衡 / 形式化（可选）**：只在 L2 成立后给；对应 SOLO **extended abstract**、expert 档、Bloom 的 analyze/evaluate/create。[^solo][^krathwohl]

> 判定「深」的标准是**连接**，不是字数：L2 相对 L1 新增的是**因果链**，L3 新增的是**边界/泛化**；若某段两层都只增加事实，应删或降级到附注（SOLO：multistructural ≠ deeper）。[^solo]

### 3.2 哪些原则具体支持「砍长度」

1. **coherence**：删无关素材、seductive details。[^mayer03]
2. **redundancy**：同义信息不重复（正文不再复述，总结不重新讲一遍）。[^clt][^mayer03]
3. **segmenting**：分段、可停，不求一段讲完。[^mayer03]
4. **expertise reversal**：对已具备该层的读者，**新手脚手架就是负担**，应删。[^kalyuga]
5. **Ausubel**：**已知的不讲**——先定位已知，再只讲增量。[^ausubel]
6. **SOLO**：堆事实（multistructural）不增深度；**没增加连接/边界的长度一律可删**。[^solo]
7. **知识诅咒**：逼自己找出「我以为他懂」的那一步，其余套话自然可删。[^cok]

**可操作的「完成判据」（与现有 `answer-style` 的 v1/v2 教训一致）**：*删掉某段若不破坏因果链、也没修复任何理解断点，就删*——深度来自修复断点，不来自篇幅。

### 3.3 层级如何选择 / 标示，如何「邀请下钻」而非前置铺满

- **先诊断再定档**：写作前显式问「已知 / 卡点 / 错误直觉 / 承重前置」。理论依据：ZPD 的 contingent 支持、Ausubel 的「已知决定学习」、知识诅咒的 debiasing「先问对方知道什么、拿不准假设不知道」。[^zpd][^ausubel][^cok]
- **默认最低档，但别轻慢**：ELI5 默认 Age 5；同时技术受众若被当外行讲会被冒犯（expertise reversal）。[^eli5skill][^kalyuga]
- **显式标示层级 + 主线**：用 signaling 的做法——一行层标签（如「先说骨架 / 再讲机制 / 需要时给边界」）与连接词，把结构暴露出来。[^mayer03]
- **用 progressive disclosure 邀请下钻**：先只给当前档，末尾**明确给出「要不要再深一层」的口子**（下一层是 opt-in），而不是预先把所有层堆出来。依据：segmenting（可停）、Reigeluth learner control、脚手架渐撤。[^mayer03][^elab][^zpd]
- **按角色意图换维度**：管理者要影响/决策，工程师要机制/trade-off——同一概念换「关心什么」而不是换准确度。[^eli5skill]
- **类比用后即焚**：至多一个、只映射关系结构、给边界、随即退回机制。[^gentner83][^gentner97]

### 3.4 理论分歧，以及「短」与「深」的冲突点

- **Ausubel「一般→具体」vs Reigeluth / 具体渐变「具体或简单→复杂」**。Ausubel 要**先给高概括的先行组织者**；Reigeluth 要**先给具体 epitome**。**调和**：epitome 既不抽象也不等于摘要——它是**「简单且完整」的一个可操作实例**；对高度抽象的领域，可**先用一句高概括框架做桥（先行组织者），紧接着落到一个可把握的实例**。[^ausubel][^elab][^fade]
- **具体 vs 抽象谁更利于迁移**：Goldstone & Son 发现**理想化（偏抽象）表征迁移更好**；Kaminski 等（2008）甚至报告抽象例子有优势；但 Fyfe 等综述的结论是**「具体→抽象」序列优于任一单独**。[^goldson][^fade] 含义：**只停在具体会伤迁移**——必须包含 fade，否则短而顺的具体讲解是陷阱。[^fade]
- **Bjork「合意困难」vs「讲清楚、讲短」**：把讲解做到**极顺滑**可能只制造「学会了」的错觉，而没产生可迁移的学习；但「难」必须是 **germane** 的（指向结构），否则只是 extraneous 负荷。[^bjork][^sweller98] 含义：**短，是短在删冗余（coherence/redundancy），不是短在替读者把思考全做完**；结尾应留一个**生成性动作**（自检 / 迁移小问题）把「难」放在对的地方。[^bjork]
- **「短」与「深」的正面冲突**：SOLO 的 extended abstract / 迁移**需要连接与泛化**，这天然占篇幅；coherence/redundancy 又在要求砍。**裁决规则**：**篇幅只跟「结构连接」走**——加长只允许为了**新增一条因果链或一个边界**；纯粹增加事实、举例、复述的一律砍。[^solo][^mayer03]
- **单一答案不可能对所有人最优**：expertise reversal 直接说明「给新手的最优」对高手是负资产；因此**分层不是锦上添花，而是唯一正解**——用一个 deep 答案服务新手、或用一个 simple 答案服务专家，都错。[^kalyuga]
- **「假设不知道」vs「别太天真」**：知识诅咒鼓励假设无知，但 ELI5 也承认极端简化会牺牲准确性（80% 准确 > 讲丢）。**解法**：简单层配**明确边界**与**升级路径**，把简化当作可回收的脚手架，而非终局结论。[^cok][^eli5skill]

---

## 4. 来源（Sources）

调研日所有 DOI 均已通过 `https://doi.org/...` 解析验证题录。

**细化理论**
1. Elaboration Theory (Charlie Reigeluth) — InstructionalDesign.org — https://www.instructionaldesign.org/theories/elaboration-theory/
2. Reigeluth, C., & Stein, F. (1983). The elaboration theory of instruction. In C. Reigeluth (ed.), *Instructional Design Theories and Models.*（见 [1] 参考文献）
3. Reigeluth, C. (1992). Elaborating the elaboration theory. *ETR&D*, 40(3), 80–86.（见 [1] 参考文献）

**具体渐变**
4. Fyfe, E. R., McNeil, N. M., Son, J. Y., & Goldstone, R. L. (2014). Concreteness Fading in Mathematics and Science Instruction: a Systematic Review. *Educational Psychology Review*, 26(1), 9–25. https://doi.org/10.1007/s10648-014-9249-3
5. Goldstone, R. L., & Son, J. Y. (2005). The Transfer of Scientific Principles Using Concrete and Idealized Simulations. *Journal of the Learning Sciences*, 14(1), 69–110. https://doi.org/10.1207/s15327809jls1401_4
6. McNeil, N. M., & Fyfe, E. R. (2012). "Concreteness fading" promotes transfer of mathematical knowledge. *Learning and Instruction*, 22, 440–448. https://doi.org/10.1016/j.learninstruc.2012.05.001

**认知负荷理论**
7. Cognitive Load Theory (John Sweller) — InstructionalDesign.org — https://www.instructionaldesign.org/theories/cognitive-load/
8. Sweller, J., van Merriënboer, J. J. G., & Paas, F. (1998). Cognitive Architecture and Instructional Design. *Educational Psychology Review*, 10(3), 251–296. https://doi.org/10.1023/A:1022193728205
9. Kalyuga, S., Ayres, P., Chandler, P., & Sweller, J. (2003). The Expertise Reversal Effect. *Educational Psychologist*, 38(1), 23–31. https://doi.org/10.1207/S15326985EP3801_4
10. Sweller, J., & Cooper, G. A. (1985). The Use of Worked Examples as a Substitute for Problem Solving in Learning Algebra. *Cognition and Instruction*, 2(1), 59–89. https://doi.org/10.1207/s1532690xci0201_3
11. Renkl, A., & Atkinson, R. K. (2003). Structuring the Transition From Example Study to Problem Solving in Cognitive Skill Acquisition. *Educational Psychologist*, 38(1), 15–22. https://doi.org/10.1207/S15326985EP3801_3

**Mayer 多媒体学习**
12. Mayer, R. E., & Moreno, R. (2003). Nine Ways to Reduce Cognitive Load in Multimedia Learning. *Educational Psychologist*, 38(1), 43–52. https://doi.org/10.1207/S15326985EP3801_6
13. Mayer, R. E. (2014). Cognitive Theory of Multimedia Learning. In *The Cambridge Handbook of Multimedia Learning* (pp. 43–71). https://doi.org/10.1017/CBO9781139547369.005

**SOLO / Bloom**
14. Biggs, J. B., & Collis, K. F. (1982). Origin and Description of the SOLO Taxonomy. In *Evaluating the Quality of Learning* (pp. 17–31). https://doi.org/10.1016/B978-0-12-097552-5.50007-7
15. SOLO Taxonomy: Five Levels of Understanding Explained — Structural Learning — https://www.structural-learning.com/post/solo-taxonomy
16. Krathwohl, D. R. (2002). A Revision of Bloom's Taxonomy: An Overview. *Theory into Practice*, 41(4), 212–218. https://doi.org/10.1207/s15430421tip4104_2
17. Anderson & Krathwohl's Revised Taxonomy: A Teacher's Guide — Structural Learning — https://www.structural-learning.com/post/anderson-and-krathwohl

**Ausubel / Vygotsky / 脚手架**
18. Subsumption Theory (David Ausubel) — InstructionalDesign.org — https://www.instructionaldesign.org/theories/subsumption-theory/
19. Social Development Theory (Vygotsky) — InstructionalDesign.org — https://www.instructionaldesign.org/theories/social-development/
20. Zone of Proximal Development — SimplyPsychology（含 Wood, Bruner & Ross 1976 定义与 fading 机制）— https://www.simplypsychology.org/zone-of-proximal-development.html
21. Wood, D., Bruner, J. S., & Ross, G. (1976). The Role of Tutoring in Problem Solving. *Journal of Child Psychology and Psychiatry*, 17(2), 89–100. https://doi.org/10.1111/j.1469-7610.1976.tb00381.x

**费曼技巧**
22. Feynman Technique: The Ultimate Guide to Learning Anything Faster — Farnam Street — https://fs.blog/feynman-technique/

**分级讲解格式**
23. DreambigOu/ELI5 — `skills/eli5/SKILL.md` — https://github.com/DreambigOu/ELI5/blob/main/skills/eli5/SKILL.md
24. WIRED「5 Levels」视频系列（专家向五类递增专业度受众讲解；见 WIRED 视频中心与官方 YouTube 频道）— https://www.wired.com/video/ ； https://www.youtube.com/user/wired/
25. r/explainlikeimfive（ELI5 出处）— https://www.reddit.com/r/explainlikeimfive/

**类比 / 结构映射**
26. Gentner, D. (1983). Structure-Mapping: A Theoretical Framework for Analogy. *Cognitive Science*, 7(2), 155–170. https://doi.org/10.1207/s15516709cog0702_3
27. Gentner, D., & Markman, A. B. (1997). Structure mapping in analogy and similarity. *American Psychologist*, 52(1), 45–56. https://doi.org/10.1037/0003-066X.52.1.45

**合意困难 / 流畅性**
28. Bjork Learning and Forgetting Lab — Research（desirable difficulties、fluency、metacognition）— https://bjorklab.psych.ucla.edu/research/
29. Bjork, R. A. (1994). Memory and metamemory considerations in the training of human beings. In *Metacognition: Knowing about Knowing*（desirable difficulties 术语出处，见 [28]）

**知识诅咒**
30. The Curse of Knowledge — Effectiviology — https://effectiviology.com/curse-of-knowledge/
31. Camerer, C., Loewenstein, G., & Weber, M. (1989). The Curse of Knowledge in Economic Settings: An Experimental Analysis. *Journal of Political Economy*, 97(5), 1232–1254. https://doi.org/10.1086/261651

---

## 附录：调研日未能一手核验 / 需注意的点

- **Wikipedia 在调研网络环境下不可达**（wiki 域与 web.archive.org 均返回传输错误），故未引用其条目；改用 DOI 解析与大学/作者/机构页面替代。相关理论的原始文献条目均在 Sources 中给出。
- **WIRED「5 Levels」**：其站内视频检索与标签页未列出该系列（视频内容未被站内搜索索引）；调研日确认的是该系列为 WIRED 视频内容、并由 WIRED 官方 YouTube 频道承载，**具体单集永久 URL 未逐一核验**。
- **Reigeluth (1992/1999) 与 Ausubel (1963/1968) 原书**：本次通过 InstructionalDesign.org 的二手综述确认观点与引文（含 Ausubel 名言），未逐页核对原书。
- **费曼技巧**：确认其为流行学习方法而非实验检验的教学理论（来源 [22] 本身也如此定位）。
- **Bjork (1994) 术语出处**：由 UCLA 实验室页面 [28] 转述，未取到原篇章 DOI。
