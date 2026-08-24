#!/usr/bin/env python3
"""Batch SEO enhancements for Ascentiant Health static site."""
import json
import re
from pathlib import Path
from typing import Optional, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://ascentiant.health"
SITE_NAME = "Ascentiant Health"
OG_IMAGE = f"{BASE}/Images/ascentiant-health-logo.png"

# Optional overrides for unique descriptions
META_OVERRIDES = {
    "thank-you.html": {
        "title": "Thank You | Ascentiant Health",
        "description": "Thank you for contacting Ascentiant Health. We will respond within one business day.",
    },
    "404.html": {
        "title": "Page Not Found | Ascentiant Health",
        "description": "The page you requested was not found. Return to Ascentiant Health for revenue cycle management resources.",
    },
}


def depth_prefix(rel_path: str) -> str:
    parts = Path(rel_path).parts
    if len(parts) <= 1:
        return ""
    return "../" * (len(parts) - 1)


def canonical_url(rel_path: str) -> str:
    p = rel_path.replace("\\", "/")
    if p == "index.html":
        return f"{BASE}/"
    if p.endswith(".html"):
        p = p[:-5]
    return f"{BASE}/{p}"


def favicon_block(prefix: str) -> str:
    return f"""  <link rel="icon" href="{prefix}Images/ascentiant-health-logo.png" type="image/png">
  <link rel="apple-touch-icon" href="{prefix}Images/ascentiant-health-logo.png">"""


def social_block(title: str, description: str, url: str) -> str:
    t = title.replace('"', "&quot;")
    d = description.replace('"', "&quot;")
    return f"""  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:title" content="{t}">
  <meta property="og:description" content="{d}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t}">
  <meta name="twitter:description" content="{d}">
  <meta name="twitter:image" content="{OG_IMAGE}">"""


def website_schema() -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": BASE,
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": BASE},
    }
    return f'  <script type="application/ld+json">\n{json.dumps(data, indent=2)}\n  </script>'


def breadcrumb_schema(items: list) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": url,
            }
            for i, (name, url) in enumerate(items)
        ],
    }
    return f'  <script type="application/ld+json">\n{json.dumps(data, indent=2)}\n  </script>'


def faq_schema(items: List[Tuple[str, str]]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in items
        ],
    }
    return f'  <script type="application/ld+json">\n{json.dumps(data, indent=2)}\n  </script>'


def parse_faq_items(html: str) -> List[Tuple[str, str]]:
    items = []
    for m in re.finditer(
        r'class="faq-q"[^>]*>([^<]+)</button>\s*<div class="faq-a">(.*?)</div>',
        html,
        re.S,
    ):
        q = re.sub(r"^\+\s*", "", m.group(1).strip())
        a = re.sub(r"<[^>]+>", " ", m.group(2))
        a = re.sub(r"\s+", " ", a).strip()
        if q and a:
            items.append((q, a))
    return items


def article_schema(title: str, description: str, url: str) -> str:
    headline = title.split("|")[0].strip()
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "description": description,
        "url": url,
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "logo": {"@type": "ImageObject", "url": OG_IMAGE},
        },
    }
    return f'  <script type="application/ld+json">\n{json.dumps(data, indent=2)}\n  </script>'


def service_schema(name: str, description: str, url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": name,
        "description": description,
        "url": url,
        "provider": {"@type": "Organization", "name": SITE_NAME, "url": BASE},
        "areaServed": "US",
        "serviceType": "Healthcare Revenue Cycle Management",
    }
    return f'  <script type="application/ld+json">\n{json.dumps(data, indent=2)}\n  </script>'


def contact_page_schema(description: str, url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "ContactPage",
        "name": "Contact Ascentiant Health",
        "description": description,
        "url": url,
        "mainEntity": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": BASE,
            "telephone": "+1-855-313-8197",
            "email": "info@ascentiant.health",
        },
    }
    return f'  <script type="application/ld+json">\n{json.dumps(data, indent=2)}\n  </script>'


def has_schema_type(html: str, schema_type: str) -> bool:
    return f'"@type": "{schema_type}"' in html or f'"@type":"{schema_type}"' in html


def service_name_from_title(title: str) -> str:
    return title.split("|")[0].strip()


def parse_breadcrumb(html: str, prefix: str) -> Optional[List[Tuple[str, str]]]:
    # Case studies use <nav class="breadcrumb">; articles use <p class="breadcrumb">.
    # Never read past the breadcrumb element or hero copy leaks into schema names.
    m = re.search(r'<(?:nav|p)\s[^>]*class="breadcrumb"[^>]*>(.*?)</(?:nav|p)>', html, re.S | re.I)
    if not m:
        m = re.search(r'class="breadcrumb"[^>]*>(.*?)</(?:nav|p)>', html, re.S | re.I)
    if not m:
        return None
    inner = m.group(1)
    links = re.findall(r'<a href="([^"]+)">([^<]+)</a>', inner)
    if not links:
        return None
    items = []
    for href, name in links:
        label = re.sub(r"\s+", " ", name).strip()
        if href.startswith("http"):
            items.append((label, href))
        elif href.startswith("/"):
            items.append((label, BASE + href))
        else:
            clean = href.replace("../", "")
            items.append((label, f"{BASE}/{clean}" if clean != "index.html" else f"{BASE}/"))
    visible = re.sub(r"<[^>]+>", " ", inner)
    parts = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"&rsaquo;|›", visible) if p.strip()]
    if parts:
        last = parts[-1]
        if len(last) > 80:
            last = last[:80].rsplit(" ", 1)[0]
        if last and (not items or items[-1][0] != last):
            items.append((last, f"{BASE}/{prefix}" if prefix else BASE))
    return items if items else None


