# 主流笔记 / PKM 应用接入可行性调研（为 `knowledge-distill` 智识沉淀扩展）

> 范围：调研市面主流笔记 / 知识管理（PKM）应用，判断 `knowledge-distill` 技能后续能现实地接入哪些；重点评估 语雀（Yuque）、飞书（Feishu/Lark）、Notion。
> 调研日期（access date）：2026-09-14。所有 URL 均在调研日实测可访问。
> 方法：**以一手来源为准**（官方产品文档、官方 API 参考、官方 SDK / 官方 MCP 仓库、官方存储格式说明、官方 GitHub 仓库）。listicle / SEO 站点仅用于发现候选名单，能力判断一律回一手源确认；每一条能力声明都带脚注指向来源。对未能在一手源确认的，明确标注「未确认」。

## 0. 前提：本技能当前的技术现实

`knowledge-distill` 是**文件系统型**工具，不调用任何网络/云 API：

- 写入 `note_root/<分类>/<标题>.md`，每个分类一个 `00-分类索引.md`（Markdown 表 + 「已收录疑问」段落）。
- 链接语法由 `format` 决定：`obsidian` → `[[wikilinks]]`；`markdown` → `[标题](标题.md)`。
- Obsidian 用 YAML frontmatter（`tags` / `created` / `source`）；普通 Markdown 用头部块。
- `skill_tools.py` 做确定性文件操作：原子写入/替换、正文关键词/正则检索、`list-structure`、lint 链接与索引、生成分类索引与 MOC。

**由此推出接入判据**（贯穿全文）：

1. **能否原样写入 Markdown、并原样读回 Markdown？**（本技能的知识载体是 Markdown 文本；无法 round-trip 就需要写转换器）
2. **是「本地文件夹」还是「云/专有存储」？** 本地文件夹 → 可能零代码（仅配置）；云/专有 → 需新增客户端 + 鉴权 + 格式适配。
3. **是「一个文件一篇笔记」，还是「块/大纲/富文本」模型？** 块模型会让链接（`[[ ]]` 与反向链接）、标题即文件名、索引对齐等现有机制失效。
4. **增删改查与目录/分类能力是否齐全？** 本技能需要「建/改笔记 + 建/归类目录 + 检索」。

---

## 1. 集成机制分类学（本报告的核心分类）

| 类别 | 含义 | 对本技能的含义 | 代表应用 |
| --- | --- | --- | --- |
| **A. 本地 Markdown 文件夹** | 应用直接 watcher 一个本地文件夹里的 `.md` | **仅配置**：把 `note_root` 指到该应用监视的目录即可，无需改代码；链接语法看是否支持 `[[ ]]` | Obsidian、Foam、Dendron、Zettlr、Typora / VS Code、Logseq（文件模式） |
| **B. 官方 HTTP API / OpenAPI / SDK** | 纯云或本地服务，提供 REST/Graph API | **需新增客户端**：鉴权 + 端点封装 + 格式转换；能否 round-trip Markdown 决定难度 | Notion、语雀、飞书、OneNote、Confluence、Google Keep、Capacities |
| **C. 本地数据库 / 专有存储 + 本地 API/CLI** | 数据在自己的库/文件里，但开有本地 API 或 CLI | **需新增本地客户端**：鉴权简单（本地 token），但内容多为专有块/大纲模型 | Joplin、思源 SiYuan、Trilium、Anytype、Logseq（HTTP API） |
| **D. 已有 MCP / 插件暴露** | 官方或社区已把该应用封装成 MCP server / 插件 | 可作为**过渡桥梁**：技能调用 MCP 工具，而非直连 API；稳定性与覆盖度参差 | Notion、飞书、语雀、Evernote、flomo、Capacities（官方）；Obsidian、Joplin、SiYuan（社区） |
| **E. 无可用 API / 不可行** | 官方无公开写读接口，或内容强绑定客户端/加密 | **不可行 / 仅只读导出**，不建议投入 | wolai、FlowUs、有道云笔记、为知笔记、Roam、Apple Notes、Bear（仅 URL scheme）、flomo（仅写入）、Standard Notes（E2E） |

