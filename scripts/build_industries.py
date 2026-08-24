#!/usr/bin/env python3
"""Generate industry pages, update navigation dropdown, and refresh hub pages."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Optional

from industry_content import INDUSTRIES, NAV_ITEMS, OLD_INDUSTRY_FILES

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://ascentiant.health"
SITE_NAME = "Ascentiant Health"
OG_IMAGE = f"{BASE}/Images/ascentiant-health-logo.png"

INDUSTRIES_LINK_RE = re.compile(
    r'<a href="(?:(?:\.\./)*)industries\.html"(?: class="active")?>Industries</a>'
    r'|<a class="active" href="(?:(?:\.\./)*)industries\.html">Industries</a>',
    re.IGNORECASE,
)

NAV_DROPDOWN_RE = re.compile(
    r'<div class="nav-dropdown[^"]*">.*?</div>\s*</div>',
    re.DOTALL,
)

SITE_NAV_RE = re.compile(
    r'(<nav class="site-nav" aria-label="Primary">)(.*?)(</nav>)',
    re.DOTALL,
)


def depth_prefix(rel_path: str) -> str:
    parts = Path(rel_path).parts
    if len(parts) <= 1:
        return ""
    return "../" * (len(parts) - 1)


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def nav_dropdown_html(prefix: str, active_slug: Optional[str] = None, hub_active: bool = False) -> str:
    active_class = " nav-dropdown--active" if hub_active or active_slug else ""
    lines = [
        f'      <div class="nav-dropdown{active_class}">',
        '        <button class="nav-dropdown-toggle" type="button" aria-expanded="false" aria-haspopup="true">',
        '          Industries <span class="nav-chevron" aria-hidden="true">▼</span>',
        "        </button>",
        '        <div class="nav-dropdown-menu" role="menu">',
    ]
    for label, slug in NAV_ITEMS:
        item_active = ' class="active"' if active_slug == slug else ""
        lines.append(
            f'          <a href="{prefix}industries/{slug}.html" role="menuitem"{item_active}>{esc(label)}</a>'
        )
    lines.extend(
        [
            f'          <a href="{prefix}industries.html" role="menuitem" class="nav-dropdown-all">View All Industries</a>',
            "        </div>",
            "      </div>",
        ]
    )
    return "\n".join(lines)


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


def breadcrumb_schema(short_name: str, page_url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Industries", "item": f"{BASE}/industries.html"},
            {"@type": "ListItem", "position": 3, "name": short_name, "item": page_url},
        ],
    }
    return f'  <script type="application/ld+json">\n{json.dumps(data, indent=2)}\n  </script>'


def faq_schema(faqs: list[tuple[str, str]]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }
    return f'  <script type="application/ld+json">\n{json.dumps(data, indent=2)}\n  </script>'


def render_section(section: dict, alt: bool) -> str:
    cls = ' class="alt"' if alt else ""
    parts = [f'  <section{cls}>', "    <div class=\"container\">", "      <div class=\"section-head\">"]
    if section.get("label"):
        parts.append(f'        <span class="section-label">{esc(section["label"])}</span>')
    parts.append(f"        <h2>{esc(section['h2'])}</h2>")
    for para in section["paragraphs"]:
        parts.append(f"        <p>{esc(para)}</p>")
    parts.append("      </div>")
    if section.get("bullets"):
        parts.append('      <ul class="feature-list">')
        for item in section["bullets"]:
            parts.append(f"        <li>{esc(item)}</li>")
        parts.append("      </ul>")
    parts.extend(["    </div>", "  </section>"])
    return "\n".join(parts)


def render_industry_page(ind: dict) -> str:
    slug = ind["slug"]
    prefix = "../"
    page_url = f"{BASE}/industries/{slug}.html"
    title = ind["title"]
    meta = ind["meta_description"]
    short = ind["short_name"]

    head = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(meta)}">
  <title>{esc(title)}</title>
  <link rel="icon" href="{prefix}Images/ascentiant-health-logo.png" type="image/png">
  <link rel="apple-touch-icon" href="{prefix}Images/ascentiant-health-logo.png">
  <link rel="canonical" href="{page_url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(meta)}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(meta)}">
  <meta name="twitter:image" content="{OG_IMAGE}">
  <link rel="stylesheet" href="{prefix}css/styles.css">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-FFGJZQC62N"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-FFGJZQC62N');
  </script>
{service_schema(ind['h1'], meta, page_url)}

{breadcrumb_schema(short, page_url)}

{faq_schema(ind['faqs'])}
</head>
<body>

<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{prefix}index.html">
      <img src="{prefix}Images/ascentiant-health-logo.png" alt="{SITE_NAME}">
      <div class="brand-tag">An Ascentiant<br>International Company</div>
    </a>
    <button class="nav-toggle" aria-expanded="false" aria-label="Toggle menu">Menu</button>
    <nav class="site-nav" aria-label="Primary">
      <a href="{prefix}rcm.html">RCM</a>
      <a href="{prefix}platform.html">Platform</a>
      <a href="{prefix}credentialing.html">Credentialing</a>
{nav_dropdown_html(prefix, active_slug=slug)}
      <a href="{prefix}resources.html">Resources</a>
      <a href="{prefix}case-studies.html">Case Studies</a>
      <a href="{prefix}about.html">About</a>
      <a href="{prefix}contact.html">Contact</a>
      <a class="btn btn-primary header-cta" href="{prefix}contact.html">Schedule Review</a>
    </nav>
  </div>
</header>

<main>
  <section class="page-hero">
    <div class="container">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <a href="{prefix}index.html">Home</a> &rsaquo; <a href="{prefix}industries.html">Industries</a> &rsaquo; {esc(short)}
      </nav>
      <span class="section-label">{esc(short)}</span>
      <h1>{esc(ind['h1'])}</h1>
      <h2 class="hero-subtitle">{esc(ind['hero_h2'])}</h2>
"""
    for para in ind["hero_paragraphs"]:
        head += f"      <p>{esc(para)}</p>\n"
    head += f"""      <a class="btn btn-primary btn-lg" href="{prefix}contact.html?interest={ind['interest']}">Schedule a Revenue Review</a>
    </div>
  </section>
"""

    body = head
    for i, section in enumerate(ind["sections"]):
        body += render_section(section, alt=(i % 2 == 1)) + "\n"

    body += f"""  <section>
    <div class="container">
      <div class="section-head">
        <span class="section-label">Why Ascentiant</span>
        <h2>Why {esc(short)} Choose Ascentiant Health</h2>
      </div>
      <ul class="feature-list">
"""
    for item in ind["why_choose"]:
        body += f"        <li>{esc(item)}</li>\n"
    body += """      </ul>
    </div>
  </section>

  <section class="alt">
    <div class="container">
      <div class="section-head">
        <span class="section-label">FAQ</span>
        <h2>Frequently Asked Questions</h2>
      </div>
      <div style="max-width:720px; margin:0 auto;">
"""
    for q, a in ind["faqs"]:
        body += f"""        <div class="faq-item">
          <button class="faq-q" type="button">+ {esc(q)}</button>
          <div class="faq-a">{esc(a)}</div>
        </div>
"""
    body += """      </div>
    </div>
  </section>

  <section>
    <div class="container cta-band">
"""
    body += f"      <h2>{esc(ind['cta_h2'])}</h2>\n"
    for para in ind["cta_paragraphs"]:
        body += f"      <p>{esc(para)}</p>\n"
    body += f"""      <a class="btn btn-primary btn-lg" href="{prefix}contact.html?interest={ind['interest']}">Schedule Your Revenue Review</a>
    </div>
  </section>

  <section class="alt">
    <div class="container">
      <div class="section-head">
        <span class="section-label">Explore</span>
        <h2>Related Resources</h2>
      </div>
      <ul class="feature-list">
        <li><a href="{prefix}rcm.html">Revenue Cycle Management</a></li>
        <li><a href="{prefix}platform.html">Revenue Cycle Operations Platform</a></li>
        <li><a href="{prefix}credentialing.html">Credentialing &amp; Enrollment</a></li>
        <li><a href="{prefix}case-studies.html">Case Studies</a></li>
        <li><a href="{prefix}resources.html">Resources</a></li>
        <li><a href="{prefix}why-ascentiant.html">Why Ascentiant Health</a></li>
        <li><a href="{prefix}contact.html">Contact</a></li>
      </ul>
    </div>
  </section>
</main>

<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <img src="{prefix}Images/ascentiant-health-logo.png" alt="{SITE_NAME}">
        <p style="color:var(--muted); font-size:14px;">Technology-enabled Revenue Cycle Management — California-based with global reach.</p>
      </div>
      <div class="footer-links">
        <div class="footer-col">
          <h4>Services</h4>
          <a href="{prefix}rcm.html">Revenue Cycle Management</a>
          <a href="{prefix}platform.html">Operations Platform</a>
          <a href="{prefix}credentialing.html">Credentialing</a>
          <a href="{prefix}ai-intelligence.html">AI Intelligence</a>
        </div>
        <div class="footer-col">
          <h4>Company</h4>
          <a href="{prefix}about.html">About</a>
          <a href="{prefix}why-ascentiant.html">Why Ascentiant</a>
          <a href="{prefix}how-we-transition.html">How We Transition</a>
          <a href="{prefix}case-studies.html">Case Studies</a>
          <a href="{prefix}resources.html">Resources</a>
        </div>
        <div class="footer-col">
          <h4>Contact</h4>
          <a href="{prefix}contact.html">Schedule Review</a>
          <a href="tel:+18553138197">855-313-8197</a>
          <a href="mailto:info@ascentiant.health">info@ascentiant.health</a>
          <a href="{prefix}privacy.html">Privacy Policy</a>
          <a href="{prefix}terms.html">Terms of Use</a>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year"></span> Ascentiant Health. All rights reserved.</span>
      <span>1341 Distribution Way, Suite 11 – Top Floor, Vista, CA 92081</span>
    </div>
  </div>
</footer>
<script src="{prefix}js/main.js"></script>
<script src="{prefix}js/conversions.js"></script>
</body>
</html>
"""
    return body


