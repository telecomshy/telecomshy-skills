# 有道云笔记后端 · 使用与书写规范

本文件说明「智识沉淀」以**有道云笔记**作为存储（`format: youdao`）时的行为、书写规范、
依赖与降级。

---

## 1. 定位：有道为唯一存储

- 选择有道后，**笔记正文只存在有道云端**，不再落本地笔记文件。
- 本地只保留**小状态**：技能配置（`~/.knowledge-distill-config.json`）、临时草稿、滚动备份（`~/.knowledge-distill-backups/`）。
- 概念映射：**分类 = 有道文件夹**；`AI笔记` 是笔记根文件夹；**索引 = 有道里的一篇笔记**。

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
- 脚本定位 CLI 的顺序：环境变量 `KNOWLEDGE_DISTILL_YOUDAO_CLI` > 技能自管目录 `~/.knowledge-distill/bin/` > PATH 上的 `youdaonote`。

## 3. 首次配置（自动装 CLI，只卡在 API Key）

1. **自动安装 CLI**——本机没有 `youdaonote` 时由技能自己下载，用户无需手动装：
   - 下载对应平台的官方压缩包，解压出**单文件可执行程序**（Windows 为 `youdaonote.exe`，其余为 `youdaonote`；自带运行时，无需 Node）；
   - 放到技能自管目录 `~/.knowledge-distill/bin/`——脚本会自动优先使用它，**不必改 PATH、也不触发杀软白名单**；
   - 下载 / 解压失败时，再退回引导用户手动安装。
   - 官方下载地址（`…` = `https://artifact.lx.netease.com/download/youdaonote-cli`）：
     - Windows x64：`…/youdaonote-cli-windows-x64.tar.gz`；arm64：`…/youdaonote-cli-windows-arm64.tar.gz`
     - macOS arm64：`…/youdaonote-cli-darwin-arm64.tar.gz`；x64：`…/youdaonote-cli-darwin-x64.tar.gz`
     - Linux x64：`…/youdaonote-cli-linux-x64.tar.gz`；arm64：`…/youdaonote-cli-linux-arm64.tar.gz`
   - 官方未提供校验和；只从上述官方域名下载。
2. **暂停，等用户提供 API Key**（技能无法代申请）：到 `https://mopen.163.com/#/dashboard` 申请，账号需绑定手机号。拿到后由技能配置：`youdaonote config set apiKey <KEY>`，或设环境变量 `YOUDAONOTE_API_KEY`，或写 `~/.youdaonote.json`。
3. `youdao-check` 确认就绪；就绪后 `list-structure "AI笔记"` 查看 / 创建根文件夹。
4. 写入技能配置：`{"format": "youdao", "note_root": "AI笔记"}`。

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
| 标签 tags | ❌ 无原生标签、无 API → 只进正文元信息行 |
| 双链 / 反链 | ❌ 技能不写；桌面端可手工加（反链、图谱可用） |
| 版本回退 | ⚠️ 无版本 API → 靠**本地滚动备份**（写前自动备份，保留最近 10 份）+ 桌面端「历史版本」手工兜底 |
| 全文检索 | ⚠️ 有道搜索只返回标题+id；技能对候选逐篇读回后在本地做片段匹配，**命中范围受有道搜索能力限制** |
| 健康检查 lint | ⚠️ 支持部分：可查 `index_orphans` / `unindexed_notes` / `question_orphans` / `empty_sections`；`stale_index` / `missing_frontmatter` / `orphan_notes` / `broken_links` 有道无对应能力、不检查 |
| 命名查重 | ✅ 按标题匹配（标题不是文件名，不做 Windows 文件名校验） |
| 幂等写入 | ✅ 先按标题查、命中则整体覆盖；`createAnyNote` 是纯新建、不 upsert |

## 6. 注意事项

- **标题必须带 `.md` 后缀**：有道靠**标题后缀**区分笔记类型；缺后缀的条目桌面端会显示
  「该文件暂不支持预览」。脚本写入时会自动补 `.md`（直接调 MCP 工具不会补，必须自行补）。
- **桌面端同步冲突**：桌面端是"本地缓存 + 云同步"。技能从云端改一篇笔记时，若桌面端那篇有
  未同步的本地改动，会触发有道自己的「冲突笔记」。**技能写入前先让桌面端同步完成**，并避免
  与桌面端同时编辑同一篇笔记。
- **限流未公布**：CLI 自身不做退避，技能脚本对瞬时失败做指数退避重试（3 次）；
  健康检查类大批量读取请谨慎。
- **API / CLI 可能变更**：记录并锁定 `youdaonote` CLI 版本。