> 说明：D 与 A–C 会重叠（一个应用可能既有 API 又有 MCP）。D 的价值在「降低接入成本」，但**官方 MCP 未必覆盖本技能需要的写/改语义**——飞书官方 MCP 即典型反例（见 §3.2）。

---

## 2. 主流应用全景表

存储模型：本地文件 / 本地库 / 纯云。
可行性：容易（配置级或官方 Markdown 直通）/ 中等（新增客户端但可 round-trip Markdown）/ 困难（需块/富文本转换或能力受限）/ 不可行。

| 名称 | 厂商/性质 | 存储模型 | 链接语法 | 官方 API/SDK | MCP | 导入/导出 | 对该技能的集成方式 | 可行性 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Obsidian | Obsidian.md / 本地优先 | 本地 `.md` 文件夹（vault）[1] | `[[wikilink]]`[2] | 无外部 API；仅插件 TypeScript API[3] | 社区（如 [43]） | 原生 Markdown | **配置级**：`note_root` 指向 vault 子目录（当前已支持） | 容易（已支持） |
| 普通 Markdown 编辑器（Typora / VS Code） | 各家 / 本地 | 本地 `.md` 文件夹[38] | 标准 `[文字](文件.md)` | 无（就是文件） | 社区 | 原生 Markdown | **配置级** | 容易（已支持） |
| Foam | 开源（VS Code 扩展） | 本地 `.md` 文件夹 | `[[wikilink]]`（Foam 语法） | 无（文件）[40] | 社区 | 原生 Markdown | 配置级 | 容易 |
| Dendron | 开源（VS Code 扩展） | 本地 `.md` 文件夹 | `[[wikilink]]` | 无（文件）[41] | 社区 | 原生 Markdown | 配置级 | 容易 |
| Zettlr | 开源 | 本地 `.md` 文件夹 | 标准 / `[[ ]]`[39] | 无（文件） | — | 原生 Markdown | 配置级 | 容易 |
| Logseq | 开源 / 本地优先 | 本地 Markdown/EDN（大纲） | `[[wikilink]]` | 本地 HTTP API（`127.0.0.1:12315/api`，Bearer）调用插件 SDK；插件 API[4][5] | 社区 | Markdown 文件 | **需本地客户端**（块/大纲语义，直接写 .md 有冲突风险） | 中等 |
| 思源 SiYuan | 开源 / 本地优先（可选自托管） | 本地工作空间（专有格式 + `.sy`） | `((块引用))` / 自有 | 本地 HTTP API `127.0.0.1:6806`，`Authorization: Token`；`/api/filetree/createDocWithMd`、`/api/export/exportMdContent`、`/api/sql`[20] | 社区 [45] | 支持 Markdown 导入导出 | **需本地客户端**：Markdown 进（createDocWithMd）/ 出（exportMdContent） | 中等 |
| Anytype | 开源 / 本地加密 | 本地加密对象库 + 网络同步 | 自有（对象/关系） | 官方 API（对象/空间/搜索/markdown body patching）+ 官方 CLI[22][23] | 社区 | Markdown body patching | 需本地客户端（对象模型） | 中等 |
| Trilium（TriliumNext） | 开源 / 本地 | 本地 SQLite 库 | 自有（note 树） | **ETAPI** REST API（本地）[21] | 社区 | Markdown 导入导出 | 需本地客户端 | 中等 |
| Joplin | 开源 / 本地优先 | 本地 SQLite 库 + 资源文件 | Markdown 链接 | **Data API** `localhost:41184`（token）`/notes` `/folders` `/search`；`body` 即 Markdown[6] | 社区 [44] | 原生 Markdown | **需本地客户端**：`POST /notes` body 传 Markdown、`GET /search` 检索 | 中等 |
| Notion | Notion / 纯云 | 纯云（block） | 自有（页/块；可含链接块） | 官方 REST API；`POST /v1/pages` 带 `markdown`、`GET/PATCH /v1/pages/:id/markdown`[7][9] | **官方** [10] | Markdown/CSV/HTML 导入导出 | **新增 API 客户端**（markdown 直通，无需块转换器） | 中等（云中最低成本） |
| 语雀 Yuque | 阿里 / 纯云 | 纯云（`lake` 专有格式，可转 Markdown） | 自有（文档链接） | 官方 OpenAPI v2（token）；限流 5000/时、100/秒[11] | **官方** [13] | 支持 Markdown 导入导出 | **新增 API 客户端**（Markdown body / lake 转换） | 中等 |
| 飞书 Feishu / Lark | 字节 / 纯云 | 纯云（docx block 树） | 自有（文档/知识库节点） | 官方 OpenAPI（App ID/Secret → tenant/user_access_token）；docx block 增删改 + `document.convert`（Markdown/HTML→块）[15][16][17][19] | **官方** [18]（但**不支持直接编辑云文档**） | 导入/导出 | **新增 API 客户端 + 块模型适配** | 困难 |
| OneNote | Microsoft / 纯云 | 纯云（页 = HTML） | 自有 | Microsoft Graph；`/me/onenote/...`；**仅委派权限，无 app-only**；页面内容为 `text/html`[24][25] | 社区/第三方 | 导入/导出 | 新增 Graph 客户端 + Markdown↔HTML 转换 | 困难 |
| Confluence | Atlassian / 云+Server | 纯云/自托管 | 自有（页面树） | REST API v2；OAuth 2.0/scopes 或用户态；正文为 storage(XHTML)/ADF[27] | 社区/第三方 | 导入/导出 | 新增客户端 + HTML/ADF 转换 | 困难 |
| Evernote / 印象笔记 | Evernote(Bending Spoons) / 纯云 | 纯云 | 自有 | **Legacy API 已 Deprecated**；官方转向远程 MCP（beta）[26] | **官方**（beta）[26] | 导入/导出 | 走官方 MCP 或放弃 | 困难（官方已弃旧 API） |
| 印象笔记（中国） | 印象笔记 / 纯云 | 纯云 | 自有 | 未在官方来源确认（与 Evernote 已拆分） | 未确认 | 导入/导出 | 不建议 | 未确认 |
| Google Keep | Google / 纯云（Workspace） | 纯云 | 自有 | Keep API v1（notes.create/list/get/delete、permissions、media）[28] | — | 导入导出（客户端） | 新增客户端；**面向 Google Workspace，门槛高（见 §4 注）** | 困难 |
| Capacities | Capacities / 纯云 | 纯云（对象库） | 自有 | API Beta **将于 2026-09-01 弃用**；有 x-callback-url 与新 API/MCP[31] | 官方（新） | 导入/导出 | 观望（旧 API 正在弃用） | 困难 |
| flomo | flomo / 纯云 | 纯云（卡片） | 自有（标签） | API + URL Scheme **需 PRO**；仅「单用户输入记录」（写入），url scheme `flomo://create`（≤5000 字）[29] | 有 [30] | 支持导入导出（非 API） | **仅写入**，无法读回/检索 → 与技能语义不匹配 | 不可行（仅输入） |
| 我来 wolai | wolai / 纯云 | 纯云 | 自有 | 官网 `/developers` 仅登录页，无公开文档；仅内部 `api.wolai.com`[33] | — | 导入导出 | 不建议 | 不可行 |
| FlowUs 息流 | FlowUs / 纯云 | 纯云 | 自有 | 官网未提供公开 API 文档[34] | — | 导入导出 | 不建议 | 不可行 |
| 有道云笔记 | 网易 / 纯云 | 纯云 | 自有 | 官网未提供公开 API 文档[35] | — | 导入导出 | 不建议 | 不可行 |
| 为知笔记 WizNote | 为知 / 云+自托管 | 云/本地库 | 自有 | 未在官方来源确认公开 API[36] | — | 导入导出 | 不建议 | 未确认 |
| Roam Research | Roam / 纯云 | 纯云（block） | `[[ ]]` | 无官方公开 API 文档[37]；社区有非官方 backend API | — | 导入导出 | 不建议 | 不可行 |
| Bear | Shiny Frog / 本地（Apple） | 本地 + iCloud | 自有 | **仅 X-Callback-URL API**（macOS/iOS），无 REST[32] | — | 导入导出 | 仅 URL scheme 追加，能力弱 | 不可行 |
| Apple Notes | Apple / 本地（Apple） | 本地 + iCloud（专有库） | 无 | 无官方 API（未确认官方声明）；仅 AppleScript / Shortcuts | — | 导入导出 | 不建议 | 不可行 |
| AppFlowy | 开源 / 本地优先 | 本地库 + 云 | 自有 | 无面向外部的通用 API；官方接 Zapier[42] | 社区 | 导入导出 | 不建议 | 困难 |
| AFFiNE | 开源 / 本地优先 | 本地库 + 云 | 自有 | 官网未提供公开 API 文档 | 社区 | 导入导出 | 不建议 | 未确认 |
| Heptabase / Tana / RemNote / Notesnook / UpNote / Standard Notes | 各家 / 云或本地 | 云或本地（多为 E2E 或专有） | 自有 | 调研日官网未见面向外部的公开内容 API | 少见 | 导入导出 | 不建议（Standard Notes 端到端加密，服务端拿不到明文） | 不可行/未确认 |

