# 智识沉淀技能接入飞书 / 语雀 / Notion 云笔记调研

> 调研日期：2026-09-14
> 调研对象：`knowledge-distill`（智识沉淀）技能能否在现有本地 Obsidian / Markdown 存储之外，把笔记同步/写入 **飞书（Feishu / Lark）**、**语雀（Yuque）**、**Notion** 三家云笔记。
> 方法：只查一手来源（各平台官方开发者文档 / 官方 API 参考）。飞书文档站提供 `.md` 镜像（页面 `<link rel="alternate" type="text/markdown">`），本次以该镜像为准；语雀开发者文档为前端渲染站点，正文经其站内数据接口取得，但「接口列表」以**需登录下载的 OAS / HTML 附件**发布，未能读取（详见 §2.3 与 §五）。
> 标注约定：凡无法从一手来源确认的事实，一律写 **`未能从一手来源确认`**，不作推断性断言。

---

## 一、概述与调研范围

### 1.1 技能现状

`knowledge-distill` 目前把对话沉淀为**本地 Markdown 笔记**：一篇笔记一个文件，按分类放在 `AI笔记/<分类>/` 子目录下，每个分类维护一个 `00-分类索引.md`；另支持备份/回退、MOC、健康检查等。脚本 `scripts/skill_tools.py` 为**纯标准库**实现（`argparse/datetime/hashlib/json/os/posixpath/re/shutil/sys/urllib.parse/pathlib`）。

### 1.2 云存储后端需要满足的能力（本调研的验收清单）

| # | 能力 | 说明 |
| - | ---- | ---- |
| 1 | 创建文档 | 新建一篇笔记 |
| 2 | 更新已有文档 | 改写 / 追加（合并场景） |
| 3 | 设置元数据 | 标题、标签（tags） |
| 4 | 归档到文件夹 / 笔记本 | 对应技能的「分类」概念 |
| 5 | 搜索 / 列出文档 | 对应 `search-notes` / `list-structure` |
| 6 | 文档间链接 | 知识图谱 / 反向链接 |
| 7 | 读回文档 | 合并 / 更新 / 回退前读取原文 |

### 1.3 区域变体

- **飞书**：中国大陆 `open.feishu.cn`；国际版 **Lark** `open.larksuite.com`，**API 路径相同**（例：`/document/server-docs/docs/docs/docx-v1/document/create` 在 `open.larksuite.com` 下同样存在 `.md` 镜像，本次已实测）。来源：<https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create> 与 <https://open.larksuite.com/document/server-docs/docs/docs/docx-v1/document/create.md>
- **语雀**：官方开放 API 面向 SaaS（`www.yuque.com`）。**私有化部署（语雀私有化）是否提供同一开放 API，未能从一手来源确认**。
- **Notion**：单一全球 API（`api.notion.com`），无区域变体。

---

## 二、三平台逐一

### 2.1 Notion

#### 2.1.1 API 是否存在

有公开 API：**Notion API**，基址 `https://api.notion.com`，需带版本头 `Notion-Version`（本次文档最新为 `2026-03-11`）。
来源：<https://developers.notion.com/reference/post-page>、<https://developers.notion.com/reference/authentication>

#### 2.1.2 认证

- 通过 HTTP `Authorization: Bearer <token>` 认证。来源：<https://developers.notion.com/reference/authentication>
- 凭证类型（三种连接方式）：
  - **Internal connection**（内部集成，机器人身份，工作区内使用）；
  - **Personal access token（PAT）**（以创建者用户身份）；
  - **Public connection（OAuth）**（代表授权用户）。
  来源：<https://developers.notion.com/reference/authentication>、<https://developers.notion.com/guides/get-started/authorization>
- 需要的**能力（capabilities）**而非传统 OAuth scope：`insert_content`、`insert_property`、`read_content`、`update_content`；缺少对应能力返回 403。来源：<https://developers.notion.com/reference/post-page>、<https://developers.notion.com/guides/data-apis/working-with-markdown-content>、<https://developers.notion.com/reference/patch-block-children>
- 审批流程：**未能从一手来源确认**（文档未描述公共集成的审核要求）。

