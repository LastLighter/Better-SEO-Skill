#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seo_audit.py — SEO 页面内容与工作流优化 自动审计脚本
=====================================================

零第三方依赖（仅使用 Python 标准库），支持 .html / .htm / .jsx / .tsx / .vue / .svelte。

用法
----
    python scripts/seo_audit.py <路径> [选项]

    <路径>                单个文件或目录（目录将递归扫描）
    -v, --verbose         输出每一项的证据（行号 / 片段）
    --json                以 JSON 输出，便于接入 CI
    --brand 图飞,Dreamifly 指定品牌词，用于校验 Title / H1 是否包含品牌
    --ext .html,.tsx      自定义扫描的扩展名（默认见 DEFAULT_EXTS）
    --min-desc N          Description 最小字符数（默认 60）
    --max-desc N          Description 最大字符数（默认 160）
    --quiet               只输出汇总统计

退出码
------
    0  全部 PASS（或仅有 WARN）
    1  存在 FAIL
    2  用法 / 路径错误
    3  扫描到 0 个文件

检查项
------
    title             Title 存在、长度、品牌词
    description       Meta Description 存在、长度、Action 引导
    canonical         canonical 链接
    open-graph        og:title / og:description / og:image
    headings          H1 唯一且存在、层级不跳级、H2 存在
    json-ld           结构化数据块存在且 JSON 可解析
    image-alt         图片 alt 完整性（含信息量判断）
    image-dimensions  图片显式 width/height 或 aspect-ratio（防 CLS）
    image-lazy        非首屏图片 loading=lazy + decoding=async
    image-format      展示图是否使用 webp/avif
    canvas-text       是否把关键文字只放在 Canvas 中而无等价文本
    cta-link          是否存在指向主工具的明确 CTA 链接
    internal-links    内链数量（语义集群）
    footer-matrix     页脚链接矩阵是否存在且锚文本非「更多/点击这里」
    keyword-stuffing  文本中是否存在异常重复的堆砌
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

DEFAULT_EXTS = (".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte")

DEFAULT_BRAND = ("图飞", "Dreamifly")

BAD_ALT_VALUES = {
    "", "image", "img", "photo", "picture", "pic", "banner", "icon",
    "logo", "图片", "图像", "照片", "图", "示例", "生成结果", "结果",
    "缩略图", "icon", "封面",
}

VAGUE_ANCHORS = {
    "更多", "点击这里", "点这里", "这里", "详情", "查看", "了解更多",
    "more", "click here", "here", "read more", "learn more", "link",
}

CTA_HINTS = (
    "生成", "生图", "开画", "出图", "立即", "马上", "免费试用", "一键",
    "开始创作", "试用", "体验", "generate", "try", "start creating", "get started",
    "create now",
)

IGNORE_EXT_IMAGE = (".svg",)

# 只有「页面级」文件才校验整页元数据；组件片段不适用（报告为 N/A 而非 FAIL）
PAGE_EXTS = (".html", ".htm")
COMPONENT_EXTS = (".jsx", ".tsx", ".vue", ".svelte")
PAGE_ONLY_CHECKS = ("title", "description", "canonical", "open-graph",
                    "headings", "json-ld", "footer-matrix")


# --------------------------------------------------------------------------- #
# 数据结构
# --------------------------------------------------------------------------- #

@dataclass
class CheckResult:
    name: str
    status: str  # PASS | WARN | FAIL | SKIP
    message: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class FileReport:
    path: str
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, name: str, status: str, message: str, evidence: list[str] | None = None) -> None:
        self.checks.append(CheckResult(name, status, message, evidence or []))

    def count(self, status: str) -> int:
        return sum(1 for c in self.checks if c.status == status)

    @property
    def verdict(self) -> str:
        if self.count("FAIL"):
            return "FAIL"
        if self.count("WARN"):
            return "WARN"
        return "PASS"


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #

def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def strip_comments(text: str) -> str:
    """移除 HTML 注释与 JS 块注释，避免把注释里的代码当成真实标签。"""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"\{/\*.*?\*/\}", "", text, flags=re.S)
    return text


def visible_text(html: str) -> str:
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\{[^{}]*\}", " ", t)  # JSX 表达式
    t = re.sub(r"&[a-zA-Z#0-9]+;", " ", t)
    return re.sub(r"\s+", " ", t).strip()