> 表中「未确认」= 调研日在官方来源未找到公开 API 文档，**不等于官方绝对没有**，只是无法用一手源证实。个人账号向的 Google Keep、Heptabase 等若日后开放，需重新评估。

---

## 3. 优先目标深挖

### 3.1 语雀 Yuque（用户点名）

- **存储模型**：纯云。文档格式 `format` 为 `lake`（语雀自研富文本，即 LakexEditor 文档模型）；开放平台支持以 Markdown 方式读写与转换 [11][14]。
- **鉴权**：个人/团队 Token。请求头带 Token；团队资源用空间子域名。Token 在 https://www.yuque.com/settings/tokens 生成 [11][13]。
- **访问范围（重要限制）**：自 2022-04-10 起，**个人 token 只能访问该 token 有权限的文档**（不再能读语雀上所有公开文档）；团队 token 可访问团队内文档 [12]。
- **限流**：每小时 ≤ 5000 次、每秒 ≤ 100 次；**同一用户/团队下所有 token 共享**该额度；响应带 `X-RateLimit-Limit` / `X-RateLimit-Remaining` [11]。
- **接口形态**：OpenAPI v2，域 `https://www.yuque.com`；路径概念 `group_login` / `book_slug` / `doc_slug` / `book_id` / `doc_id`；同一操作有「路径版」与「ID 版」重载（如获取文档：`GET /api/v2/repos/{group_login}/{book_slug}/docs/{doc_slug}` 或 `GET /api/v2/repos/{book_id}/docs/{doc_id}`）[11]。官方另提供 OAS（下载需登录）与 Postman 导入 [11]。
- **Markdown 能力**：语雀编辑器/转换层支持 `text/html`、`text/markdown`、`text/plain`、`text/lake` 等格式的进出（`insertAtSelection` / `getNodeContent`）[11]；因此**可以 Markdown 进、Markdown 出**，但底层仍是 lake，存在「往返可能丢失部分块样式」的风险。
- **MCP**：**官方** `yuque/yuque-mcp-server`，支持 AI 助手读写语雀知识库，token 从开发者设置获取；支持 claude-desktop / vscode / cursor / trae / opencode 等 [13]。
- **对技能的接入方式与工作量**：新增一个 Yuque 客户端（token 配置 + 创建/更新文档 + 列出知识库/目录 + 搜索）。分类可映射为知识库或目录；索引文件可作为一篇文档。**中等**。
- **硬点**：lake↔Markdown 往返保真；个人 token 权限范围；团队空间子域名。