#### 2.1.3 所需操作对照

| 能力 | 端点 / SDK | 说明 | 来源 |
| ---- | ---------- | ---- | ---- |
| 创建文档 | `POST /v1/pages` | 支持 `markdown` 参数（**Notion-flavored / enhanced Markdown**，原生直传），与 `children`/`content` 互斥；省略 `properties.title` 时取首个 `# h1` 作标题 | <https://developers.notion.com/reference/post-page>、<https://developers.notion.com/guides/data-apis/working-with-markdown-content> |
| 创建（块方式） | `POST /v1/pages`（`children`） | 块数组，单请求最多 100 个 | <https://developers.notion.com/reference/post-page> |
| 更新已有文档 | `PATCH /v1/pages/{page_id}/markdown` | 命令：`update_content`（查找替换）、`replace_content`（整体替换）；旧版 `insert_content`、`replace_content_range` | <https://developers.notion.com/guides/data-apis/working-with-markdown-content> |
| 更新属性 / 标题 | `PATCH /v1/pages/{page_id}` | 更新 `properties`（数据源页面）、图标、封面、`in_trash` 等；页面 `parent` 不可改 | <https://developers.notion.com/reference/patch-page> |
| 追加块 | `PATCH /v1/blocks/{block_id}/children` | 单请求最多 100 个子块；支持 `position`（start / end / after_block） | <https://developers.notion.com/reference/patch-block-children> |
| 元数据：标题 | 页面 `title` 属性 | 页面在普通页面下时**只有 `title` 一个合法属性** | <https://developers.notion.com/reference/post-page> |
| 元数据：标签 | 数据源（data source）的 `multi_select` 属性 | Notion **无工作区级标签**；标签通过数据库/数据源的 `multi_select` 属性实现，页面须以 `data_source_id` 为父级且属性须匹配数据源 schema | <https://developers.notion.com/reference/post-page>、<https://developers.notion.com/reference/property-object> |
| 归档 / 分类 | 无「文件夹」概念 | 组织方式为**父子页面层级**或**数据源**；`parent` 仅支持 `page_id` / `data_source_id` / `workspace` | <https://developers.notion.com/reference/post-page> |
| 搜索 / 列出 | `POST /v1/search` | 按标题搜索；`filter.property="object"` 可限定 `page` / `data_source`；分页 | <https://developers.notion.com/reference/post-search> |
| 文档间链接 | `link_to_page` 块；`mention`（页面 mention）；行内文本链接 | 链接目标可为 `page_id` / `database_id` / `comment_id` | <https://developers.notion.com/reference/patch-block-children>、<https://developers.notion.com/reference/post-page> |
| 读回文档 | `GET /v1/pages/{page_id}/markdown` | 返回增强 Markdown；`truncated` 表示超限被截断（约 2 万块），未知块以 `<unknown>` 表示 | <https://developers.notion.com/guides/data-apis/working-with-markdown-content> |
| 读回（块） | 检索块子级（block children） | 用于结构化读取 | <https://developers.notion.com/reference/patch-block-children> |
| 版本 / 回退 | — | 公开 API 参考中**未见**页面历史版本 / 回退端点，**未能从一手来源确认** | <https://developers.notion.com/reference/post-page>（API 参考） |

#### 2.1.4 限制

- **速率限制**：每连接（connection）按工作区套餐——Business/Enterprise **600 请求/分钟**，其余套餐 **180 请求/分钟**；另有跨连接共享的每工作区限制；超限返回 `429`（`rate_limited`），带 `Retry-After`；`529` 为服务过载。来源：<https://developers.notion.com/reference/request-limits>
- **体积限制**：单请求负载最多 **1000 个块元素 / 500KB**；`text.content` ≤ 2000 字符；任意块/富文本数组 ≤ 100；relation ≤ 100；URL ≤ 2000 字符。来源：<https://developers.notion.com/reference/request-limits>
- **Markdown 是否原生**：**原生**——创建 / 读取 / 更新均提供 enhanced markdown 端点；但为「Notion 方言」（如 callout 用 `<callout>`、表格用 `<table>`）。来源：<https://developers.notion.com/guides/data-apis/working-with-markdown-content>
- **大文本写入**：`POST /v1/pages` 与 `PATCH .../markdown` 支持 `allow_async: true`，返回 `202` + `async_task` 轮询。来源：<https://developers.notion.com/guides/data-apis/working-with-markdown-content>
- **嵌套文件夹**：无文件夹，天然支持**任意深度父子页面**。来源：<https://developers.notion.com/reference/post-page>
- **付费要求**：API 本身不要求付费；**套餐影响速率上限**（Business/Enterprise 更高）。免费工作区另有块数上限（`workspace-block-limits`）。来源：<https://developers.notion.com/reference/request-limits>

