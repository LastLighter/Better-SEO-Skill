# 02 · 页面元数据与结构规范（Meta & Structural HTML）

Agent 在生成 HTML 或 Next.js / React 页面 Header 时，必须遵循本文件模板与逻辑。

---

## 1. Title

### 1.1 标准格式

```
{主品牌名} ({英文/别名}) - {核心长尾词1} | {核心长尾词2}
```

示例：

```
图飞 (Dreamifly) - 免费AI绘图与AI生图工具 | 无限制AI图像生成平台
```

### 1.2 各页面类型变体

| 页面类型 | Title 模板 | 示例 |
| --- | --- | --- |
| 首页 / 主应用页 | `{品牌} ({英文}) - {长尾词1} \| {长尾词2}` | 图飞 (Dreamifly) - 免费AI绘图与AI生图工具 \| 无限制AI图像生成平台 |
| 工具页 | `{工具名} - {品牌} {长尾词}` | AI 生图工具 - 图飞 Dreamifly 免费无限制出图 |
| 灵感广场列表 | `{风格/主题}灵感广场 - {品牌} {长尾词}案例库` | 二次元灵感广场 - 图飞 二次元AI生图案例库 |
| 案例详情页 | `"{案例主题}" - {品牌} {长尾词}提示词与生成效果` | "赛博朋克夜城" - 图飞 无限制概念设计提示词与生成效果 |
| 程序化落地页 | `{长尾词标题} - 免费在线{品类} \| {品牌}` | 免费AI贴图生成 - 免费在线出图 \| 图飞 Dreamifly |
| 教程 / 博客 | `如何实现{长尾词}？{品牌}{品类}完整指南` | 如何实现无限制AI生图？图飞 Dreamifly 完整指南 |

### 1.3 硬性约束

- 长度：中文 ≤ 30 全角字符（含符号），英文 ≤ 60 字符；超长会被 SERP 截断。
- 品牌词必须出现一次，且尽量靠前（首页/主应用页以品牌开头）。
- 不用竖线 `|` 以外的分隔符堆叠；分隔符只用于区分「品牌段」与「关键词段」。
- 同一站点内 Title 不可重复；程序化落地页必须把长尾词注入模板，避免批量页面产出相同 Title。

---

## 2. Meta Description

### 2.1 结构公式

```
{品牌名} + {痛点解决} + {核心功能} + {强 Action 引导}
```

示例：

```html
<meta name="description"
      content="图飞 (Dreamifly) 提供免费无限制 AI 绘图与 AI 生图，输入中文提示词即可一键生成二次元、摄影、概念设计作品。无需安装，立即免费开画出图。" />
```

### 2.2 硬性约束

- 长度：中文 120–150 字（按字符数计），英文 ≤ 160 字符。
- 必须包含品牌名与目标长尾词的自然变体（不必逐字堆叠）。
- 结尾必须是动作引导：`立即免费开画` / `马上体验` / `一键生成`，不要以句号平淡收尾后再无 CTA。
- 不得与页面上任何其他页面共用同一段 Description。

---

## 3. Heading 语义树（H1–H3）

```
H1（全页唯一，品牌词 + 核心定位）
├── H2 为什么选择 {品牌} AI 生图？        ← 信任/差异化区
│   ├── H3 中文提示词直出
│   └── H3 无限制免费出图
├── H2 热门免费 AI 绘图灵感                ← UGC/PGC 内容区
│   ├── H3 二次元 AI 生图
│   └── H3 无限制概念设计
└── H2 常见问题 FAQ                        ← 长尾问句区
```

规则：

1. **H1 全页唯一**。若布局使用 Logo 作为标题，应把 Logo 包在 `<h1>` 中并同时带上品牌全称的可读文本，而不是额外再造一个 `<h1>`。
2. 不跳级：`H1 → H2 → H3`；卡片标题若语义上是列表项且无层级意义，用 `<h3>` 或直接是分组内的 `<strong>` 也可以，但同一层级的并列项需一致。
3. H2 承载「功能区 / 场景分类」，H3 承载「二级功能 / 案例标题」。
4. 每个 H2 区块至少包含一个可交互元素或一段可独立被摘录的自足文本，避免空壳标题。