### 3.2 飞书 Feishu / Lark（用户点名）

- **存储模型**：纯云，`docx` 是 **块（block）树**模型；另有多维表格、Wiki 知识空间等对象 [15]。
- **鉴权**：自建应用 App ID / App Secret → `tenant_access_token`（应用身份）或 OAuth 用户授权 → `user_access_token`（访问个人文档必需）；官方 MCP 支持 `--oauth --token-mode user_access_token` [18]。
- **接口形态**（docx v1，全部为官方文档）：
  - `docx.v1.document.create` 创建文档（可指定标题与文件夹）[16][19]
  - `docx.v1.document.get` 文档基本信息（标题、最新 revision）[19]
  - `docx.v1.document.rawContent` **纯文本**内容 [19]
  - `docx.v1.document.convert` **把 Markdown/HTML 转成块** [17][19]
  - `docx.v1.documentBlockChildren.create` / `documentBlock.patch` / `documentBlock.batchUpdate` / `documentBlockChildren.batchDelete` 增删改块 [19]
  - Wiki：`wiki.v2.space.*` / `wiki.v2.spaceNode.*`（创建节点、移动、列出子节点、搜索 wiki）[19]
- **Markdown 能力**：**不能直接写原始 Markdown**——需先用 `document.convert` 把 Markdown 转成 block，再写入；读取侧 `rawContent` 返回的是**纯文本**（丢失结构），要结构化读回需遍历 blocks。即 **Markdown 进要转换、Markdown 出要自己拼**。
- **MCP**：**官方** `larksuite/lark-openapi-mcp`（Beta）。但官方 README 明确：**不支持直接编辑飞书云文档，仅支持导入与读取**（"Direct editing of Feishu cloud documents is not supported (only importing and reading are available)"）[18]。因此 MCP **不能**承担本技能的「更新/合并笔记」语义。
- **对技能的接入方式与工作量**：新增飞书客户端（App 鉴权 + 用户 OAuth + `document.convert` + block 写入 + Wiki 节点管理 + 搜索）。分类可映射到 Wiki 空间/节点或文件夹。**困难**（块模型 + 权限 + MCP 不可写）。
- **硬点**：块模型使「标题即文件名」「`[[双链]]`」「索引与笔记一一对应」等机制需要重新设计；`convert` 只解决写入，读取仍需自研 block→Markdown。

