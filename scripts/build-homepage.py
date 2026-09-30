#!/usr/bin/env python3
"""
Static Site Generator for the Root Homepage (hocbigg.github.io) and Curricula index (c/).
Features:
- Standalone single-file build tool for the central homepage repository.
- Context-aware Navigation:
    * Root (README.md, CONTRIBUTING.md) -> [Hocbigg] | [Contributing] | [GitHub]
    * Curricula (c/<name>/index.md)     -> [Hocbigg] | [Curriculum Name] | [GitHub]
- Page Header (Logo + H1 + Last updated on) displayed exclusively for c/.../index.html.
- Inlined CSS, Semantic HTML & Accessibility (A11y) optimized.
- Dynamic canonical URLs, OpenGraph tags, sitemap.xml & robots.txt.
"""

import argparse
import html
import re
import shutil
import sys
from datetime import datetime, date
from pathlib import Path
import markdown
import yaml

# ==============================================================================
# INLINED STYLESHEET (Dán nội dung CSS của bạn vào đây)
# ==============================================================================
INLINED_CSS = """
:root {
  color-scheme: light dark;

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

body {
  margin: 1.5rem auto;
  max-width: 60rem;
  padding: 0 1rem 3.5rem;
  background-color: var(--bg);
  color: var(--fg);
  font: 1.15rem/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  
  /* Cú pháp hiện đại thay thế cho word-wrap */
  overflow-wrap: break-word;
}

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

nav .nav-brand {
  color: var(--fg);
  font-weight: 700;
  margin-right: 0.5rem;
}

.skip-link {
  position: absolute;
  transform: translateY(-150%);
  left: 1rem;
  background: var(--fg);
  color: var(--bg);
  padding: 0.5rem 1rem;
  z-index: 100;
  text-decoration: none;
  font-weight: 600;
  border-radius: 4px;
  transition: transform 0.2s ease;
}

.skip-link:focus {
  transform: translateY(1rem);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}

:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 3px;
}

h1, h2, h3, h4, h5, h6 {
  line-height: 1.3;
  margin-top: 2rem;
  margin-bottom: 1rem;
  color: var(--fg);
  font-weight: 600;
}

h1 {
  font-size: 2.5rem;
  margin-top: 0;
}

h2 {
  font-size: 2rem;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--border);
}

h3 {
  font-size: 1.5rem;
}

h4 {
  font-size: 1.25rem;
}

h5 {
  font-size: 1.15rem;
}

h6 {
  font-size: 1rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

p, ul, ol, blockquote, table {
  margin-top: 0;
  margin-bottom: 1.25rem;
}

li > ul,
li > ol {
  margin-top: 0.25rem;
  margin-bottom: 0;
}

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

a:has(img) {
  text-decoration: none;
}

.page-header {
  text-align: center;
  margin-bottom: 2rem;
}

img {
  max-width: 100%;
  height: auto;
}

.page-header img {
  margin: 0 auto 1rem;
  display: block;
}

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
  border-radius: 0;
}

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

blockquote {
  margin-inline: 0;
  border-left: 4px solid var(--border);
  padding-left: 1rem;
  color: var(--muted);
  font-style: italic;
}

@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
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
# HTML BASE TEMPLATES
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
  <img src="/images/logo.png" alt="Hocbigg logo">
  <h1>{title}</h1>
  <p class="last-updated"><small>Last updated on: <time datetime="{date_iso}">{date_iso}</time></small></p>
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

    html_text = re.sub(r'<a\s+([^>]*?)href="(https?://[^"]+)"', repl, html_text)
    return html_text


def wrap_tables(html_text: str) -> str:
    """Wrap <table> in responsive div with tabindex for keyboard a11y scroll."""
    return re.sub(
        r'(<table>[\s\S]*?</table>)',
        r'<div class="table-wrapper" tabindex="0" role="region" aria-label="Scrollable table">\1</div>',
        html_text
    )


def build_nav_for_page(rel_path: Path) -> str:
    """
    Sinh Navbar theo ngữ cảnh:
    - Nếu thuộc c/<curriculum>/... : [Hocbigg] | [Tên Curriculum] | [GitHub]
    - Nếu thuộc Root             : [Hocbigg] | [Contributing]     | [GitHub]
    """
    items = [
        '      <li><a href="https://hocbigg.github.io/" class="nav-brand">Hocbigg</a></li>'
    ]

    # Kiểm tra nếu file nằm trong thư mục c/
    if len(rel_path.parts) >= 2 and rel_path.parts[0] == "c":
        curriculum_slug = rel_path.parts[1]
        curriculum_title = curriculum_slug.replace("-", " ").replace("_", " ").title()
        items.append(f'      <li><a href="/c/{curriculum_slug}/">{curriculum_title}</a></li>')
    else:
        # Các trang gốc: README.md, CONTRIBUTING.md
        items.append('      <li><a href="/CONTRIBUTING.html">Contributing</a></li>')

    # GitHub link về tổ chức Hocbigg
    items.append(
        '      <li><a href="https://github.com/hocbigg" target="_blank" rel="noopener noreferrer">GitHub<span class="sr-only"> (opens in new tab)</span></a></li>'
    )

    return "    <ul>\n" + "\n".join(items) + "\n    </ul>"


# ==============================================================================
# MAIN PIPELINE
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Build Homepage and collection pages for GitHub Pages.")
    parser.add_argument("homepage_dir", help="Directory of the homepage repository (e.g. 01_homepage)")
    args = parser.parse_args()

    page_arg = args.homepage_dir.strip("/").strip()
    ROOT = Path.cwd() / page_arg if not Path(page_arg).is_absolute() else Path(page_arg)

    if not ROOT.exists() or not ROOT.is_dir():
        print(f"[..] Error: Homepage directory '{ROOT}' does not exist.")
        sys.exit(1)

    BASE_URL = "https://hocbigg.github.io/"
    OUT = ROOT / "out"
    ASSETS = ROOT / "assets"
    IMAGES = ROOT / "images"

    OUT.mkdir(exist_ok=True, parents=True)

    print(f"[..] Building Homepage: {page_arg}")
    print(f"[..] Base URL:          {BASE_URL}")
    print(f"[..] Output directory:  {OUT}\n")

    # 1. Copy Assets, Images & 404.html
    if ASSETS.exists():
        shutil.copytree(ASSETS, OUT / "assets", dirs_exist_ok=True)
        print("[x] Copied assets/")

    if IMAGES.exists():
        shutil.copytree(IMAGES, OUT / "images", dirs_exist_ok=True)
        print("[x] Copied images/")

    # Tự động phát hiện và đưa 404.html vào out/
    NOT_FOUND_FILE = ROOT / "404.html"
    if NOT_FOUND_FILE.exists():
        shutil.copy2(NOT_FOUND_FILE, OUT / "404.html")
        print("[x] Copied 404.html")

    # 2. Markdown engine setup
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "footnotes", "toc", "sane_lists"],
        output_format="html5"
    )

    generated_urls = []

    # 3. Process Markdown files
    for md_path in ROOT.rglob("*.md"):
        if OUT in md_path.parents or "assets" in md_path.parts:
            continue

        rel_path = md_path.relative_to(ROOT)
        is_index = md_path.name.lower() in ["readme.md", "index.md"]

        # Định tuyến đường dẫn output và URL canonical
        if is_index:
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

        raw_text = md_path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw_text)

        md.reset()
        content_html = md.convert(body)
        content_html = rewrite_internal_md_links(content_html)
        content_html = enhance_external_links(content_html)
        content_html = wrap_tables(content_html)

        if "title" in meta:
            title = str(meta["title"])
        else:
            h1 = extract_h1(body)
            title = h1 if h1 else md_path.stem.replace("_", " ").replace("-", " ").title()

        description = meta.get("description", "A lightweight static page by hocbigg.")
        author = meta.get("author", "hocbigg")
        language = meta.get("language", "en")

        # Quy tắc hiển thị Header:
        # CHỈ hiển thị Logo + H1 + Last updated on ở các trang index.md trong thư mục c/
        is_curriculum_index = (len(rel_path.parts) >= 2 and rel_path.parts[0] == "c" and is_index)

        if is_curriculum_index:
            file_mtime = datetime.fromtimestamp(md_path.stat().st_mtime).strftime("%Y-%m-%d")
            header_html = PAGE_HEADER_TEMPLATE.format(
                title=html.escape(title),
                date_iso=file_mtime
            )
        else:
            header_html = ""

        nav_html = build_nav_for_page(rel_path)

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

    print("\nHomepage build completed successfully!")


if __name__ == "__main__":
    main()


