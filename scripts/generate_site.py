#!/usr/bin/env python3
"""
Single-file Static Site Generator for GitHub Pages (Root & Project Pages)
Features:
- Zero JavaScript, Semantic HTML & Accessibility (A11y) optimized.
- Inlined CSS with auto Dark Mode support and keyboard navigation focus.
- Dynamic canonical URLs, OpenGraph metadata, sitemap.xml & robots.txt.
"""

import argparse
import html
import re
import shutil
import sys
from datetime import date
from pathlib import Path
import markdown
import yaml

# ==============================================================================
# INLINED STYLESHEET (Light/Dark mode, A11y, Focus visible, Responsive)
# ==============================================================================
INLINED_CSS = """
:root {
  --bg: #ffffff;
  --fg: #1a1a1a;
  --muted: #595959;
  --border: #e0e0e0;
  --th-bg: #f6f8fa;
  --code-bg: #f4f4f4;
  --link: #0969da;
  --focus-ring: #0969da;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0d1117;
    --fg: #e6edf3;
    --muted: #8b949e;
    --border: #30363d;
    --th-bg: #161b22;
    --code-bg: #161b22;
    --link: #58a6ff;
    --focus-ring: #58a6ff;
  }
}

*, *::before, *::after {
  box-sizing: border-box;
}

/* 1. Mở rộng độ rộng trang & font chữ thoáng hơn */
body {
  margin: 1.5rem auto;
  max-width: min(44rem, 92vw); /* Mở rộng chiều ngang linh hoạt theo màn hình */
  padding: 0 0.75rem 3.5rem;
  background-color: var(--bg);
  color: var(--fg);
  font: 1.15rem/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  word-wrap: break-word;
}

/* 2. Thiết kế lại Navbar: sạch sẽ, có đường phân cách và phân biệt Brand/Link */
.site-header {
  margin-bottom: 2.5rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 1rem;
}

nav ul {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  list-style: none;
  padding: 0;
  margin: 0;
  gap: 0.5rem 1.25rem;
  font-size: 1rem;
}

nav a {
  text-decoration: none;
  color: var(--muted);
  font-weight: 500;
}

nav a:hover, 
nav a:focus-visible {
  color: var(--fg);
  text-decoration: underline;
  text-underline-offset: 4px;
}

/* Làm nổi bật Logo / Tên thương hiệu ở đầu Navbar */
nav .nav-brand {
  color: var(--fg);
  font-weight: 700;
  margin-right: 0.5rem;
}

/* Accessibility: Skip Link */
.skip-link {
  position: absolute;
  top: -9999px;
  left: 1rem;
  background: var(--fg);
  color: var(--bg);
  padding: 0.5rem 1rem;
  z-index: 100;
  text-decoration: none;
  font-weight: 600;
  border-radius: 4px;
}
.skip-link:focus {
  top: 1rem;
}

/* Accessibility: Screen Reader Only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Keyboard focus indicators */
:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 3px;
}

/* Typography & Headings */
h1, h2, h3, h4, h5, h6 {
  line-height: 1.3;
  margin-top: 1.75em;
  margin-bottom: 0.5em;
  color: var(--fg);
}
h1 { font-size: 1.85rem; margin-top: 0.5em; }
h2 { font-size: 1.45rem; }
h3 { font-size: 1.2rem; }

p, ul, ol, blockquote, table {
  margin-top: 0;
  margin-bottom: 1.25rem;
}

/* Khử margin thừa cho danh sách con lồng bên trong (nested list) */
li > ul,
li > ol {
  margin-top: 0.25rem;
  margin-bottom: 0;
}

/* Khoảng cách gọn gàng giữa các dòng li */
li {
  margin-bottom: 0.25rem;
}

a {
  color: var(--link);
  text-decoration: underline;
  text-underline-offset: 2px;
}

a:hover {
  text-decoration-thickness: 2px;
}

.page-header {
  text-align: center;
  margin-bottom: 2rem;
}
.page-header img {
  max-width: 100%;
  height: auto;
  margin: 0 auto 1rem;
  display: block;
}

/* Code & Pre (Zero-JS minimal style) */
code {
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.875em;
  background-color: var(--code-bg);
  padding: 0.2em 0.4em;
  border-radius: 4px;
  border: 1px solid var(--border);
}
pre {
  background-color: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem;
  overflow-x: auto;
  tab-size: 2;
}
pre code {
  background: transparent;
  padding: 0;
  border: none;
  font-size: 0.9rem;
}

/* Tables */
.table-wrapper {
  overflow-x: auto;
  margin-bottom: 1.5rem;
}
table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
th, td {
  border: 1px solid var(--border);
  padding: 0.6rem 0.75rem;
  vertical-align: top;
}
th {
  background-color: var(--th-bg);
  font-weight: 600;
}

/* Blockquote */
blockquote {
  border-left: 4px solid var(--border);
  padding-left: 1rem;
  color: var(--muted);
  font-style: italic;
}

/* Media & Print */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
@media print {
  body {
    max-width: none;
    color: #000;
    background: #fff;
  }
  .skip-link, nav {
    display: none;
  }
}
"""