---

## 4. 结构化数据（Schema.org JSON-LD）

### 4.1 主页 / 工具页：`SoftwareApplication`

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "图飞 (Dreamifly)",
  "operatingSystem": "Web",
  "applicationCategory": "DesignApplication",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "1024"
  }
}
```

### 4.2 其他页面类型

| 页面 | 类型 | 必要字段 |
| --- | --- | --- |
| 案例详情页 | `CreativeWork` / `ImageObject` | `name`、`description`、`image`、`creator`、`datePublished` |
| 灵感广场列表 | `CollectionPage` + `ItemList` | `itemListElement[].url`、`position` |
| 程序化落地页 | `WebPage` + `BreadcrumbList` | `breadcrumb`、`primaryImageOfPage` |
| 教程 / 博客 | `HowTo` 或 `Article` | `headline`、`step[]`（HowTo）、`datePublished`、`author` |
| 全站 | `Organization` + `WebSite`（含 `SearchAction`） | `name`、`url`、`logo` |

### 4.3 硬性约束

- 只声明**页面上真实存在且用户可见**的数据。示例中的 `aggregateRating` 必须来自真实评分来源，
  否则属于富文本违规，可能导致整站富文本权限被撤销。
- `ratingValue` 必须是字符串或数字且与页面展示一致；`ratingCount` 为整数。
- JSON-LD 用 `<script type="application/ld+json">` 内联在 `<head>` 或页面底部，不要用 JS 动态注入后再指望爬虫执行。
- 一个页面可以放多个 JSON-LD 块，或用 `@graph` 合并。

---

## 5. Next.js / React 落地写法

### 5.1 App Router（Next.js 13+）

```tsx
// app/gallery/[style]/[id]/page.tsx
import type { Metadata } from "next";

export async function generateMetadata({ params }): Promise<Metadata> {
  const item = await getGalleryItem(params.style, params.id);
  const longTail = styleSlugToKeyword(params.style); // "anime-ai-generator" -> "二次元 AI 生图"
  const title = `"${item.title}" - 图飞 ${longTail}提示词与生成效果`;
  return {
    title,
    description: `${item.title} 由图飞 Dreamifly 免费 AI 生图生成，附完整提示词与参数，点击一键同款立即出图。`,
    alternates: { canonical: `/gallery/${params.style}/${params.id}` },
    openGraph: { title, images: [item.image], type: "article" },
  };
}
```

### 5.2 结构化数据组件

```tsx
export function SoftwareApplicationJsonLd(props: {
  name: string; ratingValue: string; ratingCount: number;
}) {
  const data = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: props.name,
    operatingSystem: "Web",
    applicationCategory: "DesignApplication",
    offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
    aggregateRating: {
      "@type": "AggregateRating",
      ratingValue: props.ratingValue,
      ratingCount: props.ratingCount,
    },
  };
  return (
    <script
      type="application/ld+json"
      // 服务端渲染输出，避免依赖客户端 JS 执行
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
```

### 5.3 纯 HTML `<head>` 骨架

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>图飞 (Dreamifly) - 免费AI绘图与AI生图工具 | 无限制AI图像生成平台</title>
  <meta name="description" content="..." />
  <link rel="canonical" href="https://example.com/" />
  <meta property="og:title" content="..." />
  <meta property="og:description" content="..." />
  <meta property="og:image" content="https://example.com/og.webp" />
  <script type="application/ld+json">{ /* SoftwareApplication */ }</script>
</head>
<body>
  <h1>图飞 Dreamifly · 免费无限制 AI 生图</h1>
  <!-- ... -->
</body>
</html>
```

> 完整可复制片段见 [`../assets/templates/`](../assets/templates)。
