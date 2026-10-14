/**
 * SEO 组件模板（React / Next.js）
 * ------------------------------------------------------------------
 * 覆盖 4 大长尾模式的可复制组件骨架：
 *   - SeoJsonLd        : 服务端渲染 JSON-LD
 *   - PresetPills      : 模式 B —— 长尾词一键填入 + URL 参数同步
 *   - GalleryCard      : 模式 A —— 卡片 alt 带长尾词、显式宽高、懒加载
 *   - OneClickRemix    : 模式 D —— 教程「一键复制并生成」闭环
 *   - FooterMatrix     : 页脚索引矩阵
 *
 * 占位品牌：图飞 (Dreamifly)。接入时替换 BRAND 常量即可。
 */

export const BRAND = { name: "图飞", en: "Dreamifly", full: "图飞 (Dreamifly)" } as const;

/* ------------------------------------------------------------------ */
/* 1. 结构化数据：服务端渲染输出，避免依赖客户端 JS 执行                 */
/* ------------------------------------------------------------------ */

export function SeoJsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}

export function softwareApplicationJsonLd(props: {
  ratingValue: string;
  ratingCount: number;
  category?: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: BRAND.full,
    operatingSystem: "Web",
    applicationCategory: props.category ?? "DesignApplication",
    offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
    // 注意：评分必须来自真实数据源，不得编造
    aggregateRating: {
      "@type": "AggregateRating",
      ratingValue: props.ratingValue,
      ratingCount: props.ratingCount,
    },
  };
}

/* ------------------------------------------------------------------ */
/* 2. 模式 B：快捷提示词与风格预设                                      */
/*    标签文本直接采用长尾词，点击后填充 Prompt 并同步更新 URL 参数      */
/* ------------------------------------------------------------------ */

export type PresetTag = {
  /** 长尾词本身，直接作为可见文本（不要写成「风格1」） */
  label: string;
  prompt: string;
  model: string;
  /** 可选：该预设对应的落地页 slug，便于内链 */
  slug?: string;
};

export const presetTags: PresetTag[] = [
  { label: "二次元 AI 生图", prompt: "masterpiece, anime girl...", model: "anime-v3", slug: "free-anime-generator" },
  { label: "无限制概念设计", prompt: "sci-fi city, cyberpunk...", model: "concept-xl", slug: "unlimited-concept-art" },
];

