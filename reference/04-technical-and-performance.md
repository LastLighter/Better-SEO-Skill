# 04 · 技术性与可读性优化（Technical & Performance Rules）

Agent 在优化代码或构建资源时需满足以下 **Hard Rules**。这些不是建议，是交付门槛。

---

## 1. 图片资源加载策略

### 1.1 格式

- 所有展示图优先采用 `.webp` 或 `.avif`。
- 保留原始格式（PNG/JPG）作为 `<picture>` 的回退源，或用 `<img srcset>` 提供多尺寸。
- 生成类产品（生图结果）应在服务端出图时同步产出 WebP 版本，而不是依赖浏览器端转换。

```html
<picture>
  <source srcset="/gallery/anime-12345.avif" type="image/avif" />
  <source srcset="/gallery/anime-12345.webp" type="image/webp" />
  <img
    src="/gallery/anime-12345.jpg"
    alt="图飞 二次元 AI 生图 生成效果：masterpiece, anime girl in rain"
    width="512" height="512"
    loading="lazy" decoding="async"
  />
</picture>
```

### 1.2 懒加载

- **非首屏图片必须显式添加** `loading="lazy"` 与 `decoding="async"`。
- 首屏主视觉（LCP 元素）**不要**加 `lazy`；应加 `fetchpriority="high"` 并配合 `preload`：

```html
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high" />
<img src="/hero.webp" alt="..." width="1200" height="630" fetchpriority="high" decoding="async" />
```

- 无限滚动列表要配合占位骨架与固定尺寸，避免滚动时布局跳动。

### 1.3 防范布局偏移（CLS）

- 必须包含显式 `width` 与 `height` **或** CSS `aspect-ratio`。

```css
.gallery-card__media { aspect-ratio: 1 / 1; width: 100%; height: auto; }
```

```html
<img src="/x.webp" alt="..." width="512" height="512" loading="lazy" decoding="async" />
```

- 图片容器禁止在图片加载完成后改变尺寸（不要用 JS 在 `onload` 里设置宽高）。
- 广告位、横幅、字体切换（`font-display: swap` + 尺寸相近的回退字体）同样需要预留空间。

---

## 2. 内嵌文本与语义化

- **禁止**将文字渲染在 Canvas 或纯图片中而不在 DOM 中保留文本。
- 关键关键词必须存放在 HTML 文本节点中（可被爬虫读取），包括：
  - 页面主标题、功能说明、案例标题、Prompt 文本本身。
  - 生图结果卡片下方的风格名 / 模型名，不要只作为图片叠加层用 CSS 背景图展示。
- 若因视觉需要必须在 Canvas 绘制文字（如海报生成器预览），必须在同一卡片内提供等价的可读文本节点：

```html
<figure>
  <canvas aria-hidden="true"></canvas>
  <figcaption class="sr-only">图飞 二次元 AI 生图 生成效果：雨中的少女</figcaption>
</figure>
```

- 图标按钮必须带可读名称（`aria-label`），并发文时不要把重要信息完全塞进 tooltip。
- 使用语义标签：`<header> <nav> <main> <section> <article> <footer>`，
  按钮用 `<button>`，跳转用 `<a href>`（不要给 `<div>` 绑 click 当链接）。

---

## 3. 页脚索引矩阵（Footer Matrix）

Footer 区域**必须**构建 HTML 链接矩阵，包含核心品牌词、主要功能页与长尾分类落地页的 `<a>` 锚文本。

```html
<footer>
  <nav aria-label="站点索引">
    <section>
      <h2>核心功能</h2>
      <ul>
        <li><a href="/">图飞 Dreamifly 免费 AI 生图</a></li>
        <li><a href="/tools/ai-drawing">AI 绘图工具</a></li>
        <li><a href="/tools/image-to-image">图生图 / 参考图生成</a></li>
      </ul>
    </section>
    <section>
      <h2>热门长尾场景</h2>
      <ul>
        <li><a href="/s/free-anime-generator">二次元 AI 生图</a></li>
        <li><a href="/s/unlimited-concept-art">无限制概念设计</a></li>
        <li><a href="/s/free-sticker-generator">免费 AI 贴图生成</a></li>
      </ul>
    </section>
    <section>
      <h2>灵感与帮助</h2>
      <ul>
        <li><a href="/gallery/anime-ai-generator">二次元灵感广场</a></li>
        <li><a href="/docs/how-to-unlimited-ai-image">如何实现无限制 AI 生图？</a></li>
      </ul>
    </section>
  </nav>
</footer>
```

规范：

- 锚文本用「长尾词」本身，不要用「点击这里 / 更多」。
- 每列 6–12 条，总量控制在 ~30 条以内；同类页面按搜索量排序，不堆砌。
- 必须是服务端渲染的真实 `<a href>`，不能是 JS 生成的按钮或用 `onclick` 跳转。
- 与 `sitemap.xml` 保持同步：Footer 矩阵中的落地页都应出现在 sitemap 中。
- 重复出现在每页的 Footer 链接不会被视为作弊，但**同一页正文内**同一锚文本不要重复指向不同 URL。

---

## 4. 其他技术项

| 项 | 要求 |
| --- | --- |
| `lang` | `<html lang="zh-CN">` 与实际内容语言一致 |
| `canonical` | 每个页面输出自指 canonical；带参数页（`?preset=`）指向干净 URL |
| `robots` | 结果页、个人中心等无收录价值页面用 `noindex`；不要用 robots.txt 屏蔽可收录页 |
| 分页 | `/gallery/page/2` 使用真实可爬链接，不要无限滚动而不提供分页 URL |
| 路由 | 语义化 slug；避免 `?id=123` 这类纯参数路由承载长尾内容 |
| sitemap | 包含首页、工具页、全部落地页、全部案例详情页；大站拆分 sitemap index |
| 渲染 | 长尾内容必须 SSR/SSG 输出；不要依赖客户端 hydration 后才出现文本 |
| 响应式 | 移动端优先，触控目标 ≥ 44×44px |

---

## 5. 性能预算（建议门槛）

| 指标 | 目标 |
| --- | --- |
| LCP | < 2.5s |
| CLS | < 0.1 |
| INP | < 200ms |
| 首屏 JS | < 200KB（gzip） |
| LCP 图片 | < 200KB |

超过预算时，优先砍首屏非关键 JS 与未压缩图片，而不是砍掉语义化文本。
