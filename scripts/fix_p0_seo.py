#!/usr/bin/env python3
"""Fix case-study breadcrumbs, broken nested-folder links, and add contextual internal links."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://ascentiant.health"

CASE_LABELS = {
    "home-health.html": "Home Health",
    "physical-therapy.html": "Physical Therapy",
    "laboratory.html": "Laboratory",
    "physician-practice.html": "Physician Practice",
}

ARTICLE_NAV = """    <nav class="site-nav" aria-label="Primary">
      <a href="/rcm">RCM</a>
      <a href="/platform">Platform</a>
      <a href="/credentialing">Credentialing</a>
      <div class="nav-dropdown">
        <button class="nav-dropdown-toggle" type="button" aria-expanded="false" aria-haspopup="true">
          Industries <span class="nav-chevron" aria-hidden="true">▼</span>
        </button>
        <div class="nav-dropdown-menu" role="menu">
          <a href="/industries/home-health-revenue-cycle-management" role="menuitem">Home Health</a>
          <a href="/industries/physical-therapy-revenue-cycle-management" role="menuitem">Physical Therapy</a>
          <a href="/industries/primary-care-internal-medicine-revenue-cycle-management" role="menuitem">Primary Care &amp; Internal Medicine</a>
          <a href="/industries/behavioral-health-revenue-cycle-management" role="menuitem">Behavioral Health</a>
          <a href="/industries/laboratory-revenue-cycle-management" role="menuitem">Laboratories</a>
          <a href="/industries/multi-specialty-physician-practice-revenue-cycle-management" role="menuitem">Multi-Specialty Physician Practices</a>
          <a href="/industries/ambulatory-surgery-center-revenue-cycle-management" role="menuitem">Ambulatory Care</a>
          <a href="/industries/other-healthcare-organizations-revenue-cycle-management" role="menuitem">Other Healthcare Organizations</a>
          <a href="/industries" role="menuitem" class="nav-dropdown-all">View All Industries</a>
        </div>
      </div>
      <a href="/resources" class="active">Resources</a>
      <a href="/case-studies">Case Studies</a>
      <a href="/about">About</a>
      <a href="/contact">Contact</a>
      <a class="btn btn-primary header-cta" href="/contact">Schedule Review</a>
    </nav>"""

ARTICLE_LINKS = {
    "credentialing-guide.html": """      <p class="related-links">Related: <a href="/credentialing">Credentialing &amp; Enrollment</a> · <a href="/rcm">Revenue Cycle Management</a> · <a href="/contact?interest=credentialing">Talk to our credentialing team</a></p>
      <p style="margin-top:32px;"><a class="btn btn-primary" href="/downloads/credentialing-checklist" target="_blank">Download Credentialing Checklist</a>
      <a class="btn" href="/contact?interest=credentialing" style="margin-left:12px;">Talk to Our Credentialing Team</a></p>""",
    "denial-management.html": """      <p class="related-links">Related: <a href="/rcm">Revenue Cycle Management</a> · <a href="/platform">Operations Platform</a> · <a href="/resources/articles/rcm-kpis">RCM KPIs</a></p>
      <p style="margin-top:32px;"><a class="btn btn-primary" href="/downloads/denial-prevention-guide" target="_blank">Download Denial Prevention Guide</a>
      <a class="btn" href="/contact?interest=revenue-review" style="margin-left:12px;">Schedule a Revenue Review</a></p>""",
    "home-health-billing-update.html": """      <p class="related-links">Related: <a href="/industries/home-health-revenue-cycle-management">Home Health RCM</a> · <a href="/case-studies/home-health">Home Health case study</a> · <a href="/rcm">Revenue Cycle Management</a></p>
      <p style="margin-top:32px;"><a class="btn btn-primary" href="/contact?interest=home-health">Schedule a Home Health Revenue Review</a>
      <a class="btn" href="/resources" style="margin-left:12px;">← All Resources</a></p>""",
    "medical-billing-guide.html": """      <p class="related-links">Related: <a href="/rcm">Revenue Cycle Management</a> · <a href="/industries">Industries we serve</a> · <a href="/platform">Operations Platform</a></p>
      <p style="margin-top:32px;"><a class="btn btn-primary" href="/downloads/revenue-cycle-assessment" target="_blank">Download Revenue Cycle Assessment</a>
      <a class="btn" href="/contact?interest=revenue-review" style="margin-left:12px;">Schedule a Revenue Review</a></p>""",
    "no-surprises-act.html": """      <p class="related-links">Related: <a href="/rcm">Revenue Cycle Management</a> · <a href="/resources/articles/denial-management">Denial management</a> · <a href="/contact">Contact our team</a></p>
      <p style="margin-top:32px;"><a class="btn btn-primary" href="/rcm">Explore Revenue Cycle Management</a>
      <a class="btn" href="/contact" style="margin-left:12px;">Contact Our Team</a></p>""",
    "physical-therapy-billing-update.html": """      <p class="related-links">Related: <a href="/industries/physical-therapy-revenue-cycle-management">Physical Therapy RCM</a> · <a href="/case-studies/physical-therapy">Physical Therapy case study</a> · <a href="/rcm">Revenue Cycle Management</a></p>
      <p style="margin-top:32px;"><a class="btn btn-primary" href="/contact?interest=physical-therapy">Schedule a PT Revenue Review</a>
      <a class="btn" href="/resources" style="margin-left:12px;">← All Resources</a></p>""",
    "rcm-kpis.html": """      <p class="related-links">Related: <a href="/platform">Operations Platform</a> · <a href="/rcm">Revenue Cycle Management</a> · <a href="/resources/articles/denial-management">Denial management</a></p>
      <p style="margin-top:32px;"><a class="btn btn-primary" href="/downloads/rcm-kpi-guide" target="_blank">Download RCM KPI Guide</a>
      <a class="btn" href="/contact" style="margin-left:12px;">Schedule a Revenue Review</a></p>""",
    "revenue-recovery.html": """      <p class="related-links">Related: <a href="/rcm">Revenue Cycle Management</a> · <a href="/case-studies">Case studies</a> · <a href="/resources/articles/denial-management">Denial management</a></p>
      <p style="margin-top:32px;"><a class="btn btn-primary" href="/downloads/revenue-leakage-checklist" target="_blank">Download Revenue Leakage Checklist</a>
      <a class="btn" href="/contact?interest=revenue-review" style="margin-left:12px;">Schedule a Revenue Review</a></p>""",
}

INDUSTRY_RELATED = {
    "home-health-revenue-cycle-management.html": [
        ('<li><a href="/case-studies">Case Studies</a></li>', '<li><a href="/case-studies/home-health">Home Health case study</a></li>'),
        ('<li><a href="/resources">Resources</a></li>', '<li><a href="/resources/articles/home-health-billing-update">Home Health billing update</a></li>\n        <li><a href="/resources">All Resources</a></li>'),
    ],
    "physical-therapy-revenue-cycle-management.html": [
        ('<li><a href="/case-studies">Case Studies</a></li>', '<li><a href="/case-studies/physical-therapy">Physical Therapy case study</a></li>'),
        ('<li><a href="/resources">Resources</a></li>', '<li><a href="/resources/articles/physical-therapy-billing-update">Physical Therapy billing update</a></li>\n        <li><a href="/resources">All Resources</a></li>'),
    ],
    "laboratory-revenue-cycle-management.html": [
        ('<li><a href="/case-studies">Case Studies</a></li>', '<li><a href="/case-studies/laboratory">Laboratory case study</a></li>'),
    ],
    "primary-care-internal-medicine-revenue-cycle-management.html": [
        ('<li><a href="/case-studies">Case Studies</a></li>', '<li><a href="/case-studies/physician-practice">Physician practice case study</a></li>'),
    ],
    "multi-specialty-physician-practice-revenue-cycle-management.html": [
        ('<li><a href="/case-studies">Case Studies</a></li>', '<li><a href="/case-studies/physician-practice">Physician practice case study</a></li>'),
    ],
}

CASE_CTA = {
    "home-health.html": (
        '<a class="btn btn-primary btn-lg" href="/contact?interest=home-health">Schedule a Revenue Review</a>',
        '<p><a class="link-arrow" href="/industries/home-health-revenue-cycle-management">Home Health Revenue Cycle Management</a> · <a class="link-arrow" href="/resources/articles/home-health-billing-update">Home Health billing update</a></p>\n      <a class="btn btn-primary btn-lg" href="/contact?interest=home-health">Schedule a Revenue Review</a>',
    ),
    "physical-therapy.html": (
        '<a class="btn btn-primary btn-lg" href="/contact?interest=physical-therapy">Schedule a Revenue Review</a>',
        '<p><a class="link-arrow" href="/industries/physical-therapy-revenue-cycle-management">Physical Therapy RCM</a> · <a class="link-arrow" href="/resources/articles/physical-therapy-billing-update">Physical Therapy billing update</a></p>\n      <a class="btn btn-primary btn-lg" href="/contact?interest=physical-therapy">Schedule a Revenue Review</a>',
    ),
    "laboratory.html": (
        '<a class="btn btn-primary btn-lg" href="/contact?interest=laboratory">Schedule a Revenue Review</a>',
        '<p><a class="link-arrow" href="/industries/laboratory-revenue-cycle-management">Laboratory RCM</a></p>\n      <a class="btn btn-primary btn-lg" href="/contact?interest=laboratory">Schedule a Revenue Review</a>',
    ),
    "physician-practice.html": (
        '<a class="btn btn-primary btn-lg" href="/contact?interest=discovery-call">Schedule a Revenue Review</a>',
        '<p><a class="link-arrow" href="/industries/multi-specialty-physician-practice-revenue-cycle-management">Multi-Specialty Physician Practice RCM</a> · <a class="link-arrow" href="/industries/primary-care-internal-medicine-revenue-cycle-management">Primary Care RCM</a></p>\n      <a class="btn btn-primary btn-lg" href="/contact?interest=discovery-call">Schedule a Revenue Review</a>',
    ),
}


def breadcrumb_block(label: str, slug: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Case Studies", "item": f"{BASE}/case-studies"},
            {"@type": "ListItem", "position": 3, "name": label, "item": f"{BASE}/case-studies/{slug}"},
        ],
    }
    return (
        '  <script type="application/ld+json">\n'
        + json.dumps(data, indent=2)
        + "\n  </script>"
    )


def fix_case_study(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    label = CASE_LABELS[path.name]
    slug = path.stem
    block = breadcrumb_block(label, slug)
    html = re.sub(
        r'  <script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "BreadcrumbList"[\s\S]*?</script>',
        block,
        html,
        count=1,
    )
    old, new = CASE_CTA[path.name]
    if old in html and new not in html:
        html = html.replace(old, new, 1)
    path.write_text(html, encoding="utf-8")
    print(f"case study OK {path.name}")


def fix_article(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    html = re.sub(
        r'<a class="brand" href="/resources">',
        '<a class="brand" href="/">',
        html,
        count=1,
    )
    html = re.sub(
        r'    <nav class="site-nav" aria-label="Primary">[\s\S]*?</nav>',
        ARTICLE_NAV,
        html,
        count=1,
    )
    html = re.sub(
        r'<p class="breadcrumb">.*?</p>',
        lambda m: m.group(0)
        .replace('<a href="/resources">Home</a>', '<a href="/">Home</a>')
        .replace('<a href="/resources/resources">Resources</a>', '<a href="/resources">Resources</a>'),
        html,
        count=1,
    )
    html = html.replace('href="../css/styles.css"', 'href="../../css/styles.css"')
    html = html.replace('<script src="../js/main.js"></script>', '<script src="../../js/main.js"></script>\n<script src="../../js/conversions.js"></script>')
    html = html.replace("/resources/resources", "/resources")
    html = html.replace("/resources/contact", "/contact")
    html = html.replace("/resources/rcm", "/rcm")
    html = html.replace("/resources/platform", "/platform")
    html = html.replace("/resources/credentialing", "/credentialing")
    html = html.replace("/resources/case-studies", "/case-studies")
    html = html.replace("/resources/about", "/about")
    html = html.replace("/resources/downloads/", "/downloads/")
    html = html.replace(
        '<footer class="site-footer"><div class="container"><div class="footer-bottom" style="border:none;margin:0;padding:0;"><span>© <span id="year"></span> Ascentiant Health</span><span><a href="/resources">← All Resources</a></span></div></div></footer>',
        '<footer class="site-footer"><div class="container"><div class="footer-bottom" style="border:none;margin:0;padding:0;"><span>© <span id="year"></span> Ascentiant Health</span><span><a href="/resources">← All Resources</a></span></div></div></footer>',
    )
    extra = ARTICLE_LINKS.get(path.name)
    if extra:
        html = re.sub(
            r'      <p style="margin-top:32px;">[\s\S]*?</p>(?:\s*<p style="margin-top:32px;">[\s\S]*?</p>)?',
            extra,
            html,
            count=1,
        )
        if extra.split("\n", 1)[0] not in html and "related-links" not in html:
            html = html.replace(
                "</div>\n    </div>\n  </section>\n</main>",
                extra + "\n    </div>\n  </section>\n</main>",
                1,
            )
    path.write_text(html, encoding="utf-8")
    print(f"article OK {path.name}")


def fix_industry(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    for old, new in INDUSTRY_RELATED.get(path.name, []):
        if old in html and new not in html:
            html = html.replace(old, new, 1)
    path.write_text(html, encoding="utf-8")
    print(f"industry OK {path.name}")


def patch_enhance_seo() -> None:
    path = ROOT / "scripts" / "enhance_seo.py"
    text = path.read_text(encoding="utf-8")
    old = '''    tail = re.split(r"&rsaquo;|›", re.sub(r"<[^>]+>", "", inner))
    if len(tail) > len(links):
        last = tail[-1].strip()
        if last:
            items.append((last, items[-1][1] if items else BASE))
    return items if items else None'''
    new = '''    visible = re.sub(r"<[^>]+>", " ", inner)
    parts = [p.strip() for p in re.split(r"&rsaquo;|›", visible) if p.strip()]
    if parts:
        last = parts[-1]
        if last and (not items or items[-1][0] != last):
            items.append((last, items[-1][1] if items else BASE))
    return items if items else None'''
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        print("patched enhance_seo.py breadcrumb parser")
    else:
        print("enhance_seo.py parser already patched or changed")


def patch_fix_seo_urls() -> None:
    path = ROOT / "scripts" / "fix_seo_urls.py"
    text = path.read_text(encoding="utf-8")
    old = '''    # Resolve relative to current file directory
    current_dir = Path(current_rel).parent
    if path.startswith("/"):
        resolved = path.lstrip("/")
    else:
        resolved = (current_dir / path).as_posix()'''
    new = '''    # Root-relative site links stay root-relative. Only resolve true relative paths.
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
        resolved = (current_dir / path).as_posix()'''
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        print("patched fix_seo_urls.py href resolver")
    else:
        print("fix_seo_urls.py resolver already patched or changed")


def main() -> None:
    for path in (ROOT / "case-studies").glob("*.html"):
        if path.name in CASE_LABELS:
            fix_case_study(path)
    for path in (ROOT / "resources" / "articles").glob("*.html"):
        fix_article(path)
    for name in INDUSTRY_RELATED:
        fix_industry(ROOT / "industries" / name)
    patch_enhance_seo()
    patch_fix_seo_urls()
    print("Done.")


if __name__ == "__main__":
    main()