def detect_nav_context(rel_path: str) -> tuple[str, Optional[str], bool]:
    prefix = depth_prefix(rel_path)
    if rel_path == "industries.html":
        return prefix, None, True
    if rel_path.startswith("industries/") and rel_path.endswith(".html"):
        slug = Path(rel_path).stem
        return prefix, slug, True
    return prefix, None, False


def update_nav_in_file(path: Path) -> bool:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    if rel.startswith("downloads/"):
        return False
    text = path.read_text(encoding="utf-8")
    prefix, active_slug, hub_active = detect_nav_context(rel)
    dropdown = nav_dropdown_html(prefix, active_slug, hub_active)

    def replace_site_nav(match: re.Match) -> str:
        open_tag, content, close_tag = match.group(1), match.group(2), match.group(3)
        if NAV_DROPDOWN_RE.search(content):
            new_content = NAV_DROPDOWN_RE.sub(dropdown, content, count=1)
        else:
            new_content = INDUSTRIES_LINK_RE.sub(dropdown, content, count=1)
        if new_content == content:
            return match.group(0)
        return open_tag + new_content + close_tag

    new_text = SITE_NAV_RE.sub(replace_site_nav, text)
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def render_industries_hub() -> str:
    prefix = ""
    meta = (
        "Technology-enabled Revenue Cycle Management for Home Health, Physical Therapy, "
        "Primary Care, Behavioral Health, Laboratories, Multi-Specialty practices, "
        "Ambulatory Surgery Centers, and other healthcare organizations."
    )
    title = "Industries We Serve | Ascentiant Health"
    cards = []
    for ind in INDUSTRIES:
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in ind["hub_tags"])
        cards.append(
            f"""        <a class="card card-link" href="industries/{ind['slug']}.html">
          <h3>{esc(ind['short_name'])}</h3>
          <p>{esc(ind['hub_blurb'])}</p>
          <div class="tagrow">{tags}</div>
        </a>"""
        )
    cards_html = "\n".join(cards)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(meta)}">
  <title>{esc(title)}</title>
  <link rel="icon" href="Images/ascentiant-health-logo.png" type="image/png">
  <link rel="apple-touch-icon" href="Images/ascentiant-health-logo.png">
  <link rel="canonical" href="{BASE}/industries.html">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(meta)}">
  <meta property="og:url" content="{BASE}/industries.html">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(meta)}">
  <meta name="twitter:image" content="{OG_IMAGE}">
  <link rel="stylesheet" href="css/styles.css">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-FFGJZQC62N"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-FFGJZQC62N');
  </script>