#### 2.1.5 可行性判定

**高**。Markdown 原生直传、读取/更新均有 markdown 端点，纯 `urllib` 即可实现。主要摩擦点：**分类（category）没有文件夹**，需用「每个分类一个父页面」或「一个数据源 + 属性」来映射；**标签只有走数据源 `multi_select`**，会改变页面父级模型（普通页面只能有 title）；无 API 层回退能力。

---

### 2.2 飞书 / Lark

#### 2.2.1 API 是否存在

有公开 API：**飞书开放平台 云文档 docx API**（新版文档，`obj_type=22`）。基址 `https://open.feishu.cn/open-apis/`；国际版 Lark 为 `https://open.larksuite.com/open-apis/`，路径一致。
来源：<https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create>、<https://open.larksuite.com/document/server-docs/docs/docs/docx-v1/document/create.md>

#### 2.2.2 认证

- **`tenant_access_token`（自建应用）**：用 `app_id` + `app_secret` 换取，最长有效期 2 小时。来源：<https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal>
- **`user_access_token`（OAuth，用户身份）**：需走 OAuth 授权码流程，有效约 2 小时、`refresh_token` 约 30 天。来源：<https://open.feishu.cn/document/server-docs/authentication-management/access-token/obtain-oauth-code>、<https://open.feishu.cn/document/server-docs/authentication-management/access-token/get-user-access-token>、<https://open.feishu.cn/document/server-docs/authentication-management/access-token/refresh-user-access-token>
- 请求头：`Authorization: Bearer <access_token>`，`Content-Type: application/json; charset=utf-8`。来源：各 API 文档（如 <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create>）
- **权限（scope）**：按 API 分别申请，例如 `docx:document`、`docx:document:create`、`docx:document:readonly`、`docx:document:write_only`、`docx:document.block:convert`、`drive:drive`、`space:folder:create`、`wiki:node:create`、`wiki:wiki`、`search:docs:read`。来源：各 API 文档（见 §2.2.3 各行来源）
- 应用类型：**自建应用（Custom App）/ 商店应用（Store App）**。来源：<https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create>
- 审批流程：创建应用、开通权限即可调用；**是否需企业管理员审批 / 应用发布审核，未能从一手来源确认**（文档未在同一处说明）。

#### 2.2.3 所需操作对照

