# 05 · Agent 自动化 CheckList（代码 review & 内容生成核验）

在 Agent 提交代码或生成页面内容时，需执行以下逐项检查。
**全部 6 项通过才算交付完成**；有 HTML/JSX 产物时，先跑 `python scripts/seo_audit.py <path>` 拿到机器结论，再做人工判断项。

---

## 交付前 6 项核验

### [ ] 1. Title & Meta

- 是否包含目标品牌词（如 图飞 / Dreamifly）与特定长尾词？
- Title 格式是否为 `{品牌} ({英文}) - {长尾词1} | {长尾词2}`？
- Description 是否落在 120–150 字，且结尾有 Action 引导？
- 是否有 `canonical`、`og:title`、`og:description`、`og:image`？

**机器可查**：`seo_audit.py` 的 `title / description / canonical / open-graph` 项。

### [ ] 2. H1 唯一性

- 当前页面是否**且仅有一个** `<h1>` 标签？
- H1 是否包含品牌词 + 核心定位？
- 层级是否连续（不出现 `H1 → H3` 跳级）？

**机器可查**：`seo_audit.py` 的 `headings` 项。

### [ ] 3. 图片 Alt 完整度

- 所有 `<img>` 或生图结果卡片是否补全了带有上下文关键词的 `alt` 描述？
- `alt` 是否包含「品牌 + 长尾词 + 内容摘要」，而不是 `image`、`图片1`、`生成结果`？
- 装饰性图片是否显式 `alt=""`（而不是缺省属性）？

**机器可查**：`seo_audit.py` 的 `image-alt` 项。

### [ ] 4. 交互逻辑

- 长尾词标签 / 预设点击后是否能**直接作用于主工作流**（输入框填入或带参数跳转）？
- 参数是否同步到 URL（可分享、可被收录）？
- 从教程页点「一键复制并生成」后，跳转的目标页是否真的读到了 `?prompt=` 参数并初始化工作流？

**人工验证**：跑一遍真实点击路径；这是唯一不能靠静态扫描确认的一项。

### [ ] 5. 加载速度

- 是否已对静态图实施 WebP/AVIF 化与 Lazy Load？
- 非首屏图片是否带 `loading="lazy" decoding="async"`？
- 所有图片是否有 `width`/`height` 或 `aspect-ratio`？

**机器可查**：`seo_audit.py` 的 `image-format / image-lazy / image-dimensions` 项。

### [ ] 6. 内链结构

- 教程 / 案例页是否包含指向主生图工具的明确 Call-to-Action 链接？
- 是否至少有一条指向相关落地页或灵感广场的内链？
- 语义化 URL 是否与 Footer 矩阵、sitemap 一致？

**机器可查**：`seo_audit.py` 的 `cta-link / internal-links` 项。

---

## 附加核验（结构性数据与内容质量）

- [ ] JSON-LD 是否为服务端输出的 `<script type="application/ld+json">`，且 JSON 可解析？
- [ ] `aggregateRating` 等富文本字段是否有真实数据来源（不得编造）？
- [ ] 关键文本是否存在于 DOM 文本节点（不是 Canvas / 图片 / CSS 背景）？
- [ ] 程序化落地页之间是否至少有 3 处真实差异化？
- [ ] Footer 锚文本是否为长尾词本身而非「更多」？
- [ ] 同一站点内 Title / Description 是否无重复？

---

## 常见反模式（命中即打回）

| 反模式 | 为什么错 | 正确做法 |
| --- | --- | --- |
| 关键词堆在 Footer，锚文本是「关键词1 关键词2 关键词3」 | 无信息量、被判作弊 | 锚文本用可读长尾短语，链接指向真实页面 |
| 首页有 3 个 `<h1>`（Logo + 主标题 + 副标题） | 稀释主题 | 主标题留 `<h1>`，其余降级为 `<p>`/`<h2>` |
| 生图结果用 `<div style="background-image">` | 爬虫读不到图片语义 | 用 `<img>` + `alt` + 显式宽高 |
| 长尾词标签只是装饰文字 | 关键词无产品价值 | 点击填充 Prompt + 同步 URL |
| 程序化落地页仅换 Title、正文相同 | doorway page，风险高 | 至少 3 处差异化内容 |
| 图片 `alt="image"` / `alt="1"` | 零信息量 | `alt="{品牌} {长尾词} 生成效果：{摘要}"` |
| 首屏 LCP 大图加 `loading="lazy"` | 拖慢 LCP | 改用 `fetchpriority="high"` + preload |
| 用 robots.txt 屏蔽带参数页 | 连带屏蔽干净 URL | 用 `noindex` + canonical 指向干净 URL |
| JSON-LD 用 `useEffect` 注入 | 爬虫可能看不到 | 服务端渲染输出 |

---

## 核验输出模板（Agent 交付时附上）

```markdown
### SEO 自查结果

| 项 | 结论 | 证据 |
| --- | --- | --- |
| Title & Meta | PASS | `app/page.tsx:12` title=「图飞 (Dreamifly) - 免费AI绘图…」 |
| H1 唯一性 | PASS | 全页 1 个 h1：`<h1>图飞 Dreamifly · 免费无限制 AI 生图</h1>` |
| 图片 Alt | PASS | 24 张卡片，alt 均含「图飞 + 风格词 + Prompt 摘要」 |
| 交互逻辑 | PASS | `PresetPills` 点击后 fill(prompt) + `history.replaceState(?preset=)` |
| 加载速度 | WARN | 2 张老素材仍是 .png，已记录 TODO 待转 WebP |
| 内链结构 | PASS | 案例页 → `/` 的「一键同款」CTA 存在 |

长尾词 → 载体映射：
- 二次元 AI 生图 → PresetPills 标签 + /s/free-anime-generator 落地页
- 无限制概念设计 → 案例详情页 Title + gallery/anime-ai-generator 列表
```

机器扫描命令：

```bash
python scripts/seo_audit.py app/            # 扫描目录
python scripts/seo_audit.py page.html -v    # 单文件 + 详细输出
python scripts/seo_audit.py app/ --json     # 输出 JSON，便于 CI 集成
```