### 3.3 Notion

- **存储模型**：纯云，页面 = block 树 [7]。
- **鉴权**：Bearer token（internal connection token / OAuth / personal access token，PAT）[7]。
- **Markdown 直通（关键）**：官方已提供「enhanced markdown / Notion-flavored Markdown」通道 [9]：
  - 创建：`POST /v1/pages` 传 `markdown`（与 `children`/`content` 互斥；大文档可 `allow_async` 走 202 异步）[9]
  - 读取：`GET /v1/pages/:page_id/markdown` 返回整页 Markdown [9]
  - 更新：`PATCH /v1/pages/:page_id/markdown` 插入/替换内容 [9]
  - 未识别的块会以 `<unknown url alt/>` 出现，可回退 blocks API [9]
- **限流**：Business/Enterprise 600 次/分（约 10/秒）；其余计划 180 次/分（约 3/秒）；另有工作区级共享限流；超限 429/529 带 `Retry-After` [8]。
- **MCP**：**官方** `makenotion/notion-mcp-server`（MIT，活跃）[10]。
- **对技能的接入方式与工作量**：新增 Notion 客户端（token + 创建页/查改 Markdown + 检索 `POST /v1/search` + 数据源/页面树）。分类可用父页面/数据库。**中等（云端里成本最低）**，因为**无需自研块转换器**。
- **硬点**：Markdown 是「Notion-flavored」，部分块（如数据库、评论）不可逆；限流需排队与退避。

### 3.4 最佳「本地 Markdown 文件夹」选项（零/低成本）

- **Obsidian**：vault 就是本地文件夹里的 Markdown 纯文本，外部改动会自动刷新；`.obsidian` 存配置 [1]；内部链接 `[[...]]` [2]。**当前已支持**，且是 A 类里最成熟的载体。
- **Foam / Dendron / Zettlr / Typora / VS Code**：同样是「本地 .md 文件夹」，`[[ ]]` 或标准链接 [38][39][40][41]。对本技能而言与 Obsidian/普通 Markdown **同类**，**只需在文档与配置里把 `note_root` 指向对应文件夹即可**，无需新增代码。建议在 references 中补一段「其它本地 Markdown 应用」说明，而非为每个应用写适配器。
- **SiYuan（若要在本地非 Obsidian 里做「真接入」）**：本地内核 HTTP API（`127.0.0.1:6806`，`Authorization: Token xxx`）提供 `createDocWithMd`（Markdown 进）、`exportMdContent`（Markdown 出）、`sql`（结构化检索）、`insertBlock`、notebook 管理 [20]。是 A/C 类里**Markdown round-trip 最干净**的本地选择。**中等**成本，且需注意 `createDocWithMd` 同 path 不覆盖（改写语义要另想办法）。