TAG_RE_CACHE: dict[str, re.Pattern[str]] = {}


def iter_tags(html: str, tag: str):
    """产出 (属性字符串, 起始索引, 完整匹配文本) 的生成器，支持 JSX 自闭合与花括号属性。"""
    pattern = TAG_RE_CACHE.get(tag)
    if pattern is None:
        pattern = re.compile(rf"<{tag}\b((?:[^<>\"']|\"[^\"]*\"|'[^']*')*?)/?>", re.I | re.S)
        TAG_RE_CACHE[tag] = pattern
    for m in pattern.finditer(html):
        yield m.group(1), m.start(), m.group(0)


def attr(attrs: str, name: str) -> str | None:
    """读取属性值，兼容 HTML / JSX（含表达式与模板字符串）。"""
    m = re.search(
        rf"""\b{name}\s*=\s*(?:"([^"]*)"|'([^']*)'|\{{([^}}]*)\}})""",
        attrs,
        re.I | re.S,
    )
    if not m:
        return None
    return next((g for g in m.groups() if g is not None), "")


def has_attr(attrs: str, name: str) -> bool:
    return re.search(rf"(?:^|\s){name}(?:\s|=|$|>)", attrs, re.I) is not None


def attr_or_expression(attrs: str, name: str) -> str | None:
    """兼容 loading={cond ? 'eager' : 'lazy'} / width={512} 这类 JSX 写法。"""
    direct = attr(attrs, name)
    if direct is not None:
        return direct
    if re.search(rf"\b{name}\s*=", attrs, re.I):
        return "__EXPR__"
    return None


def is_dynamic(value: str | None) -> bool:
    """属性值来自变量/表达式，静态扫描无法判定 -> 视为已处理但记录提示。"""
    if value is None:
        return False
    if value == "__EXPR__":
        return True
    return bool(re.search(r"[{}]|\$\{|item\.|props\.|\.map|cfg\.|tag\.", value))


# --------------------------------------------------------------------------- #
# 各项检查
# --------------------------------------------------------------------------- #

def check_title(html: str, rep: FileReport, brands: tuple[str, ...], verbose: bool) -> None:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    ev: list[str] = []
    if not m and "metadata" in html:
        m2 = re.search(r"\btitle\s*:\s*(?:\"([^\"]*)\"|'([^']*)'|`([^`]*)`)", html, re.S)
        if m2:
            title = next((g for g in m2.groups() if g), "")
            ev.append(f"L{line_of(html, m2.start())}: metadata.title = {title[:80]}")
            _judge_title(title, rep, brands, ev, dynamic=True)
            return
    if not m:
        rep.add("title", "FAIL", "未找到 <title> 或 Next.js metadata.title", ev)
        return
    title = re.sub(r"\s+", " ", m.group(1)).strip()
    ev.append(f"L{line_of(html, m.start())}: {title[:120]}")
    _judge_title(title, rep, brands, ev, dynamic=is_dynamic(title))


def _judge_title(title: str, rep: FileReport, brands: tuple[str, ...], ev: list[str], dynamic: bool) -> None:
    if not title:
        rep.add("title", "FAIL", "Title 为空", ev)
        return
    if dynamic:
        rep.add("title", "WARN", "Title 由模板/变量生成，需人工确认真实渲染结果", ev)
        return
    length = len(title)
    problems: list[str] = []
    if length > 60:
        problems.append(f"过长（{length} 字符 > 60）")
    if length < 10:
        problems.append(f"过短（{length} 字符）")
    if brands and not any(b.lower() in title.lower() for b in brands):
        problems.append("未包含品牌词")
    if "|" not in title and "-" not in title and "－" not in title and "—" not in title:
        problems.append("缺少分隔符，建议 {品牌} - {长尾词1} | {长尾词2}")
    if problems:
        rep.add("title", "WARN", "；".join(problems), ev)
    else:
        rep.add("title", "PASS", f"Title 规范（{length} 字符，含品牌与分隔符）", ev)