| 能力 | 端点 | 说明 | 来源 |
| ---- | ---- | ---- | ---- |
| 创建文档 | `POST /open-apis/docx/v1/documents` | **仅支持标题**，不支持同时创建内容；`folder_token` 指定云空间文件夹；应用频率 3 次/秒 | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create> |
| Markdown → 文档块 | `POST /open-apis/docx/v1/documents/blocks/convert` | **把 Markdown/HTML 内容转换为文档块**（支持标题、有序/无序列表、代码块、引用、分割线、图片、表格等）；需再调「创建嵌套块」插入 | <https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/convert> |
| 插入块（一层） | `POST /open-apis/docx/v1/documents/:document_id/blocks/:block_id/children` | 单请求最多 **50** 个子块；应用 3 次/秒 | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create> |
| 插入块（嵌套） | `POST /open-apis/docx/v1/documents/:document_id/blocks/:block_id/descendant` | 可一次插入**最多 1000** 个块，适合层级结构 / 表格 | <https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-descendant/create> |
| 更新块 | `PATCH /open-apis/docx/v1/documents/:document_id/blocks/:block_id` | 更新指定块；应用 3 次/秒 | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/patch> |
| 批量更新块 | `PATCH /open-apis/docx/v1/documents/:document_id/blocks/batch_update` | 批量更新块内容 | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/batch_update> |
| 元数据：标题 | 文档标题即**根 Page Block 的 `page`（text）字段**，用「更新块」改；Wiki 节点另有标题接口 | docx 标题为页面块内容；Wiki 节点用 `update_title` | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/patch>、<https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/update_title> |
| 元数据：标签 | — | docx / drive 接口中**未见**原生标签 / 标签块，**未能从一手来源确认**存在标签能力 | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create>（块类型列表无标签块） |
| 归档到文件夹 | `POST /open-apis/drive/v1/files/create_folder`（新建）；`GET /open-apis/drive/v1/files`（列出）；`POST /open-apis/drive/v1/files/:file_token/move`（移动） | 云空间文件夹，支持多层；单层节点上限 1500，总节点上限 40 万 | <https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/create_folder>、<https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/list>、<https://open.feishu.cn/document/server-docs/docs/drive-v1/file/move> |
| 归档到知识库 | `POST /open-apis/wiki/v2/spaces/:space_id/nodes` | 在知识空间建节点，`parent_node_token` 实现层级；支持 `obj_type=docx`；100 次/秒 | <https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create> |
| 搜索 / 列出 | `POST /open-apis/suite/docs-api/search/object` | `search_key` 搜索当前用户可见文档；`count` ∈ [0,50]，`offset+count<200`；**需 `user_access_token`** | <https://open.feishu.cn/document/server-docs/docs/drive-v1/search/document-search> |
| 列出文件夹内容 | `GET /open-apis/drive/v1/files` | 支持 `folder_token`、分页、排序 | <https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/list> |
| 文档间链接 | `mention_doc` 文本元素 | `token` + `obj_type`（docx=22）+ `url` + `title`，可 `@文档` | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create> |
| 读回文档（块） | `GET /open-apis/docx/v1/documents/:document_id/blocks` | 分页返回所有块（结构化） | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/list> |
| 读回文档（纯文本） | `GET /open-apis/docx/v1/documents/:document_id/raw_content` | 返回**纯文本**（非 Markdown） | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/raw_content> |
| 读文档基本信息 | `GET /open-apis/docx/v1/documents/:document_id` | 标题、版本号等 | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/get> |
| 版本 / 回退 | — | 云文档有版本概念（`revision_id`），但**未见**公开的「回退到指定版本」API，**未能从一手来源确认** | <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/get> |

#### 2.2.4 限制

- **速率限制**：按 **每个 API × 每个应用 × 每个租户** 计；超限返回 `429`（部分旧接口为 `400`，错误码 `99991400`），响应头 `x-ogw-ratelimit-reset` 给出等待秒数。自建应用分「基础版 / 商业版」有不同档位。来源：<https://open.feishu.cn/document/server-docs/api-call-guide/frequency-control>
- **具体接口频率**：创建文档 3 次/秒；创建块 3 次/秒，且**单文档并发编辑 3 次/秒**（创建块、创建嵌套块、删除块、更新块、批量更新块共享此限）；读取文档块 5 次/秒；`raw_content` 5 次/秒；新建文件夹 5 次/秒 + 10000 次/天；Wiki 建节点 100 次/秒。来源：各 API 文档（见 §2.2.3）
- **Markdown 是否原生**：**非原生**，但提供 **Markdown/HTML → 文档块** 的转换接口；写入流程为「建文档 → convert 得块 → 创建嵌套块插入」，图片需另行上传素材并替换 Image Block。来源：<https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/convert>
- **嵌套文件夹**：云空间文件夹支持多层（单层 1500、总量 40 万）；知识库用 `parent_node_token` 组织层级。来源：<https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/create_folder>、<https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create>
- **文档结构限制**：单文档块数、层级、单元格数等有上限（错误码 `1770004`~`1770013`）。来源：<https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create>
- **付费要求**：**未能从一手来源确认**具体付费门槛；已知速率档位区分基础版 / 商业版自建应用。来源：<https://open.feishu.cn/document/server-docs/api-call-guide/frequency-control>

#### 2.2.5 可行性判定

