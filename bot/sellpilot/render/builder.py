"""Turns a product spec into sellable files: PDFs and listing images."""
from __future__ import annotations

import io
import os
from dataclasses import dataclass, field

from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas as rl_canvas

from .kit import Page, Theme, lowink, register_fonts
from .pages import PAGES

SIZES = {"A4": A4, "Letter": LETTER}


@dataclass
class Built:
    files: dict[str, bytes] = field(default_factory=dict)        # filename -> pdf bytes
    images: list[tuple[str, bytes]] = field(default_factory=list)  # (filename, png bytes)
    page_count: int = 0
    sections: list[str] = field(default_factory=list)            # human labels, in order


def plan_sections(page_specs):
    """Group consecutive page keys into sections for the contents page."""
    sections, seen = [], {}
    for i, (key, _params) in enumerate(page_specs):
        if key in ("contents", "cover"):
            continue
        label = PAGES[key][1]
        if key == "monthly":
            label = "Monthly calendars"
        if label in seen:
            continue
        seen[label] = f"sec{i}"
        sections.append((label, f"sec{i}", i))
    return sections


def render_pdf(page_specs, theme: Theme, size_name: str, title: str, subtitle: str, year, brand: str,
               low: bool = False) -> tuple[bytes, int]:
    register_fonts()
    buf = io.BytesIO()
    size = SIZES[size_name]
    th = lowink(theme) if low else theme
    cv = rl_canvas.Canvas(buf, pagesize=size, pageCompression=1)
    cv.setTitle(title)
    cv.setAuthor(brand or "")
    cv.setSubject(subtitle)
    sections = plan_sections(page_specs)
    sec_at = {i: (label, key) for label, key, i in sections}
    specs = [("cover", {"title": title, "subtitle": subtitle, "year": year,
                        "tagline": "A4 + US Letter  |  print or use on a tablet"})] + list(page_specs)
    n = 0
    for idx, (key, params) in enumerate(specs):
        fn = PAGES[key][0]
        p = Page(cv, size, th, brand)
        real_i = idx - 1
        if real_i in sec_at:
            label, bkey = sec_at[real_i]
            cv.bookmarkPage(bkey)
            cv.addOutlineEntry(label, bkey, level=0)
        if key == "monthly" and params.get("month"):
            cv.bookmarkPage(f"m{params['month']}")
        if key == "contents":
            params = dict(params, items=[(lb, k) for lb, k, _ in sections])
        fn(p, **params)
        cv.showPage()
        n += 1
    cv.save()
    return buf.getvalue(), n


def build_files(spec: dict, theme: Theme, brand: str, slug: str) -> Built:
    out = Built()
    for size_name in ("A4", "Letter"):
        for low in (False, True):
            pdf, n = render_pdf(spec["pages"], theme, size_name, spec["title_short"], spec["subtitle"],
                                spec.get("year"), brand, low)
            suffix = f"{size_name}{'-LowInk' if low else ''}"
            out.files[f"{slug}-{suffix}.pdf"] = pdf
            out.page_count = n
    out.sections = [lb for lb, _k, _i in plan_sections(spec["pages"])]
    return out


def rasterize(pdf_bytes: bytes, pages: list[int], width_px: int = 900):
    """Render chosen PDF pages to PIL images (for listing photos)."""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(pdf_bytes)
    imgs = []
    for i in pages:
        if i >= len(doc):
            continue
        page = doc[i]
        scale = width_px / page.get_width()
        imgs.append(page.render(scale=scale).to_pil().convert("RGB"))
    doc.close()
    return imgs


def font_path(name: str) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", name)
