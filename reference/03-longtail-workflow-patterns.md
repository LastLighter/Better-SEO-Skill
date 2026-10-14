# 03 · 长尾词无缝融入工作流的 4 大模式

Agent 在设计或实现 UI 组件时，必须优先采用以下模式覆盖长尾词。
**判据**：任何一个长尾词，都必须能在下表中找到自己的「载体」。

---

## 模式 A：灵感广场与案例详情页（Gallery & Showcase）

**定位**：用海量 UGC/PGC 内容覆盖具体提示词与长尾风格。

### 实现逻辑

1. **列表页卡片 alt 带长尾词**

   ```
   alt="{品牌名} {长尾词} 生成效果：{Prompt前20字}"
   ```

   ```tsx
   <img
     src={item.webp}
     alt={`图飞 ${item.styleKeyword} 生成效果：${item.prompt.slice(0, 20)}`}
     width={512}
     height={512}
     loading="lazy"
     decoding="async"
   />
   ```

2. **详情页语义化 URL**

   ```
   /gallery/{style-slug}/{id}
   /gallery/anime-ai-generator/12345
   ```

   slug 表必须由「长尾词 → slug」映射集中维护，禁止随机 ID 或纯数字路由。

   ```ts
   // lib/style-slugs.ts
   export const STYLE_SLUGS = {
     "anime-ai-generator":     { keyword: "二次元 AI 生图", model: "anime-v3" },
     "unlimited-concept-art":  { keyword: "无限制概念设计", model: "concept-xl" },
     "free-sticker-generator": { keyword: "免费 AI 贴图生成", model: "sticker-v2" },
   } as const;
   ```

3. **详情页 Title 模板**

   ```
   "{案例主题}" - {品牌名} {长尾词}提示词与生成效果
   ```

### 页面内必须出现的模块

- 案例大图（带 `alt`、显式宽高）
- 完整 Prompt 文本（在 DOM 文本节点中，可被爬虫读取）
- 「一键同款」按钮 → 跳转主生图区并带入 Prompt 与参数
- 同风格案例列表（内链，形成语义集群）
- 返回该风格落地页的链接（`/s/{style-slug}`）

---

## 模式 B：快捷提示词与风格预设（Style Presets & Quick Prompts）

**定位**：将搜索词转化为「一键填入」的产品功能。

### UI 展现

输入框下方的可点击 Pill 标签或卡片，首屏可见、无需 hover 展开。

### 代码与交互规范

```tsx
// 标签文本直接采用长尾词，点击后填充 Prompt 并同步更新 URL 参数
const presetTags = [
  { label: "二次元 AI 生图", prompt: "masterpiece, anime girl...", model: "anime-v3" },
  { label: "无限制概念设计", prompt: "sci-fi city, cyberpunk...", model: "concept-xl" },
];

function PresetPills({ onApply }: { onApply: (t: typeof presetTags[number]) => void }) {
  return (
    <ul className="flex gap-2">
      {presetTags.map((tag) => (
        <li key={tag.label}>
          <button
            type="button"
            onClick={() => {
              onApply(tag);                       // 1. 填充 Prompt 到主工作流
              const url = new URL(window.location.href);
              url.searchParams.set("preset", tag.label); // 2. 同步 URL 参数，可被分享/收录
              url.searchParams.set("model", tag.model);
              window.history.replaceState(null, "", url);
            }}
          >
            {tag.label}
          </button>
        </li>
      ))}
    </ul>
  );
}
```

### 硬性约束

- 点击必须**直接作用于主工作流**：填输入框 + 选模型，或带参数跳转到工具页。只改 URL 不填 Prompt 视为不合格。
- Pill 的可见文本就是长尾词本身，不要用「风格1 / 风格2」这类无语义词。
- 标签应服务端可渲染（或在无 JS 时降级为带参数的 `<a href="/?preset=...">`），保证爬虫能读到关键词文本。
- 支持的标签数量做成可配置数据源，方便运营按搜索量增删。