</head>
<body>

<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="index.html">
      <img src="Images/ascentiant-health-logo.png" alt="{SITE_NAME}">
      <div class="brand-tag">An Ascentiant<br>International Company</div>
    </a>
    <button class="nav-toggle" aria-expanded="false" aria-label="Toggle menu">Menu</button>
    <nav class="site-nav" aria-label="Primary">
      <a href="rcm.html">RCM</a>
      <a href="platform.html">Platform</a>
      <a href="credentialing.html">Credentialing</a>
{nav_dropdown_html(prefix, hub_active=True)}
      <a href="resources.html">Resources</a>
      <a href="case-studies.html">Case Studies</a>
      <a href="about.html">About</a>
      <a href="contact.html">Contact</a>
      <a class="btn btn-primary header-cta" href="contact.html">Schedule Review</a>
    </nav>
  </div>
</header>

<main>
  <section class="page-hero">
    <div class="container">
      <span class="section-label">Industries</span>
      <h1>Specialized Revenue Cycle Management Across Healthcare</h1>
      <p>Industry-specific revenue cycle expertise, platform visibility, and disciplined follow-through for every specialty we serve.</p>
    </div>
  </section>

  <section>
    <div class="container">
      <div class="section-head">
        <span class="section-label">8 Core Industries</span>
        <h2>Healthcare Verticals We Serve</h2>
        <p>Each industry has unique billing requirements, payer nuances, and compliance demands. Our teams specialize in the verticals they serve.</p>
      </div>
      <div class="grid-2">
{cards_html}
      </div>
    </div>
  </section>

  <section class="alt">
    <div class="container">
      <div class="section-head">
        <span class="section-label">Every Industry</span>
        <h2>Platform Visibility &amp; Expert Operations</h2>
        <p>Regardless of specialty, every Ascentiant client benefits from the same operational foundation.</p>
      </div>
      <div class="grid-3">
        <div class="card">
          <h3>Industry-Specific Billing</h3>
          <p>Teams trained in your specialty's coding, payer requirements, and compliance demands — not generic claim processing.</p>
        </div>
        <div class="card">
          <h3>Operations Platform</h3>
          <p>Real-time claim tracking, denial analytics, and executive dashboards tailored to your organization's workflow.</p>
          <a class="link-arrow" href="platform.html">See the Platform →</a>
        </div>
        <div class="card">
          <h3>Credentialing Support</h3>
          <p>Provider enrollment and payer credentialing integrated with billing operations to prevent enrollment-related denials.</p>
          <a class="link-arrow" href="credentialing.html">Learn More →</a>
        </div>
      </div>
    </div>
  </section>

  <section>
    <div class="container cta-band">
      <h2>Don't See Your Specialty?</h2>
      <p>We serve additional healthcare verticals beyond our core industries. Explore our <a href="industries/other-healthcare-organizations-revenue-cycle-management.html">Other Healthcare Organizations</a> page or contact us to discuss your specific revenue cycle needs.</p>
      <a class="btn btn-primary btn-lg" href="contact.html?interest=discovery-call">Schedule a Discovery Call</a>
    </div>
  </section>