**中**。能力齐全且无 Markdown 原生限制的硬阻断（有官方 Markdown→块转换），但**接入链路最长**：需注册自建应用、申请多个 scope、维护 token 刷新；写入是「建文档 + convert + 嵌套块插入」三步，读回是块结构或纯文本（**没有 Markdown 导出**）；标题须当页面块更新；**无原生标签**。纯标准库可完成，但代码量与权限配置成本明显高于 Notion。

---

### 2.3 语雀（Yuque）

#### 2.3.1 API 是否存在

有公开 API：**语雀开放 API**。接口域名为 `https://www.yuque.com`；访问空间内资源需使用该空间的子域名。来源：<https://www.yuque.com/yuque/developer/openapi>
私有化 / 自托管版是否提供同一开放 API：**未能从一手来源确认**。

#### 2.3.2 认证

- 所有开放 API 需 Token 验证：在请求头传 **`X-Auth-Token`**。来源：<https://www.yuque.com/yuque/developer/api>
- **个人 Token**：在「个人设置」页获取，依账号权限决定可访问的数据。来源：<https://www.yuque.com/yuque/developer/api>
- **团队 Token**：在「团队设置」页创建，**仅旗舰版空间可用**（需团队管理权限）。来源：<https://www.yuque.com/yuque/developer/api>、<https://www.yuque.com/yuque/developer/gyht993a76zg54mv>
- **访问范围**：自 2022.4.10 起，个人 Token 只能访问其有权限的文档；团队 Token 可读写团队内所有文档。来源：<https://www.yuque.com/yuque/developer/vzippmige58g7r9t>
- OAuth2 授权码等第三方授权方式：**未能从一手来源确认**。

#### 2.3.3 所需操作对照

> 说明：语雀官方「接口列表」以 **OAS（YAML）/ HTML 附件**发布在《语雀开放 API 接口文档》页，**下载需登录语雀账号**，本次未能读取。因此除下表已确认项外，其余端点标 `未能从一手来源确认`。

| 能力 | 端点 / 接口 | 说明 | 来源 |
| ---- | ----------- | ---- | ---- |
| 获取团队知识库列表 | `GET /api/v2/groups/{login}/repos` | 团队 Token 可用 | <https://www.yuque.com/yuque/developer/gyht993a76zg54mv> |
| 获取知识库文档列表 | `GET /api/v2/repos/{book_id}/docs` | 列出某知识库下文档 | <https://www.yuque.com/yuque/developer/gyht993a76zg54mv> |
| 读取文档详情 | `GET /api/v2/repos/{book_id}/docs/{id}` | 重载写法之一 | <https://www.yuque.com/yuque/developer/gyht993a76zg54mv>、<https://www.yuque.com/yuque/developer/openapi> |
| 读取文档详情（路径式） | `GET /api/v2/repos/{group_login}/{book_slug}/docs/{doc_slug}` | 不知道 `book_id` 时按 URL 路径取 | <https://www.yuque.com/yuque/developer/openapi> |
| 创建文档 | 未能从一手来源确认 | 官方接口列表为需登录下载的 OAS 附件 | <https://www.yuque.com/yuque/developer/openapi> |
| 更新文档 | 未能从一手来源确认 | 同上 | <https://www.yuque.com/yuque/developer/openapi> |
| 元数据：标题 / 标签 | 未能从一手来源确认 | 同上；是否存在原生标签能力未知 | <https://www.yuque.com/yuque/developer/openapi> |
| 归档（知识库 / 目录） | 未能从一手来源确认具体端点 | 官方更新记录提到「**批量变更知识库目录**」，说明存在目录相关接口 | <https://www.yuque.com/yuque/developer/openapi> |
| 搜索 / 列出 | 未能从一手来源确认具体端点 | 官方更新记录提到「**搜索 API 的改进**」，说明存在搜索接口 | <https://www.yuque.com/yuque/developer/openapi> |
| 文档间链接 | 未能从一手来源确认 | — | <https://www.yuque.com/yuque/developer/openapi> |
| Markdown 写入 | 未能从一手来源确认 | 官方接口列表不可读；仅能确认编辑器支持 `text/markdown` 数据格式 | <https://www.yuque.com/yuque/developer/ndflcx5eprg7gbdl> |
| 版本 / 回退 | 未能从一手来源确认 | — | <https://www.yuque.com/yuque/developer/openapi> |