def check_description(html: str, rep: FileReport, min_len: int, max_len: int, verbose: bool) -> None:
    m = re.search(
        r"""<meta[^>]*\bname\s*=\s*["']description["'][^>]*\bcontent\s*=\s*["']([^"']*)["']""",
        html, re.I | re.S,
    ) or re.search(
        r"""<meta[^>]*\bcontent\s*=\s*["']([^"']*)["'][^>]*\bname\s*=\s*["']description["']""",
        html, re.I | re.S,
    )
    ev: list[str] = []
    if not m:
        m2 = re.search(r"""\bdescription\s*:\s*(?:"([^"]*)"|'([^']*)'|`([^`]*)`)""", html, re.S)
        if m2:
            desc = next((g for g in m2.groups() if g), "")
            ev.append(f"L{line_of(html, m2.start())}: metadata.description = {desc[:100]}")
            rep.add("description", "WARN", "Description 来自 metadata 模板，需确认最终渲染长度与 CTA", ev)
            return
        rep.add("description", "FAIL", "缺少 meta description", ev)
        return
    desc = re.sub(r"\s+", " ", m.group(1)).strip()
    ev.append(f"L{line_of(html, m.start())}: {desc[:140]}")
    if is_dynamic(desc):
        rep.add("description", "WARN", "Description 为动态值，需人工确认", ev)
        return
    n = len(desc)
    problems = []
    if n == 0:
        rep.add("description", "FAIL", "meta description 为空", ev)
        return
    if n > max_len:
        problems.append(f"过长（{n} > {max_len}）")
    if n < min_len:
        problems.append(f"过短（{n} < {min_len}）")
    if not any(h.lower() in desc.lower() for h in CTA_HINTS):
        problems.append("缺少 Action 引导词（如 立即/免费/一键/Generate）")
    if problems:
        rep.add("description", "WARN", "；".join(problems), ev)
    else:
        rep.add("description", "PASS", f"Description 规范（{n} 字符，含 CTA）", ev)


def check_canonical(html: str, rep: FileReport, verbose: bool) -> None:
    m = re.search(r"""<link[^>]*\brel\s*=\s*["']canonical["'][^>]*>""", html, re.I)
    if not m:
        m = re.search(r"""\balternates\s*:\s*\{[^}]*canonical""", html, re.S | re.I)
        if m:
            rep.add("canonical", "PASS", "存在 Next.js alternates.canonical",
                    [f"L{line_of(html, m.start())}"] if verbose else [])
            return
        rep.add("canonical", "WARN", "未找到 canonical 链接（带参数页需指向干净 URL）")
        return
    href = attr(m.group(0), "href") or ""
    if is_dynamic(href):
        rep.add("canonical", "PASS", "canonical 为动态生成", [f"L{line_of(html, m.start())}"] if verbose else [])
    elif href:
        rep.add("canonical", "PASS", f"canonical = {href[:80]}", [f"L{line_of(html, m.start())}"] if verbose else [])
    else:
        rep.add("canonical", "WARN", "canonical 存在但 href 为空", [])


def check_open_graph(html: str, rep: FileReport, verbose: bool) -> None:
    need = ("og:title", "og:description", "og:image")
    found = {k: bool(re.search(rf"""(?:property|name)\s*=\s*["']{re.escape(k)}["']""", html, re.I)) for k in need}
    missing = [k for k, v in found.items() if not v]
    if not missing:
        rep.add("open-graph", "PASS", "og:title / og:description / og:image 齐全", [])
    elif len(missing) == len(need):
        rep.add("open-graph", "WARN", "未找到任何 Open Graph 标签（分享与富展现会退化）", [])
    else:
        rep.add("open-graph", "WARN", "缺少 " + "、".join(missing), [])


def check_headings(html: str, rep: FileReport, brands: tuple[str, ...], verbose: bool) -> None:
    h1: list[tuple[int, str]] = []
    levels: list[tuple[int, int, str]] = []  # (level, line, text)
    for level in (1, 2, 3, 4, 5, 6):
        for attrs, idx, full in _iter_heading_tags(html, level):
            text = _heading_text(html, idx, level, full)
            levels.append((level, line_of(html, idx), text))
            if level == 1:
                h1.append((line_of(html, idx), text))
    levels.sort(key=lambda x: x[1])

    ev = [f"L{ln}: H{lv} {txt[:60]}" for lv, ln, txt in levels] if verbose else []
    if not h1:
        rep.add("headings", "FAIL", "缺少 <h1>（全页必须有且仅有一个）", ev)
        return
    if len(h1) > 1:
        rep.add("headings", "FAIL", f"发现 {len(h1)} 个 <h1>，必须唯一",
                [f"L{ln}: {txt[:60]}" for ln, txt in h1])
        return
    h1_text = h1[0][1]
    msgs = ["H1 唯一"]
    status = "PASS"
    if brands and not any(b.lower() in h1_text.lower() for b in brands):
        msgs.append("H1 未包含品牌词")
        status = "WARN"
    if not any(lv == 2 for lv, _, _ in levels):
        msgs.append("缺少 H2 分层")
        status = "WARN"
    prev = 0
    for lv, ln, _ in levels:
        if prev and lv > prev + 1:
            msgs.append(f"层级跳级 L{ln}: H{prev} → H{lv}")
            status = "WARN"
            break
        prev = lv
    rep.add("headings", status, "；".join(msgs), ev)