# ==============================================================================
# HTML BASE TEMPLATE
# ==============================================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{{language}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">

  <title>{{title}}</title>
  <meta name="description" content="{{description}}">
  <meta name="author" content="{{author}}">

  <link rel="canonical" href="{{canonical_url}}">
  <meta property="og:title" content="{{title}}">
  <meta property="og:description" content="{{description}}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{{canonical_url}}">
  <link rel="icon" href="https://hocbigg.github.io/images/favicon.ico">

  <style>
{{css}}
  </style>
</head>
<body>

  <a href="#main-content" class="skip-link">Skip to main content</a>

  <header class="site-header">
    <nav aria-label="Main Navigation">
{{nav_html}}
    </nav>
  </header>

  <main id="main-content">
    <article>
{{header_html}}
{{content_html}}
    </article>
  </main>

</body>
</html>
"""

PAGE_HEADER_TEMPLATE = """<header class="page-header">
  <img src="{base_prefix}images/logo.png" alt="Hocbigg logo" width="120" height="120">
  <h1>{title}</h1>
</header>"""

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def parse_front_matter(text: str):
    """Extract YAML front-matter and markdown body."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            return meta, parts[2].strip()
    return {}, text.strip()


def extract_h1(markdown_text: str):
    """Extract first level-1 heading if present."""
    for line in markdown_text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def rewrite_internal_md_links(html_text: str) -> str:
    """Rewrite relative .md href links to .html."""
    return re.sub(r'href="((?!https?://)[^"]+)\.md"', r'href="\1.html"', html_text)


def enhance_external_links(html_text: str) -> str:
    """Add target="_blank", rel and screen-reader context to external links."""
    def repl(m):
        attrs = m.group(1)
        url = m.group(2)
        if 'target=' in attrs:
            return m.group(0)
        return f'<a {attrs}href="{url}" target="_blank" rel="noopener noreferrer"'

    # Inject attributes
    html_text = re.sub(r'<a\s+([^>]*?)href="(https?://[^"]+)"', repl, html_text)
    return html_text


def wrap_tables(html_text: str) -> str:
    """Wrap <table> in responsive div with tabindex for keyboard a11y scroll."""
    return re.sub(
        r'(<table>[\s\S]*?</table>)',
        r'<div class="table-wrapper" tabindex="0" role="region" aria-label="Scrollable table">\1</div>',
        html_text
    )


def build_nav(is_root: bool, page_name: str = "") -> str:
    """Construct semantic accessible navigation with global & project links."""
    items = [
        '      <li><a href="https://hocbigg.github.io/" class="nav-brand">Hocbigg</a></li>'
    ]

    # Nếu đang ở trong Project Page, thêm link quay về trang đầu của Project đó
    if not is_root and page_name:
        items.append(f'      <li><a href="/{page_name}/">{page_name}</a></li>')

    items.extend([
        '      <li><a href="https://hocbigg.github.io/CONTRIBUTING.html">Contributing</a></li>',
        '      <li><a href="https://github.com/hocbigg/" target="_blank" rel="noopener noreferrer">GitHub<span class="sr-only"> (opens in new tab)</span></a></li>'
    ])
    return "    <ul>\n" + "\n".join(items) + "\n    </ul>"