</main>

<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <img src="Images/ascentiant-health-logo.png" alt="{SITE_NAME}">
        <p style="color:var(--muted); font-size:14px;">Technology-enabled Revenue Cycle Management — California-based with global reach.</p>
      </div>
      <div class="footer-links">
        <div class="footer-col">
          <h4>Services</h4>
          <a href="rcm.html">Revenue Cycle Management</a>
          <a href="platform.html">Operations Platform</a>
          <a href="credentialing.html">Credentialing</a>
          <a href="ai-intelligence.html">AI Intelligence</a>
        </div>
        <div class="footer-col">
          <h4>Company</h4>
          <a href="about.html">About</a>
          <a href="why-ascentiant.html">Why Ascentiant</a>
          <a href="how-we-transition.html">How We Transition</a>
          <a href="case-studies.html">Case Studies</a>
          <a href="resources.html">Resources</a>
        </div>
        <div class="footer-col">
          <h4>Contact</h4>
          <a href="contact.html">Schedule Review</a>
          <a href="tel:+18553138197">855-313-8197</a>
          <a href="mailto:info@ascentiant.health">info@ascentiant.health</a>
          <a href="privacy.html">Privacy Policy</a>
          <a href="terms.html">Terms of Use</a>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year"></span> Ascentiant Health. All rights reserved.</span>
      <span>1341 Distribution Way, Suite 11 – Top Floor, Vista, CA 92081</span>
    </div>
  </div>