def _iter_heading_tags(html: str, level: int):
    pattern = re.compile(rf"<h{level}\b[^>]*>(.*?)</h{level}>", re.I | re.S)
    for m in pattern.finditer(html):
        yield m.group(0), m.start(), m.group(1)


def _heading_text(html: str, idx: int, level: int, full: str) -> str:
    inner = re.sub(r"<[^>]+>", " ", full)
    inner = re.sub(r"\{[^{}]*\}", " ", inner)
    return re.sub(r"\s+", " ", inner).strip()


def check_jsonld(html: str, rep: FileReport, verbose: bool) -> None:
    blocks = list(re.finditer(
        r"""<script[^>]*\btype\s*=\s*["']application/ld\+json["'][^>]*>(.*?)</script>""",
        html, re.I | re.S,
    ))
    if not blocks:
        rep.add("json-ld", "WARN", "未找到 JSON-LD 结构化数据（建议注入 SoftwareApplication）", [])
        return
    bad: list[str] = []
    types: list[str] = []
    for m in blocks:
        raw = m.group(1).strip()
        raw = re.sub(r"^\s*\{/\*.*?\*/\}", "", raw, flags=re.S).strip()
        if not raw or raw.startswith("{/*") or "__html" in raw:
            types.append("(动态注入，需运行时确认)")
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            bad.append(f"L{line_of(html, m.start())}: JSON 解析失败 - {exc.msg}")
            continue
        for t in _collect_types(data):
            types.append(t)
    ev = [f"类型：{', '.join(sorted(set(types)))}"] if types else []
    if verbose:
        ev += [f"L{line_of(html, m.start())}: {len(m.group(1))} 字符" for m in blocks]
    if bad:
        rep.add("json-ld", "FAIL", "JSON-LD 无法解析：" + "；".join(bad), ev)
    elif not types:
        rep.add("json-ld", "WARN", "存在 JSON-LD 块但为动态注入，需确认服务端输出", ev)
    else:
        rep.add("json-ld", "PASS", f"JSON-LD 可解析，类型：{', '.join(sorted(set(types)))}", ev)


def _collect_types(node) -> list[str]:
    out: list[str] = []
    if isinstance(node, dict):
        t = node.get("@type")
        if isinstance(t, str):
            out.append(t)
        elif isinstance(t, list):
            out.extend([x for x in t if isinstance(x, str)])
        for v in node.values():
            out.extend(_collect_types(v))
    elif isinstance(node, list):
        for v in node:
            out.extend(_collect_types(v))
    return out