# ==============================================================================
# MAIN BUILD PIPELINE
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Build static site for GitHub Pages.")
    parser.add_argument("page", help="Repo folder name or '.' / 'root' for user page (hocbigg.github.io)")
    args = parser.parse_args()

    page_arg = args.page.strip("/").strip()
    
    # 1. Phân biệt kiểu trang: Root domain (hocbigg.github.io) hay Project con
    is_root = page_arg in [".", "", "root", "hocbigg.github.io", "01_homepage"]

    # 2. Tách biệt logic: ROOT luôn trỏ đúng vào thư mục cần build
    if page_arg in [".", ""]:
        ROOT = Path.cwd()
    else:
        ROOT = Path.cwd() / page_arg

    # 3. BASE_URL và BASE_PREFIX chỉ dùng để phục vụ SEO & liên kết
    if is_root:
        BASE_URL = "https://hocbigg.github.io/"
        BASE_PREFIX = "/"
    else:
        BASE_URL = f"https://hocbigg.github.io/{page_arg}/"
        BASE_PREFIX = f"/{page_arg}/"

    OUT = ROOT / "out"
    ASSETS = ROOT / "assets"
    IMAGES = ROOT / "images"

    if not ROOT.exists():
        print(f"[..] Error: Root path '{ROOT}' does not exist.")
        sys.exit(1)

    OUT.mkdir(exist_ok=True, parents=True)

    print(f"[..] Building site: {'(Root Site)' if is_root else page_arg}")
    print(f"[..] Base URL: {BASE_URL}")
    print(f"[..] Output:   {OUT}\n")

    # 1. Copy Assets & Images if present
    if ASSETS.exists():
        shutil.copytree(ASSETS, OUT / "assets", dirs_exist_ok=True)
        print("[x] Copied assets/")

    if IMAGES.exists():
        shutil.copytree(IMAGES, OUT / "images", dirs_exist_ok=True)
        print("[x] Copied images/")

    # 2. Markdown engine setup
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "footnotes", "toc", "sane_lists"],
        output_format="html5"
    )

    nav_html = build_nav(is_root, page_arg)
    generated_urls = []

    # 3. Process Markdown files
    for md_path in ROOT.rglob("*.md"):
        # Ignore output directory & assets
        if OUT in md_path.parents or "assets" in md_path.parts:
            continue

        rel_path = md_path.relative_to(ROOT)
        is_readme = md_path.name.lower() == "readme.md"

        # Determine target HTML path & canonical URL
        if is_readme:
            if rel_path.parent == Path("."):
                out_path = OUT / "index.html"
                page_rel_url = ""
            else:
                out_path = OUT / rel_path.parent / "index.html"
                page_rel_url = rel_path.parent.as_posix() + "/"
        else:
            out_path = (OUT / rel_path).with_suffix(".html")
            page_rel_url = rel_path.with_suffix(".html").as_posix()

        out_path.parent.mkdir(parents=True, exist_ok=True)
        canonical_url = BASE_URL + page_rel_url

        # Parse content
        raw_text = md_path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw_text)

        # Markdown to HTML
        md.reset()
        content_html = md.convert(body)
        content_html = rewrite_internal_md_links(content_html)
        content_html = enhance_external_links(content_html)
        content_html = wrap_tables(content_html)

        # Metadata resolution
        if "title" in meta:
            title = str(meta["title"])
        else:
            h1 = extract_h1(body)
            title = h1 if h1 else md_path.stem.replace("_", " ").replace("-", " ").title()

        description = meta.get("description", "A lightweight static page by hocbigg.")
        author = meta.get("author", "hocbigg")
        language = meta.get("language", "en")

        header_html = (
            PAGE_HEADER_TEMPLATE.format(base_prefix=BASE_PREFIX, title=html.escape(title))
            if is_readme and rel_path.parent == Path(".")
            else ""
        )

        # Render Full Page
        rendered_html = (
            HTML_TEMPLATE
            .replace("{{language}}", html.escape(language))
            .replace("{{title}}", html.escape(title))
            .replace("{{description}}", html.escape(description))
            .replace("{{author}}", html.escape(author))
            .replace("{{canonical_url}}", canonical_url)
            .replace("{{css}}", INLINED_CSS.strip())
            .replace("{{nav_html}}", nav_html)
            .replace("{{header_html}}", header_html)
            .replace("{{content_html}}", content_html)
        )

        out_path.write_text(rendered_html, encoding="utf-8")
        generated_urls.append(canonical_url)
        print(f"[x] Rendered: {rel_path} → {out_path.relative_to(ROOT)}")

    # 4. Generate sitemap.xml
    today = date.today().isoformat()
    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for url in sorted(set(generated_urls)):
        sitemap_lines.append("  <url>")
        sitemap_lines.append(f"    <loc>{url}</loc>")
        sitemap_lines.append(f"    <lastmod>{today}</lastmod>")
        sitemap_lines.append("  </url>")
    sitemap_lines.append("</urlset>")

    (OUT / "sitemap.xml").write_text("\n".join(sitemap_lines), encoding="utf-8")
    print(f"\n[x] Generated sitemap.xml ({len(generated_urls)} URLs)")

    # 5. Generate robots.txt
    robots_content = f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}sitemap.xml\n"
    (OUT / "robots.txt").write_text(robots_content, encoding="utf-8")
    print("[x] Generated robots.txt")

    print("\nBuild completed successfully!")


if __name__ == "__main__":
    main()