export function PresetPills({
  tags = presetTags,
  onApply,
}: {
  tags?: PresetTag[];
  onApply: (tag: PresetTag) => void;
}) {
  return (
    <ul className="flex flex-wrap gap-2" aria-label="常用风格预设">
      {tags.map((tag) => (
        <li key={tag.label}>
          <button
            type="button"
            onClick={() => {
              onApply(tag); // 1. 直接作用于主工作流：填充 Prompt + 选模型
              const url = new URL(window.location.href); // 2. 同步 URL，可分享/可收录
              url.searchParams.set("preset", tag.label);
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

/** 无 JS 降级版：首屏 SSR 出可爬链接，点击由主工作流读取 ?preset= 参数 */
export function PresetPillsNoJs({ tags = presetTags }: { tags?: PresetTag[] }) {
  return (
    <ul className="flex flex-wrap gap-2">
      {tags.map((tag) => (
        <li key={tag.label}>
          <a href={`/?preset=${encodeURIComponent(tag.label)}&model=${tag.model}`}>{tag.label}</a>
        </li>
      ))}
    </ul>
  );
}

/* ------------------------------------------------------------------ */
/* 3. 模式 A：灵感广场卡片                                             */
/*    alt = "{品牌名} {长尾词} 生成效果：{Prompt前20字}"                  */
/* ------------------------------------------------------------------ */

export type GalleryItem = {
  id: string | number;
  title: string;
  styleKeyword: string; // 长尾词，如「二次元 AI 生图」
  styleSlug: string; // 语义化 slug，如 anime-ai-generator
  prompt: string;
  webp: string;
  avif?: string;
  width?: number;
  height?: number;
  /** 是否首屏：首屏图不加 lazy，改用 fetchpriority="high" */
  priority?: boolean;
};

export function buildGalleryAlt(item: Pick<GalleryItem, "styleKeyword" | "prompt">) {
  return `${BRAND.full} ${item.styleKeyword} 生成效果：${item.prompt.slice(0, 20)}`;
}

export function buildGalleryHref(item: Pick<GalleryItem, "styleSlug" | "id">) {
  return `/gallery/${item.styleSlug}/${item.id}`; // 语义化 URL，禁止纯 ?id=123
}

export function GalleryCard({ item }: { item: GalleryItem }) {
  const width = item.width ?? 512;
  const height = item.height ?? 512;
  return (
    <figure>
      <a href={buildGalleryHref(item)}>
        <picture>
          {item.avif ? <source srcSet={item.avif} type="image/avif" /> : null}
          <source srcSet={item.webp} type="image/webp" />
          <img
            src={item.webp}
            alt={buildGalleryAlt(item)}
            width={width}
            height={height}
            loading={item.priority ? "eager" : "lazy"}
            decoding="async"
            fetchPriority={item.priority ? "high" : "auto"}
          />
        </picture>
        <h3>{`"${item.title}" - ${BRAND.name} ${item.styleKeyword}提示词与生成效果`}</h3>
      </a>
      {/* 关键文本留在 DOM 文本节点，不要只画在图片/Canvas 里 */}
      <figcaption className="text-xs text-neutral-500">{item.prompt}</figcaption>
    </figure>
  );
}

/* ------------------------------------------------------------------ */
/* 4. 模式 D：帮助中心「一键复制并生成」闭环                            */
/* ------------------------------------------------------------------ */

export function OneClickRemix({
  prompt,
  model,
  ctaLabel = "一键复制并生成",
}: {
  prompt: string;
  model: string;
  ctaLabel?: string;
}) {
  const href = `/?prompt=${encodeURIComponent(prompt)}&model=${model}`;
  return (
    <div className="prompt-block">
      <pre>
        <code>{prompt}</code>
      </pre>
      <a
        href={href}
        onClick={() => {
          void navigator.clipboard?.writeText(prompt); // 复制 + 跳转，目标页需读取 ?prompt= 初始化
        }}
      >
        {ctaLabel}
      </a>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* 5. 页脚索引矩阵：锚文本用长尾词本身，服务端渲染真实 <a href>           */
/* ------------------------------------------------------------------ */

export const footerMatrix = [
  {
    heading: "核心功能",
    links: [
      { label: `${BRAND.name} ${BRAND.en} 免费 AI 生图`, href: "/" },
      { label: "AI 绘图工具", href: "/tools/ai-drawing" },
      { label: "图生图 / 参考图生成", href: "/tools/image-to-image" },
    ],
  },
  {
    heading: "热门长尾场景",
    links: [
      { label: "二次元 AI 生图", href: "/s/free-anime-generator" },
      { label: "无限制概念设计", href: "/s/unlimited-concept-art" },
      { label: "免费 AI 贴图生成", href: "/s/free-sticker-generator" },
    ],
  },
  {
    heading: "灵感与帮助",
    links: [
      { label: "二次元灵感广场", href: "/gallery/anime-ai-generator" },
      { label: "如何实现无限制 AI 生图？", href: "/docs/how-to-unlimited-ai-image" },
    ],
  },
] as const;

export function FooterMatrix() {
  return (
    <footer>
      <nav aria-label="站点索引">
        {footerMatrix.map((col) => (
          <section key={col.heading}>
            <h2>{col.heading}</h2>
            <ul>
              {col.links.map((link) => (
                <li key={link.href}>
                  {/* 禁止「点击这里 / 更多」这类锚文本 */}
                  <a href={link.href}>{link.label}</a>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </nav>
    </footer>
  );
}
