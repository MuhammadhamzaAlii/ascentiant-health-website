#!/usr/bin/env python3
"""Apply SEO audit fixes 1-6: canonicals, sitemap, links, titles, article schema."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://ascentiant.health"
OG_IMAGE = f"{BASE}/Images/ascentiant-health-logo.png"
OLD_BASES = (
    "https://www.ascentiant.health",
    "http://www.ascentiant.health",
    "https://ascentiant.health",  # normalize .html forms too
)

TITLE_REPLACEMENTS = {
    "Home Health Revenue Cycle Management | Home Health Medical Billing | Ascentiant Health":
        "Home Health Revenue Cycle Management | Ascentiant Health",
    "Physical Therapy Revenue Cycle Management | Physical Therapy Medical Billing | Ascentiant Health":
        "Physical Therapy Revenue Cycle Management | Ascentiant Health",
    "Primary Care Revenue Cycle Management | Internal Medicine Medical Billing | Ascentiant Health":
        "Primary Care Revenue Cycle Management | Ascentiant Health",
    "Behavioral Health Revenue Cycle Management | Mental Health Medical Billing | Ascentiant Health":
        "Behavioral Health Revenue Cycle Management | Ascentiant Health",
    "Laboratory Revenue Cycle Management | Clinical Laboratory Billing | Ascentiant Health":
        "Laboratory Revenue Cycle Management | Ascentiant Health",
    "Multi-Specialty Revenue Cycle Management | Physician Practice Medical Billing | Ascentiant Health":
        "Multi-Specialty Revenue Cycle Management | Ascentiant Health",
    "Ambulatory Surgery Center Revenue Cycle Management | ASC Medical Billing | Ascentiant Health":
        "ASC Revenue Cycle Management | Ascentiant Health",
    "Healthcare Revenue Cycle Management | Medical Billing Services | Ascentiant Health":
        "Healthcare Revenue Cycle Management | Ascentiant Health",
    "Ascentiant Health Platform | One Intelligent Revenue Cycle Platform":
        "Revenue Cycle Platform Software | Ascentiant Health",
    "Ascentiant Health | Revenue Cycle Management & Operations Platform":
        "Ascentiant Health | Revenue Cycle Management",
    "Denial Management Best Practices | Ascentiant Health Resources":
        "Denial Management Best Practices | Ascentiant Health",
    "RCM KPIs Every Leader Should Track | Ascentiant Health Resources":
        "RCM KPIs Every Leader Should Track | Ascentiant Health",
    "Physical Therapy Billing Update 2026 | Ascentiant Health Resources":
        "Physical Therapy Billing Update 2026 | Ascentiant Health",
    "No Surprises Act Overview for Providers | Ascentiant Health Resources":
        "No Surprises Act for Providers | Ascentiant Health",
    "Medical Billing Guide for Practices | Ascentiant Health Resources":
        "Medical Billing Guide for Practices | Ascentiant Health",
    "Home Health Billing Update 2026 | Ascentiant Health Resources":
        "Home Health Billing Update 2026 | Ascentiant Health",
    "Provider Credentialing Guide | Ascentiant Health Resources":
        "Provider Credentialing Guide | Ascentiant Health",
    "Revenue Recovery Strategies | Ascentiant Health Resources":
        "Revenue Recovery Strategies | Ascentiant Health",
}

ARTICLE_META = {
    "credentialing-guide.html": {
        "headline": "Provider Credentialing Guide",
        "published": "2026-07-11",
    },
    "denial-management.html": {
        "headline": "Denial Management Best Practices",
        "published": "2026-07-11",
    },
    "home-health-billing-update.html": {
        "headline": "Home Health Billing Update 2026",
        "published": "2026-07-11",
    },
    "medical-billing-guide.html": {
        "headline": "Medical Billing Guide for Practices",
        "published": "2026-07-11",
    },
    "no-surprises-act.html": {
        "headline": "No Surprises Act Overview for Providers",
        "published": "2026-07-11",
    },
    "physical-therapy-billing-update.html": {
        "headline": "Physical Therapy Billing Update 2026",
        "published": "2026-07-11",
    },
    "rcm-kpis.html": {
        "headline": "RCM KPIs Every Leader Should Track",
        "published": "2026-07-11",
    },
    "revenue-recovery.html": {
        "headline": "Revenue Recovery Strategies",
        "published": "2026-07-11",
    },
}

SKIP_LINK_PREFIXES = ("mailto:", "tel:", "javascript:", "#", "data:")
ASSET_EXTS = (".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".ico", ".pdf", ".xml", ".txt")


def clean_public_path(path: str) -> str:
    path = path.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if path in ("", "index.html", "/index.html"):
        return "/"
    if path.startswith("/"):
        path = path[1:]
    if path.endswith(".html"):
        path = path[:-5]
    if path.endswith("/index"):
        path = path[: -len("/index")] or ""
    return "/" if path in ("", "/") else f"/{path}"


def public_url_from_rel(rel_path: str) -> str:
    return BASE + clean_public_path(rel_path)


def normalize_absolute_ascentiant(url: str) -> str:
    parts = urlsplit(url)
    if "ascentiant.health" not in parts.netloc:
        return url
    path = clean_public_path(parts.path or "/")
    return urlunsplit(("https", "ascentiant.health", path, parts.query, parts.fragment))


def resolve_page_href(href: str, current_rel: str) -> str:
    if not href or href.startswith(SKIP_LINK_PREFIXES):
        return href
    if href.startswith("http://") or href.startswith("https://"):
        if "ascentiant.health" in href:
            return normalize_absolute_ascentiant(href)
        return href

    parts = urlsplit(href)
    path = parts.path
    if not path:
        return href

    lower = path.lower()
    if lower.endswith(ASSET_EXTS) or "/Images/" in path or path.endswith("/Images"):
        return href
    if "dashboard-preview" in path:
        # keep preview as .html file for iframe
        return href

    # Root-relative site links stay root-relative. Only resolve true relative paths.
    current_dir = Path(current_rel).parent
    if path.startswith("/"):
        resolved = path.lstrip("/")
        if resolved.endswith(ASSET_EXTS) or resolved.startswith("Images/"):
            return href
        clean = clean_public_path(resolved)
        query = f"?{parts.query}" if parts.query else ""
        frag = f"#{parts.fragment}" if parts.fragment else ""
        return f"{clean}{query}{frag}"
    else:
        resolved = (current_dir / path).as_posix()
        while "/../" in resolved:
            resolved = re.sub(r"[^/]+/\.\./", "", resolved)
        resolved = resolved.replace("./", "")

    clean = clean_public_path(resolved)
    query = f"?{parts.query}" if parts.query else ""
    frag = f"#{parts.fragment}" if parts.fragment else ""
    return f"{clean}{query}{frag}"


def rewrite_hrefs(html: str, current_rel: str) -> str:
    def repl(match: re.Match) -> str:
        quote = match.group(1)
        href = match.group(2)
        new_href = resolve_page_href(href, current_rel)
        return f"href={quote}{new_href}{quote}"

    return re.sub(r'href=(["\'])([^"\']+)\1', repl, html)


def strip_html_from_known_urls(text: str) -> str:
    # Convert absolute ascentiant URLs with .html to clean form
    def repl(m: re.Match) -> str:
        return normalize_absolute_ascentiant(m.group(0))

    return re.sub(
        r"https?://(?:www\.)?ascentiant\.health[^\s\"'<>]*",
        repl,
        text,
    )


def apply_title_replacements(html: str) -> str:
    for old, new in TITLE_REPLACEMENTS.items():
        html = html.replace(old, new)
        html = html.replace(old.replace("&", "&amp;"), new.replace("&", "&amp;"))
    return html


def enrich_article_schema(html: str, filename: str, public_url: str, description: str) -> str:
    meta = ARTICLE_META.get(filename)
    if not meta:
        return html
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta["headline"],
        "description": description,
        "image": [OG_IMAGE],
        "datePublished": meta["published"],
        "dateModified": modified,
        "author": {"@type": "Organization", "name": "Ascentiant Health", "url": BASE},
        "publisher": {
            "@type": "Organization",
            "name": "Ascentiant Health",
            "url": BASE,
            "logo": {"@type": "ImageObject", "url": OG_IMAGE},
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": public_url,
        },
        "url": public_url,
    }
    block = (
        '  <script type="application/ld+json">'
        + json.dumps(data, separators=(",", ":"))
        + "</script>"
    )
    # Replace existing compact or pretty Article schema blocks
    pattern = re.compile(
        r'  <script type="application/ld\+json">\s*\{[^{}]*"@type"\s*:\s*"Article".*?</script>',
        re.S,
    )
    if pattern.search(html):
        return pattern.sub(lambda _m: block, html, count=1)
    # Fallback: insert before </head>
    return html.replace("</head>", block + "\n</head>", 1)


def extract_description(html: str) -> str:
    m = re.search(r'<meta name="description" content="([^"]*)"', html, re.I)
    return m.group(1) if m else ""


def process_html(path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("scripts/"):
        return
    html = path.read_text(encoding="utf-8")
    original = html

    # Absolute URL normalization (canonical, og, schema, twitter, etc.)
    html = strip_html_from_known_urls(html)
    html = html.replace("https://www.ascentiant.health", BASE)
    html = html.replace("http://www.ascentiant.health", BASE)

    # Explicitly set canonical to correct public URL when present
    public_url = public_url_from_rel(rel)
    html = re.sub(
        r'(<link rel="canonical" href=")[^"]*(">)',
        rf"\1{public_url}\2",
        html,
        count=1,
    )
    html = re.sub(
        r'(<meta property="og:url" content=")[^"]*(">)',
        rf"\1{public_url}\2",
        html,
        count=1,
    )

    html = rewrite_hrefs(html, rel)
    html = apply_title_replacements(html)

    # Sync og:title / twitter:title if title changed in TITLE_REPLACEMENTS
    m_title = re.search(r"<title>([^<]+)</title>", html, re.I)
    if m_title:
        title = m_title.group(1)
        html = re.sub(
            r'(<meta property="og:title" content=")[^"]*(">)',
            rf"\1{title}\2",
            html,
            count=1,
        )
        html = re.sub(
            r'(<meta name="twitter:title" content=")[^"]*(">)',
            rf"\1{title}\2",
            html,
            count=1,
        )

    if rel.startswith("resources/articles/"):
        html = enrich_article_schema(
            html,
            Path(rel).name,
            public_url,
            extract_description(html),
        )

    if html != original:
        path.write_text(html, encoding="utf-8")
        print(f"OK {rel}")
    else:
        print(f"-- {rel}")


def write_sitemap() -> None:
    pages = [
        ("/", "weekly", "1.0"),
        ("/rcm", "monthly", "0.9"),
        ("/platform", "monthly", "0.9"),
        ("/credentialing", "monthly", "0.8"),
        ("/ai-intelligence", "monthly", "0.8"),
        ("/why-ascentiant", "monthly", "0.8"),
        ("/about", "monthly", "0.7"),
        ("/contact", "monthly", "0.9"),
        ("/industries", "monthly", "0.8"),
        ("/resources", "weekly", "0.7"),
        ("/case-studies", "monthly", "0.8"),
        ("/how-we-transition", "monthly", "0.8"),
        ("/privacy", "yearly", "0.3"),
        ("/terms", "yearly", "0.3"),
        ("/thank-you", "yearly", "0.2"),
        ("/case-studies/home-health", "monthly", "0.7"),
        ("/case-studies/physical-therapy", "monthly", "0.7"),
        ("/case-studies/physician-practice", "monthly", "0.7"),
        ("/case-studies/laboratory", "monthly", "0.7"),
        ("/resources/articles/denial-management", "monthly", "0.6"),
        ("/resources/articles/rcm-kpis", "monthly", "0.6"),
        ("/resources/articles/medical-billing-guide", "monthly", "0.6"),
        ("/resources/articles/credentialing-guide", "monthly", "0.6"),
        ("/resources/articles/revenue-recovery", "monthly", "0.6"),
        ("/resources/articles/home-health-billing-update", "monthly", "0.6"),
        ("/resources/articles/physical-therapy-billing-update", "monthly", "0.6"),
        ("/resources/articles/no-surprises-act", "monthly", "0.6"),
        ("/industries/home-health-revenue-cycle-management", "monthly", "0.8"),
        ("/industries/physical-therapy-revenue-cycle-management", "monthly", "0.8"),
        ("/industries/primary-care-internal-medicine-revenue-cycle-management", "monthly", "0.8"),
        ("/industries/behavioral-health-revenue-cycle-management", "monthly", "0.8"),
        ("/industries/laboratory-revenue-cycle-management", "monthly", "0.8"),
        ("/industries/multi-specialty-physician-practice-revenue-cycle-management", "monthly", "0.8"),
        ("/industries/ambulatory-surgery-center-revenue-cycle-management", "monthly", "0.8"),
        ("/industries/other-healthcare-organizations-revenue-cycle-management", "monthly", "0.7"),
    ]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, freq, pri in pages:
        loc = f"{BASE}/" if path == "/" else f"{BASE}{path}"
        lines.append(
            f"  <url><loc>{loc}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority></url>"
        )
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("OK sitemap.xml")


def write_robots() -> None:
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: https://ascentiant.health/sitemap.xml\n",
        encoding="utf-8",
    )
    print("OK robots.txt")


def patch_scripts() -> None:
    for name in ("enhance_seo.py", "build_industries.py", "industry_content.py"):
        path = ROOT / "scripts" / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        new = text.replace("https://www.ascentiant.health", BASE)
        # Fix canonical helper to strip .html
        if name == "enhance_seo.py":
            new = new.replace(
                'BASE = "https://www.ascentiant.health"',
                f'BASE = "{BASE}"',
            )
            if "def canonical_url" in new:
                new = re.sub(
                    r"def canonical_url\(rel_path: str\) -> str:.*?return f\"\{BASE\}/\{p\}\"",
                    f'''def canonical_url(rel_path: str) -> str:
    p = rel_path.replace("\\\\", "/")
    if p == "index.html":
        return f"{{BASE}}/"
    if p.endswith(".html"):
        p = p[:-5]
    return f"{{BASE}}/{{p}}"''',
                    new,
                    count=1,
                    flags=re.S,
                )
        if new != text:
            path.write_text(new, encoding="utf-8")
            print(f"OK scripts/{name}")


def main() -> None:
    for path in sorted(ROOT.rglob("*.html")):
        process_html(path)
    write_sitemap()
    write_robots()
    patch_scripts()
    print("Done.")


if __name__ == "__main__":
    main()