---

## 4. 推荐与排序

### 4.1 按「接入成本」分组

**第一梯队：配置级（零/极少代码）**
- 本地 Markdown 文件夹全家桶：Obsidian（已支持）、普通 Markdown（已支持）、Foam、Dendron、Zettlr、Typora/VS Code。
- 行动：**不写适配器**，只在 `references/plain-markdown-best-practices.md` 增补「哪些应用属于本地 Markdown 文件夹、如何把 `note_root` 指过去、各自链接语法差异」，并在首次配置的选项里把「其它」引导到「选一个本地文件夹」。

**第二梯队：新增 API 客户端，但可 Markdown round-trip（性价比最高）**
- **notion**：官方已提供 `POST /v1/pages(markdown)` / `GET|PATCH /v1/pages/:id/markdown`，**免块转换器**；有官方 MCP。[7][9][10]
- **语雀 Yuque**：官方 OpenAPI v2 + 官方 MCP；支持 Markdown/lake；中文用户契合度高。[11][13]
- 本地侧的 **SiYuan**：本地 HTTP + Markdown 进出，无云鉴权负担。[20]
- 次选 **Joplin / Trilium / Anytype**：本地 API/CLI，Markdown 或 markdown-body 能力尚可，但模型与现有「文件+索引」机制差异更大。[6][21][22]

**第三梯队：困难（需块/富文本转换或能力受限）**
- **飞书 Feishu**：文档为 block 树，写入要 `document.convert`，读取要自研 block→Markdown；官方 MCP **不可编辑**。[17][18][19]
- **OneNote**：内容为 HTML，需 Markdown↔HTML；仅委派权限。[24][25]
- **Confluence**：storage(XHTML)/ADF 转换，OAuth/scopes。[27]
- **Google Keep**：Workspace 面向，接入门槛高（调研日未在一手源确认个人账号可用性）。[28]

**不建议 / 不可行**
- 纯云且官方无公开写读 API：**wolai、FlowUs、有道云笔记、为知笔记（未确认）、Roam、Apple Notes**。[33][34][35][36][37]
- **flomo**：API/URL scheme 仅「写入」且需 PRO，无法读回与检索，与本技能「沉淀 + 检索 + 索引对齐」的核心语义不匹配。[29]
- **Bear**：仅 X-Callback-URL，能力弱。[32]
- **Evernote**：旧 API 已 Deprecated，官方转远程 MCP（beta），不稳定。[26]

### 4.2 建议的下一步 3 个集成（排行）

1. **语雀 Yuque** —— 用户点名，且官方 OpenAPI v2 + 官方 MCP 齐备、支持 Markdown/lake 往返，中文用户覆盖面最广；接入的是「新增客户端」，风险集中在 lake↔Markdown 保真与个人 token 权限范围。[11][13]
2. **Notion** —— 官方已提供 markdown 直通的创建/读取/更新三个端点，**免去块转换器**，是主流云笔记里单位成本最低的一档；有官方 MCP 兜底。[9][10]
3. **飞书 Feishu / Lark** —— 用户点名，官方能力最全（`document.convert` + block 增删改 + Wiki），但块模型 + 读取需自研 + 官方 MCP 不可写，工时最高；建议排在语雀/Notion 之后作为第三个攻坚目标。[17][18][19]

> 若更看重「本地、零鉴权、快落地」：把第 3 位换成 **SiYuan**（本地 HTTP + Markdown 进出）或先做 **Anytype/Trilium/Joplin** 任一本地库；本地类的共同难点是专有模型与现有「文件 + `00-分类索引.md`」机制的对齐。
> 「文件夹级」的低成本动作可与上述并行：更新 references，明确宣告「凡本地 Markdown 文件夹类应用均受支持」。

### 4.3 关键取舍与硬点小结