#### 2.3.4 限制

- **速率限制**：**每小时最多 5000 次请求，每秒最多 100 次**；响应头 `X-RateLimit-Limit`（总次数限制）与 `X-RateLimit-Remaining`（剩余次数）；**个人或团队下所有 Token 共享同一额度**。来源：<https://www.yuque.com/yuque/developer/openapi>
- **日期时间**：ISO 8601，通常 UTC。来源：<https://www.yuque.com/yuque/developer/openapi>
- **URL 结构**：`https://www.yuque.com/{user_or_group}/{book_slug}/{doc_slug}`；常用字段 `group_login`、`book_slug`、`doc_slug`、`book_id`、`doc_id`。来源：<https://www.yuque.com/yuque/developer/openapi>
- **Markdown 是否原生**：语雀编辑器支持 `text/markdown` 数据格式（`insertAtSelection` / `getNodeContent` 支持 `text/html`、`text/markdown`、`text/plain`、`text/lake`）；但**开放 API 建/改文档是否直接接受 Markdown，未能从一手来源确认**。来源：<https://www.yuque.com/yuque/developer/ndflcx5eprg7gbdl>
- **嵌套文件夹**：语雀组织模型为「知识库（repo）」+「目录（TOC）」，非文件系统文件夹；**TOC 的写入/嵌套端点未能从一手来源确认**。来源：<https://www.yuque.com/yuque/developer/openapi>
- **付费要求**：团队 Token（用于空间内读写）**仅旗舰版空间可用**。来源：<https://www.yuque.com/yuque/developer/gyht993a76zg54mv>

#### 2.3.5 可行性判定

**中（读易写存疑）**。
- **读 / 列表**：已确认端点简单（`X-Auth-Token` 头 + `GET`），纯标准库即可，工作量小。
- **写（创建 / 更新）**：**受阻**——权威接口清单以需登录下载的 OAS 附件发布，无法从一手来源确认端点与参数，故**当前不能给出可实施的写入方案**。需先由有语雀账号者下载该 OAS（或登录后用浏览器查看交互式接口文档）再评估。
- 团队空间写入还要求**旗舰版空间**。

---

## 三、可行性结论对比表

| 维度 | Notion | 飞书 / Lark | 语雀 |
| ---- | ------ | ----------- | ---- |
| 公开 API | ✅ Notion API | ✅ 云文档 docx API | ✅ 语雀开放 API |
| 认证方式 | Bearer（Internal / PAT / OAuth） | tenant_access_token / user_access_token(OAuth) | `X-Auth-Token`（个人 / 团队） |
| 创建文档 | `POST /v1/pages`（**原生 Markdown**） | 建文档 + **convert** + 插块（三步） | 未能从一手来源确认 |
| 更新文档 | `PATCH /v1/pages/{id}/markdown` | 更新块 / 批量更新块 | 未能从一手来源确认 |
| 标题 | 页面 `title` 属性 | 根 Page Block / Wiki `update_title` | 未能从一手来源确认 |
| 标签 | 仅数据源 `multi_select` | 无原生标签（未确认） | 未能从一手来源确认 |
| 分类 / 归档 | 无文件夹，用父子页面 / 数据源 | 云空间文件夹 或 知识空间节点 | 知识库 + 目录（写入未确认） |
| 搜索 / 列表 | `POST /v1/search` | `POST /suite/docs-api/search/object`（需 user token） | 未能从一手来源确认端点 |
| 文档间链接 | `link_to_page` / mention / 行内链接 | `mention_doc` | 未能从一手来源确认 |
| 读回 | `GET .../markdown`（**Markdown**） | 块列表（结构化）或 `raw_content`（**纯文本**） | `GET .../docs/{id}`（已确认） |
| 速率 | 180/min（非商用），600/min（商用） | 3~100 次/秒（按 API），单文档并发 3/秒 | 5000/小时、100/秒，Token 共享 |
| 付费门槛 | API 免费（套餐影响速率） | 未确认 | 团队 Token 需**旗舰版** |
| 主要阻断 | 无文件夹 / 标签需数据源 | 链路长、权限多、无 Markdown 导出 | **写入端点无法从一手来源确认** |
| 标准库可实现 | ✅ | ✅ | 读 ✅ / 写 存疑 |
| 综合可行性 | **高** | **中** | **中（读高、写待确认）** |