def check_images(html: str, rep: FileReport, verbose: bool) -> None:
    tags = list(iter_tags(html, "img"))
    if not tags:
        rep.add("image-alt", "SKIP", "页面无 <img>（若为 Canvas/背景图渲染，请人工确认文本已入 DOM）", [])
        return

    no_alt: list[str] = []
    bad_alt: list[str] = []
    missing_dim: list[str] = []
    missing_lazy: list[str] = []
    non_modern: list[str] = []
    dynamic_dim = 0

    for attrs, idx, full in tags:
        ln = line_of(html, idx)
        src = attr(attrs, "src") or ""
        alt = attr(attrs, "alt")
        if alt is None and not re.search(r"\balt\s*=", attrs):
            no_alt.append(f"L{ln}: {src[:60]}")
        else:
            alt_val = (alt or "").strip()
            if alt_val and alt_val.lower() in BAD_ALT_VALUES:
                bad_alt.append(f"L{ln}: alt=\"{alt_val}\" 无信息量")
            elif alt_val and len(alt_val) < 4 and not is_dynamic(alt_val):
                bad_alt.append(f"L{ln}: alt=\"{alt_val}\" 过短，建议含品牌+长尾词+摘要")

        # 尺寸
        w = attr_or_expression(attrs, "width")
        h = attr_or_expression(attrs, "height")
        style = attr(attrs, "style") or ""
        cls = attr(attrs, "className") or attr(attrs, "class") or ""
        has_ratio_attr = "aspect-ratio" in style or "aspect-" in cls
        if (w is None or h is None) and not has_ratio_attr:
            missing_dim.append(f"L{ln}: {src[:50]}")
        elif is_dynamic(w) or is_dynamic(h):
            dynamic_dim += 1

        # 懒加载
        loading = attr_or_expression(attrs, "loading")
        decoding = attr_or_expression(attrs, "decoding")
        fetchprio = attr_or_expression(attrs, "fetchpriority") or attr_or_expression(attrs, "fetchPriority")
        is_priority = (fetchprio or "").lower() == "high" or (loading or "").lower() == "eager"
        if not is_priority:
            problems = []
            if loading is None:
                problems.append("loading")
            elif "lazy" not in (loading or "").lower() and loading != "__EXPR__":
                problems.append(f"loading={loading}")
            if decoding is None:
                problems.append("decoding")
            if problems:
                missing_lazy.append(f"L{ln}: 缺 {'/'.join(problems)}（{src[:40]}）")

        # 格式
        low = src.lower()
        if low and not any(low.endswith(e) for e in IGNORE_EXT_IMAGE):
            if not re.search(r"\.(webp|avif)([?#]|$)", low) and not is_dynamic(src):
                non_modern.append(f"L{ln}: {src[:60]}")

    n = len(tags)
    if no_alt:
        rep.add("image-alt", "FAIL", f"{len(no_alt)}/{n} 个 <img> 缺少 alt", no_alt[:12])
    elif bad_alt:
        rep.add("image-alt", "WARN", f"{len(bad_alt)}/{n} 个 alt 无信息量", bad_alt[:12])
    else:
        rep.add("image-alt", "PASS", f"{n} 个 <img> 均有信息量 alt", [] if not verbose else [f"共 {n} 张"])

    if missing_dim:
        rep.add("image-dimensions", "WARN",
                f"{len(missing_dim)}/{n} 张图片缺显式 width/height 或 aspect-ratio（CLS 风险）",
                missing_dim[:12])
    else:
        extra = f"，{dynamic_dim} 张为动态值" if dynamic_dim else ""
        rep.add("image-dimensions", "PASS", f"{n} 张图片均已声明尺寸{extra}", [])

    if missing_lazy:
        rep.add("image-lazy", "WARN", f"{len(missing_lazy)} 张非首屏图片缺 lazy/async", missing_lazy[:12])
    else:
        rep.add("image-lazy", "PASS", "图片懒加载与异步解码已标注", [])

    if non_modern:
        rep.add("image-format", "WARN", f"{len(non_modern)} 张图片非 webp/avif", non_modern[:12])
    else:
        rep.add("image-format", "PASS", "图片格式均为 webp/avif（或动态生成）", [])


def check_canvas(html: str, rep: FileReport, verbose: bool) -> None:
    canvases = list(iter_tags(html, "canvas"))
    if not canvases:
        rep.add("canvas-text", "PASS", "未使用 <canvas> 承载文本", [])
        return
    ev = [f"L{line_of(html, i)}: <canvas>" for _, i, _ in canvases[:10]]
    sr_only = len(re.findall(r"class(?:Name)?\s*=\s*[\"'][^\"']*sr-only", html, re.I))
    figcaption = len(re.findall(r"<figcaption", html, re.I))
    aria = len(re.findall(r"aria-label|aria-describedby", html, re.I))
    if sr_only or figcaption or aria:
        rep.add("canvas-text", "WARN",
                f"存在 {len(canvases)} 个 <canvas>，检测到 {sr_only} 个 sr-only / {figcaption} 个 figcaption / "
                f"{aria} 个 aria 标签，请确认 Canvas 内容有等价 DOM 文本",
                ev if verbose else [])
    else:
        rep.add("canvas-text", "FAIL",
                f"存在 {len(canvases)} 个 <canvas> 但未发现等价可读文本（sr-only / figcaption / aria）",
                ev)


