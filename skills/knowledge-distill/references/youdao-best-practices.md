# 有道云笔记后端 · 使用与书写规范

本文件说明「智识沉淀」以**有道云笔记**作为存储（`format: youdao`）时的行为、书写规范、
依赖与降级。设计背景见仓库 `docs/智识沉淀-有道存储实现方案.md`。

---

## 1. 定位：有道为唯一存储

- 选择有道后，**笔记正文只存在有道云端**，不再落本地笔记文件。
- 本地只保留**小状态**：技能配置（`~/.knowledge-distill-config.json`）、临时草稿、滚动备份（`~/.knowledge-distill-backups/`）。
- 概念映射：**分类 = 有道文件夹**；`AI笔记` 是笔记根文件夹；**索引 / MOC = 有道里的一篇笔记**。

## 2. 依赖：官方 `youdaonote` CLI

技能通过官方 CLI 的**云端 MCP 接口**读写（不是网页端、也不是桌面端的本地缓存）：

```bash
youdaonote call listNotes          --args '{"parentId":"0"}'
youdaonote call searchNotes        --args '{"keyword":"...","startIndex":0}'
youdaonote call getNoteTextContent --args '{"fileId":"..."}'
youdaonote call createAnyNote      --args '{"title":"...","type":"md","content":"...","parentId":"..."}'
youdaonote call updateMarkdownNote --args '{"fileId":"...","title":"...","content":"..."}'
youdaonote call createDir          --args '{"parentId":"0","dirName":"..."}'
```

- **认证由 CLI 负责**：API Key 存 `~/.youdaonote.json`，或用环境变量 `YOUDAONOTE_API_KEY`；
  技能**不读取、不存储** Key。
- 就绪自检：`python "<SKILL_DIR>/scripts/skill_tools.py" youdao-check`（内部调用 `youdaonote check --json`）。
- 脚本调用 CLI 时可用环境变量 `KNOWLEDGE_DISTILL_YOUDAO_CLI` 指定可执行文件（默认 `youdaonote`）。

## 3. 首次配置（引导为主）

1. 安装 `youdaonote` CLI（官方下载包；涉及 PATH / 杀软，需用户自行完成）。
2. 到 `mopen.163.com` 申请 API Key（**绑定手机号账号，技能无法代申请**）。
3. 配置认证：`youdaonote config set apiKey`（或设 `YOUDAONOTE_API_KEY`）。
4. 运行 `youdao-check` 确认就绪；就绪后 `list-structure "AI笔记"` 查看/创建根文件夹。
5. 写入技能配置：`{"format": "youdao", "note_root": "AI笔记"}`。

## 4. 内容模型（写入有道的笔记长什么样）

写入内容为**标准 Markdown**（有道原生支持），但**没有 frontmatter**：

- **顶部一行元信息**（替代 Obsidian 的 frontmatter）：
  `> 创建：YYYY-MM-DD ｜ 来源：对话 ｜ 标签：a、b`
- **callout 用有道高亮块**（桌面端 7.1.8+ 渲染）：
  `::: success` / `::: info` / `::: warning` / `::: danger`（绿 / 蓝 / 黄 / 红），以 `:::` 收尾。
- **笔记间链接用纯文本标题**：云端不支持 `[[wikilinks]]`，CLI 也给不出笔记 URL，
  所以「相关笔记」「索引」里的链接是**不可点击的纯文本**；可点双链请在桌面端手工补。
- 其余照标准 Markdown：标题层级、列表、代码块、引用、表格、待办 `- [ ]`、KaTeX 公式、Mermaid。
- 事实 / 推断标注（`(推断)` / `(待核实)`）、易变事实加日期等既有规则**不变**。

## 5. 能力对照与降级（相对本地 Obsidian / Markdown）

标 ⚠️/❌ 的为**降级**（相对本地缺失或变弱）。

| 能力 | 有道表现 |
| ---- | -------- |
| 原生 Markdown | ✅ |
| 分类 / 索引 | ✅（文件夹 + 笔记） |
| 内容地图 MOC | ❌ 暂不支持（v2） |
| 标签 tags | ❌ 无原生标签、无 API → 只进正文元信息行 |
| 双链 / 反链 | ❌ 技能不写；桌面端可手工加（反链、图谱可用） |
| 版本回退 | ⚠️ 无版本 API → 靠**本地滚动备份**（写前自动备份，保留最近 10 份）+ 桌面端「历史版本」手工兜底 |
| 全文检索 | ⚠️ 有道搜索只返回标题+id；技能对候选逐篇读回后在本地做片段匹配，**命中范围受有道搜索能力限制** |
| 健康检查 lint | ❌ 暂不支持（v2）：无时间戳做不了 `stale_index`，无 frontmatter / 反链 |
| 命名查重 | ✅ 按标题匹配（标题不是文件名，不做 Windows 文件名校验） |
| 幂等写入 | ✅ 先按标题查、命中则整体覆盖；`createAnyNote` 是纯新建、不 upsert |

## 6. 注意事项

- **桌面端同步冲突**：桌面端是"本地缓存 + 云同步"。技能从云端改一篇笔记时，若桌面端那篇有
  未同步的本地改动，会触发有道自己的「冲突笔记」。**技能写入前先让桌面端同步完成**，并避免
  与桌面端同时编辑同一篇笔记。
- **限流未公布**：CLI 自身不做退避，技能脚本对瞬时失败做指数退避重试（3 次）；
  健康检查类大批量读取请谨慎。
- **API / CLI 可能变更**：记录并锁定 `youdaonote` CLI 版本。