---

## 四、实现建议（对 knowledge-distill 的接入方式与优先级）

### 4.1 总体策略：本地为源、云端为镜像（publish/mirror）

不要用云后端替换本地 Markdown。建议保持「**本地 Markdown 是唯一事实源**」：
- 笔记仍先落本地（保留现有的备份、回退、索引、MOC、健康检查）；
- 云存储作为**可选的发布/镜像目标**，单向推送（本地 → 云端），云端不作为回退依据（Notion 无 API 回退、飞书读回非 Markdown、语雀写入未确认）。

这样既不破坏技能既有的「事务化写入 + 备份回退」契约，也避免云端成为新的单点。

### 4.2 建议的后端抽象

在 `skill_tools.py` 中引入一个轻量存储后端接口（内部函数或类），把现有文件系统实现抽为 `local` 后端，云平台各实现一组最小操作：

```
create_doc(title, markdown, category) -> remote_id
update_doc(remote_id, markdown)        -> ok
read_doc(remote_id)                    -> markdown
search_docs(query)                     -> [{title, remote_id, url}]
link_docs(from_id, to_ids)             -> ok      # 可选，能力允许时
```

- **依赖**：脚本现为纯标准库，云端调用用 `urllib.request` + `ssl` + `json` 即可，**无需引入第三方库**（保持零依赖）。
- **配置**：在 `~/.knowledge-distill-config.json` 增加 `backend`（`local`/`notion`/`feishu`/`yuque`）与凭据字段；**Token 一律不进仓库**，建议从环境变量读取，配置只存引用。
- **ID 映射**：把云端 ID 写入笔记 frontmatter（如 `notion_page_id` / `feishu_document_id` / `yuque_slug`），实现「同一篇笔记重复发布 = 更新而非新建」，并让链接可跨端映射。
- **幂等与限流**：按平台限速做退避重试（Notion `Retry-After`；飞书 `x-ogw-ratelimit-reset`；语雀 100/秒）。

### 4.3 各平台的「分类 / 标签 / 链接」映射

| 技能概念 | Notion | 飞书 | 语雀 |
| -------- | ------ | ---- | ---- |
| 分类 | 每个分类一个**父页面**（最简）；或一个**数据源**（可带标签，但页面只能建在数据源下） | 云空间**文件夹**（`folder_token`）；或知识空间节点树 | 知识库（repo）/ 目录（TOC） |
| 标签 | 数据源 `multi_select`；否则写入正文 frontmatter 文本 | 无原生标签 → 写入正文 frontmatter 文本 | 待确认 |
| 互链 | `link_to_page` / mention / 行内链接 | `mention_doc` | 待确认 |

### 4.4 优先级与工作量（纯标准库适配器）

1. **Notion（优先，先做）** — 工作量约 **1~2 人日**。
   - 理由：Markdown 原生直传，创建/读取/更新各一个端点，认证最简单（一个 Bearer Token）；最贴近技能现有 Markdown 模型。
   - 主要工作：建一个父页面作根、每分类建子页面作分类、正文直传 Markdown、frontmatter 存 `notion_page_id`；搜索用 `POST /v1/search`。
   - 注意：标签若要结构化需改用数据源父级，建议**首版把 tags 留在正文**。
2. **飞书 / Lark（次之）** — 工作量约 **3~5 人日**。
   - 理由：需注册自建应用、申请 scope、维护 token；写入是「建文档 → `blocks/convert` → `descendant` 插入」三步；读回为块结构或纯文本，需自行还原 Markdown。
   - 主要工作：token 管理、Markdown→块转换与分片（≤1000/次）、文件夹或知识空间节点映射、`mention_doc` 互链。