def check_links(html: str, rep: FileReport, verbose: bool) -> None:
    anchors: list[tuple[int, str, str]] = []
    for attrs, idx, full in iter_tags(html, "a"):
        href = attr(attrs, "href") or ""
        m = re.search(r">(.*?)</a>", html[idx:], re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", m.group(1)) if m else ""
        text = re.sub(r"\{[^{}]*\}", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        anchors.append((line_of(html, idx), href, text))

    if not anchors:
        rep.add("cta-link", "FAIL", "页面没有任何 <a> 链接（SPA 空壳或全用 div+onclick）", [])
        rep.add("internal-links", "FAIL", "无内链，无法形成语义集群", [])
        return

    internal = [(ln, h, t) for ln, h, t in anchors
                if h.startswith("/") or h.startswith("#") or h.startswith(".")
                or "example.com" in h
                or (h and not re.match(r"^[a-z]+:", h, re.I))]
    external = [(ln, h, t) for ln, h, t in anchors if re.match(r"^https?://", h or "", re.I)]
    cta = [(ln, h, t) for ln, h, t in anchors
           if any(k.lower() in t.lower() for k in CTA_HINTS)]

    app_like = [(ln, h, t) for ln, h, t in anchors
                if re.search(r"prompt=|preset=|model=|/\?|/generate|/create|/tools/", h or "", re.I)]

    if app_like:
        ev = [f"L{ln}: {t[:40]} -> {h[:70]}" for ln, h, t in app_like[:6]] if verbose else []
        rep.add("cta-link", "PASS", f"存在 {len(app_like)} 个带工作流参数的 CTA 链接（Prompt/预设已带入）", ev)
    elif cta:
        ev = [f"L{ln}: {t[:40]} -> {h[:70]}" for ln, h, t in cta[:6]] if verbose else []
        rep.add("cta-link", "WARN",
                f"存在 {len(cta)} 个含动作词的链接，但未见携带 prompt/preset/model 参数，请确认点击后能作用于主工作流",
                ev)
    else:
        rep.add("cta-link", "FAIL", "未找到指向主生图工具的明确 Call-to-Action 链接", [])

    if len(internal) >= 3:
        rep.add("internal-links", "PASS", f"内链 {len(internal)} 条（外链 {len(external)} 条）", [])
    else:
        rep.add("internal-links", "WARN", f"内链仅 {len(internal)} 条，建议补充语义集群内链",
                [f"L{ln}: {t[:40]} -> {h[:60]}" for ln, h, t in internal[:5]])


def check_footer(html: str, rep: FileReport, verbose: bool) -> None:
    m = re.search(r"<footer\b.*?</footer>", html, re.S | re.I)
    if not m:
        rep.add("footer-matrix", "WARN", "未找到 <footer>，页脚索引矩阵缺失", [])
        return
    block = m.group(0)
    links: list[tuple[str, str]] = []
    for am in re.finditer(r"<a\b[^>]*href\s*=\s*[\"']([^\"']*)[\"'][^>]*>(.*?)</a>", block, re.S | re.I):
        text = re.sub(r"<[^>]+>", " ", am.group(2))
        text = re.sub(r"\{[^{}]*\}", " ", text)
        links.append((am.group(1), re.sub(r"\s+", " ", text).strip()))
    if not links:
        rep.add("footer-matrix", "WARN", "Footer 内无任何 <a> 链接，索引矩阵缺失", [])
        return

    groups = len(re.findall(r"<h[2-6]\b", block, re.I)) + len(re.findall(r"<section\b", block, re.I))
    vague = [t for _, t in links if (t and t.lower() in VAGUE_ANCHORS) or (t and len(t) < 2)]
    ev = [f"{t} -> {h}" for h, t in links[:12]] if verbose else []

    # 页脚矩阵可以是「多组标题 + 少量链接」的紧凑导航，因此按分组 OR 条数判定
    if vague:
        rep.add("footer-matrix", "WARN", f"{len(vague)}/{len(links)} 条锚文本无信息量（如「更多/点击这里」）",
                [f'"{t}"' for t in vague[:8]])
    elif len(links) >= 6 or (len(links) >= 3 and groups >= 2):
        rep.add("footer-matrix", "PASS",
                f"Footer 索引矩阵：{len(links)} 条链接 / {groups} 个分组，锚文本均含信息", ev)
    else:
        rep.add("footer-matrix", "WARN",
                f"Footer 仅 {len(links)} 条链接且无分组，建议构建品牌词+功能页+长尾落地页矩阵", ev)


def check_keyword_stuffing(html: str, rep: FileReport, verbose: bool) -> None:
    text = visible_text(html)
    if len(text) < 200:
        rep.add("keyword-stuffing", "SKIP", f"可见文本过少（{len(text)} 字符），可能是客户端渲染页面", [])
        return
    tokens: dict[str, int] = {}
    for tok in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z]{4,}", text):
        key = tok.lower()
        if key in {"the", "and", "with", "that", "this", "from", "your", "http", "https", "com", "www"}:
            continue
        tokens[key] = tokens.get(key, 0) + 1
    total = sum(tokens.values()) or 1
    top = sorted(tokens.items(), key=lambda kv: -kv[1])[:5]
    offenders = [(w, c, c / total) for w, c in top if c >= 8 and c / total > 0.05]
    if offenders:
        rep.add("keyword-stuffing", "WARN",
                "疑似关键词堆砌：" + "、".join(f"{w}×{c}" for w, c, _ in offenders),
                [f"密度 {r:.1%}" for _, _, r in offenders] if verbose else [])
    else:
        rep.add("keyword-stuffing", "PASS", f"词频正常（最高 {top[0][0]}×{top[0][1]}）" if top else "词频正常", [])


# --------------------------------------------------------------------------- #
# 单文件分析
# --------------------------------------------------------------------------- #

def audit_text(text: str, path: str, brands: tuple[str, ...],
               min_desc: int, max_desc: int, verbose: bool) -> FileReport:
    rep = FileReport(path=path)
    html = strip_comments(text)
    suffix = Path(path).suffix.lower()
    is_page = suffix in PAGE_EXTS
    is_component = suffix in COMPONENT_EXTS

    check_headings(html, rep, brands, verbose)
    check_jsonld(html, rep, verbose)
    check_images(html, rep, verbose)
    check_canvas(html, rep, verbose)
    check_links(html, rep, verbose)
    check_footer(html, rep, verbose)

    if is_page:
        check_title(html, rep, brands, verbose)
        check_description(html, rep, min_desc, max_desc, verbose)
        check_canonical(html, rep, verbose)
        check_open_graph(html, rep, verbose)
        check_keyword_stuffing(html, rep, verbose)
    else:
        # 组件片段：补一条提示，说明整页项需要在页面/布局文件上校验
        rep.add("page-scope", "SKIP",
                f"{suffix or '未知'} 视为组件片段，整页元数据请对页面文件（如 page.html / layout.tsx）运行审计",
                [])
        if is_component:
            for name in PAGE_ONLY_CHECKS:
                _demote_to_na(rep, name)

    # 组件文件的词频受代码标识符干扰，直接标记为不适用
    if is_component:
        _demote_to_na(rep, "keyword-stuffing")

    order = {name: i for i, name in enumerate(
        ("title", "description", "canonical", "open-graph", "headings", "json-ld", "image-alt",
         "image-dimensions", "image-lazy", "image-format", "canvas-text", "cta-link",
         "internal-links", "footer-matrix", "keyword-stuffing", "page-scope"))}
    rep.checks.sort(key=lambda c: order.get(c.name, 99))
    return rep


def _demote_to_na(rep: FileReport, name: str) -> None:
    """把页面级检查在组件文件中的结论降级为 N/A（不计入 WARN/FAIL）。"""
    for c in rep.checks:
        if c.name == name and c.status in ("FAIL", "WARN"):
            c.status = "NA"
            c.message = "组件片段不适用（" + c.message + "）"
        elif c.name == name and c.status in ("PASS", "SKIP"):
            c.status = "NA"
            c.message = "组件片段不适用"


# --------------------------------------------------------------------------- #
# 输出
# --------------------------------------------------------------------------- #

ICON = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]", "SKIP": "[SKIP]", "NA": "[N/A ]"}


