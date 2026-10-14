<div align="center">

# Better SEO Skill

**SEO 页面内容与工作流优化指南 · 一个可直接安装给 AI Agent 使用的 SEO Skill**

把「搜什么」变成「点什么」—— 让长尾词成为真实的产品功能，而不是页脚里的关键词垃圾。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](scripts/seo_audit.py)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](scripts/seo_audit.py)
[![Tests](https://img.shields.io/badge/tests-passing-success.svg)](tests/run_tests.py)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-purple.svg)](SKILL.md)

[快速开始](#-快速开始) · [安装](#-安装) · [核心内容](#-skill-内容) · [审计脚本](#-自动化审计脚本) · [CheckList](#-交付前-checklist)

</div>

---

## 📖 这是什么

**Better SEO Skill** 是一份写给 AI Agent（Claude Code / DSH / Cursor / 任意支持 Skills 的 Agent）的
**SEO 工程化操作手册 + 可执行审计工具**。

它解决的核心问题：Agent 写页面时最容易犯的两类错误 ——
**① 把关键词硬塞进页面（伤体验、被判作弊）**，
**② 该有的 SEO 结构全漏了（H1 不唯一、图片没 alt、没有结构化数据）**。

本 Skill 用「三大原则 + 四大长尾模式 + 技术 Hard Rules + 机器可查的 CheckList」把这两件事同时管住。

> 判断口径贯穿全篇：**当一个 SEO 改动无法用「用户会因此更快完成任务」解释时，就不要做。**

### 三大核心原则

| 原则 | 含义 | 反例 |
| --- | --- | --- |
| **意图契合 Search Intent** | 长尾词不硬塞，必须转化为用户刚需的功能模块或内容载体 | 在 Footer 堆 200 个关键词垃圾链接 |
| **体验优先 UX First** | SEO 元素必须提升用户的交互效率 | 弹窗要求用户复制提示词 |
| **机器可读 Crawler Friendly** | 关键信息（H1–H3、Alt、Schema.org）可被爬虫无障碍读取 | 文字画在 Canvas / 纯图片里 |

冲突时的优先级：**机器可读 > 体验优先 > 意图契合**。

---

## 🚀 快速开始

### 1. 装给 Agent

```bash
git clone https://github.com/LastLighter/Better-SEO-Skill.git
```

```powershell
# DSH / 通用 skills 目录
Copy-Item -Recurse .\Better-SEO-Skill "$env:USERPROFILE\.dsh\skills\better-seo-workflow"

# Claude Code
Copy-Item -Recurse .\Better-SEO-Skill "$env:USERPROFILE\.claude\skills\better-seo-workflow"
```

```bash
# macOS / Linux
cp -r Better-SEO-Skill ~/.claude/skills/better-seo-workflow
```

目录名建议使用 frontmatter 中的 `name`（`better-seo-workflow`）。
仓库根目录即 Skill 根目录，`SKILL.md` 位于最上层，克隆即可用。

### 2. 让 Agent 干活

直接下达任务即可，例如：

```
用 better-seo-workflow 写一个「二次元 AI 生图」的落地页，
要求覆盖长尾词、带 JSON-LD，并按 CheckList 自查。
```

### 3. 自己跑审计

```bash
python scripts/seo_audit.py ./app            # 扫描目录（递归）
python scripts/seo_audit.py page.html -v     # 单文件 + 每项证据（行号/片段）
python scripts/seo_audit.py ./app --json     # JSON 输出，便于接 CI
python tests/run_tests.py                    # 跑脚本自带回归测试
```

---

## 📦 安装

只要 Agent 能读取 Markdown，就能用这份 Skill。三种方式：

| 方式 | 做法 | 适用 |
| --- | --- | --- |
| **Skill 目录安装**（推荐） | 把整个仓库放到 `~/.dsh/skills/better-seo-workflow/` 或 `~/.claude/skills/better-seo-workflow/` | Claude Code、DSH 等支持 Agent Skills 的环境 |
| **单文件投喂** | 只把 [`SKILL.md`](SKILL.md) 粘进系统提示词 / 项目规则文件 | 任意 LLM，无需目录结构 |
| **项目内规则** | 复制到仓库 `.cursor/rules/`、`CLAUDE.md`、`AGENTS.md` 或 `.github/copilot-instructions.md` | 希望团队内所有 Agent 统一 SEO 规范 |

> 有些 Agent 只识别 `~/.config/<agent>/skills/` 之类的路径，按其文档放置即可 ——
> 本 Skill 不依赖任何专有格式，全部是标准 Markdown + 一个零依赖 Python 脚本。

---

## 🧠 Skill 内容

```
SKILL.md                                    ← 主入口：三大原则 + 最小可执行规范 + 工作流 + 红线
reference/
├── 01-core-principles.md                   ← 原则详解、决策流程、术语表
├── 02-meta-and-structure.md                ← Title / Description / H1-H3 / JSON-LD 规范与各页面变体
├── 03-longtail-workflow-patterns.md        ← 4 大长尾模式的实现细节与代码骨架
├── 04-technical-and-performance.md         ← 图片、懒加载、CLS、语义化、Footer 矩阵、技术项
└── 05-agent-checklist.md                   ← 交付前 6 项核验 + 常见反模式 + 输出模板
assets/templates/
├── head-and-structure.html                 ← 完整 SEO 页面骨架（可跑过审计的正面样例）
├── react-components.tsx                    ← React/Next.js 组件模板（4 大模式全覆盖）
└── jsonld/                                 ← 可复制的结构化数据模板
    ├── software-application.jsonld         ← 工具页SoftwareApplication
    ├── organization-website.jsonld         ← 全站 Organization + WebSite(SearchAction)
    ├── breadcrumb-list.jsonld              ← 面包屑（落地页必备）
    └── howto-article.jsonld                ← 教程 HowTo
scripts/seo_audit.py                        ← 零依赖审计脚本
tests/                                      ← 回归测试 + 反面样例
```

### 最小可执行规范

**Title**

```
{主品牌名} ({英文/别名}) - {核心长尾词1} | {核心长尾词2}

图飞 (Dreamifly) - 免费AI绘图与AI生图工具 | 无限制AI图像生成平台
```

**Meta Description**：品牌名 + 痛点解决 + 核心功能 + 强 Action 引导，120–150 字内。

**Heading 语义树**：`H1` 全页唯一（品牌 + 核心定位）→ `H2` 核心功能区 / 场景分类 → `H3` 二级功能 / 案例标题。

**结构化数据**：主页与工具页注入 `SoftwareApplication` JSON-LD：

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "图飞 (Dreamifly)",
  "operatingSystem": "Web",
  "applicationCategory": "DesignApplication",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.8", "ratingCount": "1024" }
}
```

> ⚠️ `aggregateRating` 必须来自真实评分来源，不得编造，否则可能被撤销整站富文本权限。

### 长尾词融入工作流的 4 大模式

| 模式 | 定位 | 关键实现 |
| --- | --- | --- |
| **A · 灵感广场与案例详情页** | 用海量 UGC/PGC 覆盖具体提示词与长尾风格 | 卡片 `alt="{品牌名} {长尾词} 生成效果：{Prompt前20字}"`；路由 `/gallery/{style-slug}/{id}`；详情页 Title `"{案例主题}" - {品牌名} {长尾词}提示词与生成效果` |
| **B · 快捷提示词与风格预设** | 把搜索词变成「一键填入」的产品功能 | 输入框下方可点击 Pill / 卡片；`label` 直接用长尾词；点击填充 Prompt **并同步 URL 参数** |
| **C · 动态落地页与参数预设** | 针对高频长尾词生成定向入口页 | `/s/free-anime-generator` 复用主生图 UI，但 H1 换成长尾标题、默认勾选模型/风格、预置范例 Prompt |
| **D · 帮助中心与「一键同款」闭环** | 教程引流转化为活跃用户 | `/docs`、`/blog` 以长尾词为标题；Prompt 代码块旁必须有「一键复制并生成」，跳主生图区并带入 Prompt |

```tsx
// 模式 B：标签文本直接采用长尾词，点击后填充 Prompt 并同步更新 URL 参数
const presetTags = [
  { label: "二次元 AI 生图", prompt: "masterpiece, anime girl...", model: "anime-v3" },
  { label: "无限制概念设计", prompt: "sci-fi city, cyberpunk...", model: "concept-xl" },
];
```

### 技术性与可读性 Hard Rules

1. 所有展示图优先 `.webp` / `.avif`。
2. 非首屏图片必须显式 `loading="lazy" decoding="async"`。
3. 必须提供显式 `width`/`height` 或 `aspect-ratio` 防范 CLS。
4. 禁止将文字渲染在 Canvas 或纯图片中而不在 DOM 中保留文本；关键词必须存在于 HTML 文本节点。
5. Footer 必须构建 HTML 链接矩阵（核心品牌词 + 主要功能页 + 长尾分类落地页的 `<a>` 锚文本）。

---

## 🔍 自动化审计脚本

`scripts/seo_audit.py` —— **零第三方依赖**（只用 Python 标准库），
支持 `.html / .htm / .jsx / .tsx / .vue / .svelte`，可递归扫描目录。

```bash
python scripts/seo_audit.py ./app -v                  # 每项输出证据与行号
python scripts/seo_audit.py ./app --json > report.json # 结构化输出
python scripts/seo_audit.py ./app --brand 图飞,Dreamifly
python scripts/seo_audit.py ./app --quiet              # 只看汇总
```

退出码：`0` 无 FAIL ／ `1` 存在 FAIL ／ `2` 路径错误 ／ `3` 未匹配到文件 —— 可直接作为 CI 门禁。

### 检查项

| 检查项 | 级别 | 说明 |
| --- | --- | --- |
| `title` | WARN | Title 存在、长度、品牌词、分隔符 |
| `description` | WARN | 存在、长度区间、Action 引导词 |
| `canonical` | WARN | 自指 canonical（含 Next.js `alternates.canonical` 识别） |
| `open-graph` | WARN | `og:title` / `og:description` / `og:image` |
| `headings` | **FAIL** | H1 缺失或多个 H1、层级跳级、H2 缺失 |
| `json-ld` | **FAIL**/WARN | JSON-LD 存在且 **JSON 可解析**，并列出 `@type` |
| `image-alt` | **FAIL**/WARN | alt 缺失 / 无信息量（`alt="image"`、`alt="图片1"`） |
| `image-dimensions` | WARN | 缺显式 `width`/`height` 或 `aspect-ratio`（CLS 风险） |
| `image-lazy` | WARN | 非首屏图缺 `loading="lazy"` / `decoding="async"` |
| `image-format` | WARN | 展示图非 `webp`/`avif` |
| `canvas-text` | **FAIL** | 有 `<canvas>` 但无等价可读文本（`sr-only`/`figcaption`/`aria`） |
| `cta-link` | **FAIL**/WARN | 是否存在带 `prompt=`/`preset=`/`model=` 参数的 CTA 链接 |
| `internal-links` | WARN | 内链数量（语义集群） |
| `footer-matrix` | WARN | Footer 链接矩阵条数与锚文本质量 |
| `keyword-stuffing` | WARN | 词频异常（关键词堆砌） |

**智能之处**：

- 识别 JSX 动态值（`width={512}`、`loading={cond ? 'eager' : 'lazy'}`），不误报。
- 组件片段（`.tsx`/`.jsx`/`.vue`）自动把整页元数据项标记为 `N/A`，不产生假 FAIL。
- 自动跳过 `.git`、`node_modules`、`.next`、`dist`、`build` 等目录。

### 输出示例

```
==============================================================================
文件：app/page.html
------------------------------------------------------------------------------
  [PASS] title              Title 规范（44 字符，含品牌与分隔符）
  [FAIL] headings           发现 2 个 <h1>，必须唯一
  [FAIL] image-alt          2/3 个 <img> 缺少 alt
  [WARN] image-format       3 张图片非 webp/avif
  [WARN] keyword-stuffing   疑似关键词堆砌：生图×32、免费×12
  → 结论：[FAIL] PASS 9 / WARN 4 / FAIL 2 / N/A 0
==============================================================================
```

### 自检（Dogfooding）

本仓库自己的模板就能跑过自己的审计 —— 这是判断脚本是否误报的最快方式：

```bash
# 扫描仓库内所有页面/组件模板（跳过反面样例与纯 JSON-LD 数据文件）
python scripts/seo_audit.py . --exclude ",.git,tests,jsonld"
```

实际输出：

```
[PASS] assets/templates/head-and-structure.html  (PASS 15 / WARN 0 / FAIL 0 / N/A 0)
[PASS] assets/templates/react-components.tsx     (PASS 7 / WARN 0 / FAIL 0 / N/A 3)
总计：2 个文件 | FAIL 0 · WARN 0 · PASS 22 · N/A 3
整体结论：[PASS]
```

而反面样例会按预期失败：

```bash
python scripts/seo_audit.py tests/fixtures/bad-page.html
# → [FAIL] headings / image-alt / canvas-text ... 整体结论：[FAIL]，退出码 1
```

---

## ✅ 交付前 CheckList

Agent 提交代码或生成页面内容时，逐项核验：

- [ ] **Title & Meta**：是否包含目标品牌词（如 图飞 / dreamifly）与特定长尾词？
- [ ] **H1 唯一性**：当前页面是否且仅有一个 `<h1>` 标签？
- [ ] **图片 Alt 完整度**：所有 `<img>` 或生图结果卡片是否补全了带有上下文关键词的 `alt` 描述？
- [ ] **交互逻辑**：长尾词标签 / 预设点击后是否能直接作用于主工作流（输入框填入或带参数跳转）？
- [ ] **加载速度**：是否已对静态图实施 WebP 化与 Lazy Load？
- [ ] **内链结构**：教程 / 案例页是否包含指向主生图工具的明确 Call-to-Action 链接？

机器可查的 5 项交给脚本，第 4 项（交互逻辑）必须真实点击一遍验证。

### 常见反模式

| 反模式 | 为什么错 | 正确做法 |
| --- | --- | --- |
| 关键词堆在 Footer，锚文本是「关键词1 关键词2」 | 无信息量、被判作弊 | 锚文本用可读长尾短语，链接指向真实页面 |
| 首页有 3 个 `<h1>` | 稀释主题 | 主标题留 `<h1>`，其余降级 |
| 生图结果用 `<div style="background-image">` | 爬虫读不到图片语义 | 用 `<img>` + `alt` + 显式宽高 |
| 长尾词标签只是装饰文字 | 关键词无产品价值 | 点击填充 Prompt + 同步 URL |
| 程序化落地页仅换 Title、正文相同 | doorway page，风险高 | 至少 3 处真实差异化 |
| 图片 `alt="image"` / `alt="1"` | 零信息量 | `alt="{品牌} {长尾词} 生成效果：{摘要}"` |
| 首屏 LCP 大图加 `loading="lazy"` | 拖慢 LCP | 改用 `fetchpriority="high"` + preload |
| JSON-LD 用 `useEffect` 注入 | 爬虫可能看不到 | 服务端渲染输出 |

完整版见 [`reference/05-agent-checklist.md`](reference/05-agent-checklist.md)。

---

## 🗂 目录结构

```
Better-SEO-Skill/
├── SKILL.md                  # Agent Skill 入口（带 YAML frontmatter）
├── README.md
├── LICENSE                   # MIT
├── reference/                # 5 份规范文档
├── assets/templates/         # 可复制的 JSON-LD / HTML / React 模板
├── scripts/seo_audit.py      # 零依赖审计脚本
└── tests/                    # 回归测试 + 反面样例
```

---

## 🛠 自定义

- **换品牌**：把模板与示例中的 `图飞 (Dreamifly)` 替换成你的品牌，并同步更新
  `scripts/seo_audit.py` 中的 `DEFAULT_BRAND`（或用 `--brand` 参数传入）。
- **扩检查项**：在 `scripts/seo_audit.py` 中新增 `check_xxx(html, rep, verbose)` 函数，
  并在 `audit_text()` 里调用即可，`CheckResult` 会自动进入汇总与 JSON 输出。
- **调长度阈值**：`--min-desc` / `--max-desc`；Title 阈值在 `_judge_title()` 中。
- **多语言站点**：把中文长尾词替换为对应语种，CTA 引导词表 `CTA_HINTS` 同步扩充。

---

## 🤝 贡献

欢迎提 Issue / PR：新增检查项、补充落地页模式、翻译 README。
提交前请确保：

```bash
python tests/run_tests.py    # 全部通过
```

---

## 📄 License

[MIT](LICENSE) © [LastLighter](https://github.com/LastLighter)

---

<div align="center">

**如果这份 Skill 帮你省下了改 SEO 的时间，欢迎点个 ⭐ Star**

</div>