3. **语雀（最后，先补调研）** — 读适配器约 **0.5 人日**；**写适配器暂缓**。
   - 理由：读取端点已确认、实现简单；但**创建/更新/搜索端点无法从一手来源确认**。
   - 前置动作：由有语雀账号者登录后下载《语雀开放 API 接口文档》页的 **OAS 附件**（或直接用浏览器查看交互式接口列表），确认写入端点与 Markdown 支持后，再评估是否开发。

### 4.5 与现有设计边界的关系

`references/design-boundaries.md` 的两条边界需说明：
- 「**跨工具兼容（适配多种 Agent 平台）**」针对的是 *Agent 运行平台*，**不覆盖存储后端**，因此接入云笔记不与其冲突；
- 「**外部资料 / 网页接入沉淀**」禁止的是 *把外部网页内容抓进笔记*，而云笔记是 *把已沉淀的笔记发布出去*，方向相反，同样不冲突。
- 但云后端会引入**长期维护成本**（各平台 API 变更、权限、限流）。建议在边界文件中新增一条：云存储后端为**可选、单向、镜像**能力，失败不阻断本地沉淀；并遵循「未确认接口不实现」的护栏。

---

## 五、参考来源汇总

### Notion（官方）
1. Authentication — <https://developers.notion.com/reference/authentication>
2. Create a page — <https://developers.notion.com/reference/post-page>
3. Update page — <https://developers.notion.com/reference/patch-page>
4. Working with markdown content — <https://developers.notion.com/guides/data-apis/working-with-markdown-content>
5. Append block children — <https://developers.notion.com/reference/patch-block-children>
6. Search by title — <https://developers.notion.com/reference/post-search>
7. Request limits — <https://developers.notion.com/reference/request-limits>
8. Property object — <https://developers.notion.com/reference/property-object>
9. Authorization guide — <https://developers.notion.com/guides/get-started/authorization>
10. Capabilities — <https://developers.notion.com/reference/capabilities>

### 飞书 / Lark（官方，均为文档页及其 `.md` 镜像）
1. 创建文档 — <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create>
2. Markdown/HTML 内容转换为文档块 — <https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/convert>
3. 创建块 — <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create>
4. 创建嵌套块 — <https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-descendant/create>
5. 更新块 — <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/patch>
6. 批量更新块 — <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/batch_update>
7. 获取文档基本信息 — <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/get>
8. 获取文档所有块 — <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/list>
9. 获取文档纯文本内容 — <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/raw_content>
10. 新建文件夹 — <https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/create_folder>
11. 获取文件夹中的文件清单 — <https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/list>
12. 移动文件 — <https://open.feishu.cn/document/server-docs/docs/drive-v1/file/move>
13. 创建知识空间节点 — <https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create>
14. 更新知识空间节点标题 — <https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/update_title>
15. 搜索文档 — <https://open.feishu.cn/document/server-docs/docs/drive-v1/search/document-search>
16. 自建应用获取 tenant_access_token — <https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal>
17. 获取 user_access_token（OAuth）— <https://open.feishu.cn/document/server-docs/authentication-management/access-token/obtain-oauth-code>、<https://open.feishu.cn/document/server-docs/authentication-management/access-token/get-user-access-token>、<https://open.feishu.cn/document/server-docs/authentication-management/access-token/refresh-user-access-token>
18. 频控策略 — <https://open.feishu.cn/document/server-docs/api-call-guide/frequency-control>
19. Lark 国际版同名文档 — <https://open.larksuite.com/document/server-docs/docs/docs/docx-v1/document/create>

### 语雀（官方开发者文档）
1. 语雀开放 API 接口文档（含 OAS/HTML 附件下载，需登录）— <https://www.yuque.com/yuque/developer/openapi>
2. Overview（身份认证 / Token）— <https://www.yuque.com/yuque/developer/api>
3. 使用 API 获取空间内文档（团队 Token、接口地址）— <https://www.yuque.com/yuque/developer/gyht993a76zg54mv>
4. 语雀开放 API 访问范围变更 — <https://www.yuque.com/yuque/developer/vzippmige58g7r9t>
5. 命令列表（编辑器支持 `text/markdown` 等数据格式）— <https://www.yuque.com/yuque/developer/ndflcx5eprg7gbdl>