</footer>
<script src="js/main.js"></script>
<script src="js/conversions.js"></script>
</body>
</html>
"""


def update_index_industry_section() -> bool:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    new_grid = """      <div class="grid-4">
        <a class="card card-link" href="industries/home-health-revenue-cycle-management.html"><h4>Home Health</h4><p>EVV compliance, prior authorizations, episode billing, and Medicare home health reimbursement.</p></a>
        <a class="card card-link" href="industries/physical-therapy-revenue-cycle-management.html"><h4>Physical Therapy</h4><p>Prior authorizations, therapy documentation, coding accuracy, and payer-specific PT requirements.</p></a>
        <a class="card card-link" href="industries/behavioral-health-revenue-cycle-management.html"><h4>Behavioral Health</h4><p>Mental health billing, prior authorizations, payer enrollment, and documentation compliance.</p></a>
        <a class="card card-link" href="industries/primary-care-internal-medicine-revenue-cycle-management.html"><h4>Primary Care &amp; Internal Medicine</h4><p>High-volume physician billing, preventive care, chronic care management, and coding compliance.</p></a>
      </div>"""
    pattern = re.compile(r'<div class="grid-4">.*?</div>\s*<p style="text-align:center; margin-top:28px;">', re.DOTALL)
    match = pattern.search(text)
    if not match:
        return False
    new_text = pattern.sub(
        new_grid + '\n      <p style="text-align:center; margin-top:28px;">',
        text,
        count=1,
    )
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    created: list[str] = []
    updated: list[str] = []
    deleted: list[str] = []
    issues: list[str] = []

    industries_dir = ROOT / "industries"
    industries_dir.mkdir(exist_ok=True)

    for old in OLD_INDUSTRY_FILES:
        old_path = industries_dir / old
        if old_path.exists():
            old_path.unlink()
            deleted.append(f"industries/{old}")

    for html_path in sorted(ROOT.rglob("*.html")):
        if update_nav_in_file(html_path):
            updated.append(str(html_path.relative_to(ROOT)))

    for ind in INDUSTRIES:
        out = industries_dir / f"{ind['slug']}.html"
        out.write_text(render_industry_page(ind), encoding="utf-8")
        created.append(str(out.relative_to(ROOT)))

    hub_path = ROOT / "industries.html"
    hub_path.write_text(render_industries_hub(), encoding="utf-8")
    if "industries.html" not in updated:
        updated.append("industries.html")

    if update_index_industry_section():
        if "index.html" not in updated:
            updated.append("index.html")
    else:
        issues.append("Could not update index.html industry grid section")

    print("=" * 60)
    print("Ascentiant Health — Industry Pages Build Summary")
    print("=" * 60)
    print(f"\nCreated {len(created)} industry pages:")
    for f in created:
        print(f"  + {f}")

    print(f"\nUpdated {len(updated)} files:")
    for f in sorted(set(updated)):
        print(f"  ~ {f}")

    print(f"\nDeleted {len(deleted)} old industry files:")
    for f in deleted:
        print(f"  - {f}")

    if issues:
        print(f"\nIssues ({len(issues)}):")
        for issue in issues:
            print(f"  ! {issue}")
    else:
        print("\nNo issues reported.")

    print("\nDone.")


if __name__ == "__main__":
    main()