def print_report(rep: FileReport, verbose: bool, quiet: bool) -> None:
    if quiet:
        print(f"{ICON[rep.verdict]} {rep.path}  "
              f"(PASS {rep.count('PASS')} / WARN {rep.count('WARN')} / FAIL {rep.count('FAIL')} / "
              f"N/A {rep.count('NA')})")
        return
    print("=" * 78)
    print(f"文件：{rep.path}")
    print("-" * 78)
    for c in rep.checks:
        if c.status in ("SKIP", "NA") and not verbose:
            continue
        print(f"  {ICON[c.status]} {c.name:<18} {c.message}")
        if verbose:
            for e in c.evidence:
                print(f"          · {e}")
    print(f"  → 结论：{ICON[rep.verdict]} PASS {rep.count('PASS')} / "
          f"WARN {rep.count('WARN')} / FAIL {rep.count('FAIL')} / N/A {rep.count('NA')}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="seo_audit.py",
        description="SEO 页面内容与工作流优化 自动审计（零依赖）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python scripts/seo_audit.py app/\n"
               "  python scripts/seo_audit.py page.html -v\n"
               "  python scripts/seo_audit.py app/ --json > seo-report.json\n"
               "  python scripts/seo_audit.py app/ --brand 图飞,Dreamifly\n",
    )
    parser.add_argument("path", help="要审计的文件或目录")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出每项证据（行号/片段）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    parser.add_argument("--quiet", action="store_true", help="只输出汇总行")
    parser.add_argument("--brand", default=",".join(DEFAULT_BRAND),
                        help="品牌词，逗号分隔（默认：图飞,Dreamifly）")
    parser.add_argument("--ext", default=",".join(DEFAULT_EXTS), help="扫描的扩展名，逗号分隔")
    parser.add_argument("--exclude", default=",.git,node_modules,.next,dist,build,.turbo,coverage",
                        help="扫描时忽略的目录名，逗号分隔（含空项以允许留空）")
    parser.add_argument("--no-recursive", action="store_true", help="目录只扫描第一层，不递归")
    parser.add_argument("--min-desc", type=int, default=60, help="Description 最小字符数（默认 60）")
    parser.add_argument("--max-desc", type=int, default=160, help="Description 最大字符数（默认 160）")
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"[FAIL] 路径不存在：{target}", file=sys.stderr)
        return 2

    exts = tuple(e if e.startswith(".") else "." + e for e in args.ext.split(",") if e.strip())
    brands = tuple(b.strip() for b in args.brand.split(",") if b.strip())
    excluded = {d.strip() for d in args.exclude.split(",") if d.strip()}

    if target.is_file():
        files = [target]
    else:
        walker = target.glob("*") if args.no_recursive else target.rglob("*")
        files = sorted(
            p for p in walker
            if p.is_file()
            and p.suffix.lower() in exts
            and not excluded.intersection(p.parts)
        )

    if not files:
        print(f"[FAIL] 未在 {target} 中找到匹配的文件（扩展名：{', '.join(exts)}）", file=sys.stderr)
        return 3

    reports: list[FileReport] = []
    for f in files:
        try:
            reports.append(audit_text(read_text(f), str(f), brands, args.min_desc, args.max_desc, args.verbose))
        except OSError as exc:
            rep = FileReport(path=str(f))
            rep.add("read", "FAIL", f"读取失败：{exc}", [])
            reports.append(rep)

    totals: dict[str, int] = {"PASS": 0, "WARN": 0, "FAIL": 0, "NA": 0}
    for rep in reports:
        for s in totals:
            totals[s] += rep.count(s)

    if args.json:
        payload = {
            "summary": {
                "files": len(reports),
                "fail_files": sum(1 for r in reports if r.verdict == "FAIL"),
                "warn_files": sum(1 for r in reports if r.verdict == "WARN"),
                "pass_files": sum(1 for r in reports if r.verdict == "PASS"),
                "checks": totals,
                "verdict": "FAIL" if totals["FAIL"] else ("WARN" if totals["WARN"] else "PASS"),
            },
            "files": [
                {"path": r.path, "verdict": r.verdict, "checks": [asdict(c) for c in r.checks]}
                for r in reports
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for rep in reports:
            print_report(rep, args.verbose, args.quiet)
        print("=" * 78)
        print(f"总计：{len(reports)} 个文件 | FAIL {totals['FAIL']} · WARN {totals['WARN']} · "
              f"PASS {totals['PASS']} · N/A {totals['NA']}")
        verdict = "FAIL" if totals["FAIL"] else ("WARN" if totals["WARN"] else "PASS")
        print(f"整体结论：{ICON[verdict]}")
        print("=" * 78)

    return 1 if totals["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