def extract_title_desc(html: str, key: str) -> str:
    if key == "title":
        m = re.search(r"<title>([^<]+)</title>", html, re.I)
    else:
        m = re.search(r'<meta name="description" content="([^"]*)"', html, re.I)
    return m.group(1).strip() if m else ""


def remove_existing_seo(html: str) -> str:
    html = re.sub(r'\n  <link rel="canonical"[^>]+>', "", html)
    html = re.sub(r'\n  <meta property="og:[^"]+"[^>]+>', "", html)
    html = re.sub(r'\n  <meta name="twitter:[^"]+"[^>]+>', "", html)
    html = re.sub(r'\n  <link rel="icon"[^>]+>', "", html)
    html = re.sub(r'\n  <link rel="apple-touch-icon"[^>]+>', "", html)
    return html


def inject_after_title(html: str, block: str) -> str:
    if "rel=\"canonical\"" in html:
        html = remove_existing_seo(html)
    return re.sub(r"(</title>)", r"\1\n" + block, html, count=1)


def inject_before_head_close(html: str, block: str) -> str:
    if block.strip() in html:
        return html
    return html.replace("</head>", block + "\n</head>", 1)


def add_conversions_script(html: str, prefix: str) -> str:
    src = f'{prefix}js/conversions.js'
    if "conversions.js" in html:
        return html
    return html.replace(
        f'<script src="{prefix}js/main.js"></script>',
        f'<script src="{prefix}js/main.js"></script>\n<script src="{src}"></script>',
    )


def process_file(path: Path) -> None:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    if rel.startswith("scripts/") or rel.startswith("downloads/") or rel == "platform/dashboard-preview.html":
        # Still fix emails in downloads if any; skip full SEO for printables
        if "downloads/" in rel:
            text = path.read_text(encoding="utf-8")
            text = text.replace("mailto:info.health", "mailto:info@ascentiant.health")
            text = text.replace(">info.health<", ">info@ascentiant.health<")
            path.write_text(text, encoding="utf-8")
        return

    html = path.read_text(encoding="utf-8")
    html = html.replace("mailto:info.health", "mailto:info@ascentiant.health")
    html = html.replace(">info.health<", ">info@ascentiant.health<")

    prefix = depth_prefix(rel)
    key = Path(rel).name
    title = META_OVERRIDES.get(key, {}).get("title") or extract_title_desc(html, "title")
    desc = META_OVERRIDES.get(key, {}).get("description") or extract_title_desc(html, "description")
    if not title:
        title = SITE_NAME
    if not desc:
        desc = f"{SITE_NAME} — technology-enabled revenue cycle management for healthcare providers."

    url = canonical_url(rel)
    block = favicon_block(prefix) + "\n" + social_block(title, desc, url)
    html = inject_after_title(html, block)

    if key == "index.html" and not has_schema_type(html, "WebSite"):
        html = inject_before_head_close(html, "\n" + website_schema() + "\n")

    crumbs = parse_breadcrumb(html, prefix)
    if crumbs:
        # fix last item URL to current page
        crumbs[-1] = (crumbs[-1][0], url)
        schema = breadcrumb_schema(crumbs)
        html = re.sub(
            r'  <script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "BreadcrumbList"[\s\S]*?</script>\n',
            "",
            html,
        )
        html = inject_before_head_close(html, "\n" + schema + "\n")

    faq_items = parse_faq_items(html)
    if faq_items and not has_schema_type(html, "FAQPage"):
        html = inject_before_head_close(html, "\n" + faq_schema(faq_items) + "\n")

    if rel.startswith("case-studies/") and rel != "case-studies.html" and not has_schema_type(html, "Article"):
        html = inject_before_head_close(html, "\n" + article_schema(title, desc, url) + "\n")

    if rel.startswith("industries/") and not has_schema_type(html, "Service"):
        html = inject_before_head_close(html, "\n" + service_schema(service_name_from_title(title), desc, url) + "\n")

    if key == "contact.html" and not has_schema_type(html, "ContactPage"):
        html = inject_before_head_close(html, "\n" + contact_page_schema(desc, url) + "\n")

    if key == "ai-intelligence.html" and not has_schema_type(html, "Service"):
        html = inject_before_head_close(html, "\n" + service_schema("AI Revenue Intelligence", desc, url) + "\n")

    html = add_conversions_script(html, prefix)
    path.write_text(html, encoding="utf-8")
    print(f"OK {rel}")


def main():
    for path in sorted(ROOT.rglob("*.html")):
        process_file(path)
    print("Done.")


if __name__ == "__main__":
    main()