- **不要为每个本地 Markdown 编辑器写适配器**：Foam/Dendron/Zettlr/Typora 与本技能已支持的两种格式同构，配置/doc 说明即可。
- **块模型是最大结构性障碍**：飞书、Notion（历史）、OneNote、Confluence、Roam 都是块/富文本；Notion 因官方 Markdown 端点而「破格」变容易，飞书/OneNote/Confluence 则必须做转换层。
- **官方 MCP ≠ 可直接复用**：飞书官方 MCP 不能编辑云文档 [18]；MCP 更适合做「读/搜」补充，写/合并仍需自研客户端。
- **Round-trip 保真要单列风险**：语雀 lake、Notion-flavored Markdown、飞书 block 都可能丢失 callout / 块引用 / 附件等样式——建议为每个新增后端定义「可安全写入的 Markdown 子集」。
- **鉴权与配额**：语雀 token 共享限流 [11]；Notion 3 rps 默认 [8]；飞书需应用审核与权限申请 [18]。这些要在客户端里做退避/排队，否则会触发 429。

---

## 5. 来源（Sources）

以下 URL 均在 2026-09-14 实测可访问。

1. Obsidian — How Obsidian stores data（本地 Markdown vault、`.obsidian`、外部改动自动刷新）— https://help.obsidian.md/data-storage
2. Obsidian — Internal links（`[[wikilink]]` 语法）— https://help.obsidian.md/links
3. Obsidian API（插件 TypeScript 类型定义，非外部 REST API）— https://github.com/obsidianmd/obsidian-api
4. Logseq HTTP API server（`127.0.0.1:12315/api`、Bearer、调用插件 SDK）— https://github.com/logseq/logseq/blob/master/resources/docs/api_server.html
5. Logseq Plugin SDK 文档 — https://plugins-doc.logseq.com
6. Joplin Data API（41184、token、`/notes`/`/folders`/`/search`、`body` 为 Markdown）— https://github.com/laurent22/joplin/blob/dev/readme/api/references/rest_api.md
7. Notion API Introduction（Bearer、REST、分页）— https://developers.notion.com/reference/intro
8. Notion Request limits（3 rps / 10 rps、429/529、Retry-After）— https://developers.notion.com/reference/request-limits
9. Notion Working with markdown content（`POST /v1/pages(markdown)`、`GET/PATCH .../markdown`）— https://developers.notion.com/guides/data-apis/working-with-markdown-content
10. Notion 官方 MCP Server — https://github.com/makenotion/notion-mcp-server
11. 语雀 — OpenAPI 总览（域名、限流 5000/时·100/秒、字段解释、OAS 下载）— https://www.yuque.com/yuque/developer/api
12. 语雀 — 开放 API 访问范围变更（个人 token 仅限有权限文档）— https://www.yuque.com/yuque/developer/vzippmige58g7r9t
13. 语雀官方 MCP Server（读写知识库、token 设置）— https://github.com/yuque/yuque-mcp-server ；Token 入口 https://www.yuque.com/settings/tokens
14. 语雀 — LakexEditor 文档（支持 `text/markdown`/`text/lake`/`text/html` 转换）— https://www.yuque.com/yuque/developer/gfoax065u2v72isu （见 OpenAPI 书内「开始使用」）
15. 飞书开放平台 — 文档概述（docx 块、Wiki、token 概念）— https://open.feishu.cn/document/server-docs/docs/docs-overview
16. 飞书 — 创建文档 `docx.v1.document.create` — https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/create
17. 飞书 — 转换 Markdown/HTML 为块 `docx.v1.document.convert` — https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/convert
18. 飞书官方 OpenAPI MCP（含「不支持直接编辑云文档」说明）— https://github.com/larksuite/lark-openapi-mcp
19. 飞书 MCP 全量工具/接口列表（docx v1、wiki v2 各端点）— https://github.com/larksuite/lark-openapi-mcp/blob/main/docs/reference/tool-presets/tools-en.md
20. 思源 SiYuan — API 文档（`127.0.0.1:6806`、`Authorization: Token`、`createDocWithMd`、`exportMdContent`、`sql`、`insertBlock`）— https://github.com/siyuan-note/siyuan/blob/master/docs/API.zh-CN.md
21. Trilium — ETAPI (REST API) — https://docs.triliumnotes.org/user-guide/advanced-usage/etapi
22. Anytype API 参考（Auth / Objects / Spaces / Search / markdown body patching）— https://developers.anytype.io/docs/reference/
23. Anytype 开发者指南 — https://developers.anytype.io/docs/guides/
24. OneNote REST API 概览（Graph 根 URL、仅委派权限）— https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview
25. OneNote 创建页面（`POST /onenote/pages`，内容 `text/html`）— https://learn.microsoft.com/en-us/graph/api/onenote-post-pages
26. Evernote Developers（官方 MCP beta；导航标注 Legacy API Deprecated）— https://dev.evernote.com/mcp
27. Confluence Cloud REST API v2（OAuth/scopes、storage/ADF 格式）— https://developer.atlassian.com/cloud/confluence/rest/v2/intro/
28. Google Keep API v1（notes.create/list/get/delete、permissions、media；归属 Google Workspace）— https://developers.google.com/keep/api/reference/rest
29. flomo — API & URL Scheme（需 PRO；单用户输入记录；`flomo://create` ≤5000 字）— https://help.flomoapp.com/advance/api.html
30. flomo — MCP（AI 工具连接）— https://help.flomoapp.com/advance/mcp
31. Capacities — API Beta（**将于 2026-09-01 弃用**；另有 x-callback-url 与新 API/MCP）— https://docs.capacities.io/developer/api
32. Bear — X-Callback-URL API — https://bear.app/faq/x-callback-url-scheme-documentation/
33. 我来 wolai — 开发者页（仅登录页，无公开文档）— https://www.wolai.com/developers
34. FlowUs 息流 官网（未见公开 API 文档）— https://flowus.cn/
35. 有道云笔记 官网（未见公开 API 文档）— https://note.youdao.com/
36. 为知笔记 WizNote 官网（官网未见公开 API 文档；GitHub 有 WizNoteLite）— https://www.wiz.cn/
37. Roam Research 官网（无官方公开 API 文档）— https://roamresearch.com/
38. Typora 官网（本地 Markdown 编辑器）— https://typora.io/
39. Zettlr 官网（本地 Markdown 编辑器）— https://www.zettlr.com/
40. Foam 官网（VS Code + Markdown 文件夹 + `[[ ]]`）— https://foambubble.github.io/foam/
41. Dendron 官网（VS Code + Markdown 文件夹）— https://www.dendron.so/
42. AppFlowy 官方 Zapier 集成（无通用外部 API 佐证）— https://zapier.com/apps/appflowy/integrations
43. Obsidian MCP（社区示例）— https://github.com/cyanheads/obsidian-mcp-server
44. Joplin MCP（社区）— https://github.com/alondmnt/joplin-mcp
45. SiYuan MCP（社区）— https://github.com/xgq18237/siyuan_mcp_server

---

## 附录：调研日未能在一手来源确认的点（明确标注 unverified）

- **印象笔记（中国）** 是否提供公开 API：未见官方开放平台文档，未确认。
- **为知笔记 WizNote** 的公开 API/开放平台：官网未见，未确认（仅找到开源客户端 WizNoteLite）。
- **AFFiNE / Heptabase / Tana / RemNote / Notesnook / UpNote / Standard Notes** 是否存在面向外部的公开内容 API：调研日官网未见，未确认（Standard Notes 为端到端加密，服务端无可读明文，即便有 API 也难直接沉淀明文 Markdown）。
- **Google Keep API** 对个人（非 Workspace）账号的可用性/限制：官方页面归属 Google Workspace，具体「仅企业、需服务账号 + 域委派」的措辞未在本次抓取中直接读到原文，标注为**未完全确认**。
- **Apple Notes** 是否有官方开发者 API：未找到官方明确声明；能力「无公开 API」为间接判断。
- 语雀官方 OAS 文件（`yuque_openapi_*.yaml`）下载需登录，故端点细节依据官方文档总览页 [11] 与语雀官方 MCP [13]，未逐一比对 OAS 全文。
