---
name: better-seo-workflow
description: SEO 页面内容与工作流优化指南。在生成前端组件、设计页面结构、撰写落地页/灵感广场内容、配置 Title/Meta/JSON-LD 或优化用户交互工作流时使用；也用于产品页、工具页、帮助中心/博客、程序化落地页的 SEO 代码评审。提供 Title/Description/Heading 模板、Schema.org 结构化数据、长尾词融入工作流的 4 大模式、技术性与可读性 Hard Rules、交付前 CheckList，以及可直接运行的 seo_audit.py 自动化审计脚本。
license: MIT
---

# SEO 页面内容与工作流优化指南 (SEO Page & Workflow Optimization)

## 1. 技能定位

**触发场景**：生成前端组件、设计页面结构、撰写落地页/灵感广场内容、配置 Meta 标签、
以及优化用户交互工作流时使用。

**不适用**：纯后端/数据库任务、与页面可见内容无关的构建脚本改造。

## 2. 三大核心原则（所有决策的裁判）

| 原则 | 含义 | 反例 |
| --- | --- | --- |
| **意图契合 Search Intent** | 长尾词不硬塞，必须转化为用户刚需的功能模块或内容载体 | 在 Footer 堆 200 个关键词垃圾链接 |
| **体验优先 UX First** | SEO 元素必须提升交互效率，而不是给用户添堵 | 弹窗要求用户复制提示词 |
| **机器可读 Crawler Friendly** | 关键信息（H1–H3、Alt、Schema.org）可被爬虫无障碍读取 | 文字画在 Canvas / 纯图片里 |

> 判断口径：当一个 SEO 改动无法用「用户会因此更快完成任务」解释时，就不要做。

## 3. 最小可执行规范（写代码时直接照做）

**Title 格式**

```
{主品牌名} ({英文/别名}) - {核心长尾词1} | {核心长尾词2}
图飞 (Dreamifly) - 免费AI绘图与AI生图工具 | 无限制AI图像生成平台
```

**Meta Description**：品牌名 + 痛点解决 + 核心功能 + 强 Action 引导，120–150 字内（中文按字符，英文按字符数 ≤ 160）。

**Heading 语义树**

- `H1`：全页唯一，含品牌词 + 核心定位。
- `H2`：核心功能区 / 场景分类（如「为什么选择图飞 Dreamifly AI 生图？」「热门免费 AI 绘图灵感」）。
- `H3`：二级功能或案例标题。

**结构化数据**：主页与工具页注入 `SoftwareApplication` JSON-LD
（模板见 [`assets/templates/jsonld/software-application.jsonld`](assets/templates/jsonld/software-application.jsonld)）。

**技术 Hard Rules**

1. 展示图优先 `.webp` / `.avif`。
2. 非首屏图片显式 `loading="lazy" decoding="async"`。
3. 必须给显式 `width`/`height` 或 `aspect-ratio`，防 CLS。
4. 禁止把关键文字只渲染进 Canvas/图片；关键词必须存在于 HTML 文本节点。
5. Footer 必须构建 HTML 链接矩阵（品牌词 + 主要功能页 + 长尾分类落地页的 `<a>` 锚文本）。

## 4. 长尾词融入工作流的 4 大模式

| 模式 | 定位 | 关键实现 |
| --- | --- | --- |
| **A 灵感广场与案例详情页** | 用海量 UGC/PGC 覆盖具体提示词与长尾风格 | 卡片 `alt="{品牌名} {长尾词} 生成效果：{Prompt前20字}"`；路由 `/gallery/{style-slug}/{id}`；详情页 Title `"{案例主题}" - {品牌名} {长尾词}提示词与生成效果` |
| **B 快捷提示词与风格预设** | 把搜索词变成「一键填入」的产品功能 | 输入框下方可点击 Pill/卡片，`label` 直接用长尾词，点击填充 Prompt 并同步 URL 参数 |
| **C 动态落地页与参数预设** | 针对高频长尾词生成定向入口页 | `/s/free-anime-generator` 复用主生图 UI，但 H1 替换为长尾标题、默认勾选对应模型/风格、预置范例 Prompt |
| **D 帮助中心与「一键同款」闭环** | 教程引流转化为活跃用户 | `/docs`、`/blog` 以长尾词为标题；Prompt 代码块旁必须有「一键复制并生成」按钮，跳主生图区并带入 Prompt |

实现细节、代码骨架与路由表见 [`reference/03-longtail-workflow-patterns.md`](reference/03-longtail-workflow-patterns.md)。

## 5. Agent 工作流（按顺序执行）

1. **定位页面类型**：首页 / 工具页 / 灵感广场列表 / 案例详情 / 程序化落地页 / 教程博客。
2. **取词**：确定 1 个核心长尾词 + 2–4 个支撑长尾词；每个词必须能映射到一个真实功能或内容载体。
3. **写元数据**：按第 3 节模板产出 Title、Description、H1–H3 语义树、JSON-LD。
4. **模式选型**：至少落地第 4 节中的 1 个模式，并说明该长尾词在 UI 上的载体。
5. **实现**：图片、语义化、Footer 矩阵按 Hard Rules 落地。
6. **自查**：逐项过 [`reference/05-agent-checklist.md`](reference/05-agent-checklist.md)；
   有 HTML / JSX 产物时运行审计脚本拿机器结论：

   ```bash
   python scripts/seo_audit.py <目标文件或目录> -v     # 每项带证据与行号
   python scripts/seo_audit.py <目标> --json           # 输出 JSON，便于接 CI
   ```

   退出码 `0` = 无 FAIL，`1` = 存在 FAIL。脚本已做组件片段（`.tsx/.jsx`）降级，
   在组件文件上不会因为「没有 Title」而产生假失败。
7. **交付说明**：在回复中列出「用到的长尾词 → 对应载体（组件/路由/文案）」的映射表。

## 6. 文件导航

| 文件 | 用途 |
| --- | --- |
| [`reference/02-meta-and-structure.md`](reference/02-meta-and-structure.md) | Title/Description/Heading/JSON-LD 完整规范与多页面变体 |
| [`reference/03-longtail-workflow-patterns.md`](reference/03-longtail-workflow-patterns.md) | 4 大模式的路由、组件与代码骨架 |
| [`reference/04-technical-and-performance.md`](reference/04-technical-and-performance.md) | 性能、语义化、Footer 矩阵、CLS/懒加载细则 |
| [`reference/05-agent-checklist.md`](reference/05-agent-checklist.md) | 提交前 6 项核验 + 常见反模式 |
| [`assets/templates/`](assets/templates) | 可直接复制的 JSON-LD 与 JSX/HTML 片段 |
| [`scripts/seo_audit.py`](scripts/seo_audit.py) | 零依赖 SEO 审计脚本，输出 PASS/WARN/FAIL（支持 `.html/.htm/.jsx/.tsx/.vue/.svelte`） |

## 7. 红线（任一命中即视为交付不合格）

- 一个页面多个 `<h1>`，或 `<h1>` 缺失。
- 关键图片缺 `alt`，或 `alt` 是 `image`、`图片1` 这类无信息量文本。
- 长尾词标签点击后不作用于主工作流（既不填输入框也不带参数跳转）。
- 首屏外图片没做懒加载 / 没写 `width`+`height`。
- 教程、案例页没有指向主生图工具的明确 CTA 链接。