---

## 模式 C：动态落地页与参数预设（Programmatic Landing Pages）

**定位**：针对高频长尾词（如「免费 AI 贴图生成」）生成定向入口页。

### 页面逻辑

访问 URL（如 `/s/free-anime-generator`）时，渲染主生图 UI，但做差异化：

| 差异化项 | 规则 |
| --- | --- |
| H1 | 自动替换为长尾标题，如 `免费 AI 贴图生成 · 图飞 Dreamifly` |
| 描述段 | 150 字以内，说明该长尾词场景能做什么 |
| 工作流参数 | 默认勾选对应模型 / 风格（`model`、`style`、`aspectRatio`） |
| 输入框 | 预置范例 Prompt |
| 示例区 | 3–6 张该风格样例图（带长尾词 alt） |
| Breadcrumb | `首页 > AI 生图 > {长尾词}`，并输出 `BreadcrumbList` JSON-LD |
| CTA | 主按钮文案与该长尾词一致（「免费生成贴图」） |

### 实现骨架

```tsx
// app/s/[slug]/page.tsx
export function generateStaticParams() {
  return Object.keys(STYLE_SLUGS).map((slug) => ({ slug }));
}

export default function LandingPage({ params }: { params: { slug: string } }) {
  const cfg = STYLE_SLUGS[params.slug];
  if (!cfg) notFound();
  return (
    <>
      <h1>{cfg.keyword} · 图飞 Dreamifly</h1>
      <Generator
        defaultModel={cfg.model}
        defaultPrompt={cfg.samplePrompt}
        syncUrlParams
      />
    </>
  );
}
```

### 硬性约束

- 每个落地页必须有**真实差异化内容**（H1、描述、示例图、默认参数至少 3 项不同），否则视为 doorway page，会被判垃圾内容。
- 落地页之间以及与 `/gallery` 之间必须互相内链，形成语义集群，而不是孤立页面。
- 页面必须可被 SSR/SSG 渲染出完整 HTML 文本，不要只返回一个空壳 SPA 容器。

---

## 模式 D：帮助中心与「一键同款」闭环（Help Center to App Linkage）

**定位**：教程内容引流并转化为活跃用户。

### 规范

1. 在 `/docs` 或 `/blog` 撰写以长尾词为标题的指南，如《如何实现无限制 AI 生图？》。
2. 文章内部 Prompt 代码块旁**必须**包含「一键复制并生成」按钮：

```tsx
<PromptBlock
  prompt={docPrompt}
  ctaHref={`/?prompt=${encodeURIComponent(docPrompt)}&model=${docModel}`}
  ctaLabel="一键复制并生成"
/>
```

3. 点击行为：复制到剪贴板 → 跳转主生图区 → 自动带入 Prompt 与参数（读取 URL 参数并初始化工作流）。
4. 文章底部必须有明确的 Call-to-Action 链接回到主工具，例如：
   `👉 立即用图飞 Dreamifly 免费生成同款作品`。
5. 教程内文首段就要出现长尾词与品牌名，并给出「本文能帮你做出什么」的一句话结论。
6. 文章输出 `HowTo` 或 `Article` JSON-LD，`step[]` 与正文步骤一一对应。

### 闭环检查

```
搜索结果 → 教程页 → 一键复制并生成 → 主生图页（Prompt/参数已带入）→ 出图 → 灵感广场沉淀
```

任何一环断开（例如按钮只是复制、不跳转，或跳转后 Prompt 丢失），该模式即视为未实现。

---

## 模式选型速查

| 场景 | 首选模式 | 组合建议 |
| --- | --- | --- |
| 冷启动、没有内容存量 | B | B + C（预设标签直接做成落地页入口） |
| 已有用户作品沉淀 | A | A + B（案例详情内嵌同款按钮） |
| 有明确高搜索量长尾词 | C | C + D（落地页配一篇指南互链） |
| 需要长期内容增长 | D | D + A（教程引用案例图） |
