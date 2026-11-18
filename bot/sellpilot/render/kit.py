"""Drawing kit for printable pages: themes, fonts and reusable page parts.

Every page is drawn with sizes relative to the page, so the same template
renders on A4 and US Letter. A "low ink" version swaps colour fills for
outlines and light greys.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace

from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")
_FONTS = {
    "Serif": "DMSerifDisplay-Regular.ttf",
    "Sans": "Poppins-Regular.ttf",
    "SansLight": "Poppins-Light.ttf",
    "SansMed": "Poppins-Medium.ttf",
    "SansBold": "Poppins-SemiBold.ttf",
    "Script": "GreatVibes-Regular.ttf",
    "Hand": "AmaticSC-Bold.ttf",
}
_registered = False


def register_fonts() -> None:
    global _registered
    if _registered:
        return
    for name, file in _FONTS.items():
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, file)))
    _registered = True


@dataclass(frozen=True)
class Theme:
    key: str
    name: str
    primary: str      # headings, header bars
    accent: str       # small highlights
    soft: str         # light fills
    paper: str        # page background tint (cover only)
    ink: str = "#2B2B2B"
    line: str = "#C9C3BA"
    title_font: str = "Serif"
    deco: str = "corners"   # corners | dots | wave | band | none
    tags: tuple = ()

    def c(self, attr: str) -> Color:
        return HexColor(getattr(self, attr))


THEMES = [
    Theme("sage", "Sage Calm", "#6F8F72", "#C9A66B", "#E7EFE4", "#F6F8F3", tags=("sage green", "minimalist", "aesthetic")),
    Theme("blush", "Blush Bloom", "#C98986", "#8E6C88", "#F7E6E4", "#FDF7F5", deco="dots", tags=("pink", "cute", "feminine")),
    Theme("terracotta", "Terracotta Boho", "#B8654A", "#D9A441", "#F3E2D7", "#FBF5EF", deco="wave", tags=("boho", "terracotta", "neutral")),
    Theme("ocean", "Ocean Breeze", "#3E7C91", "#E2A86F", "#DDEDF1", "#F4F9FA", deco="band", tags=("blue", "coastal", "clean")),
    Theme("lavender", "Lavender Dream", "#8A7BB8", "#E0A3B6", "#ECE8F6", "#F8F6FC", deco="dots", tags=("purple", "lavender", "pastel")),
    Theme("mono", "Modern Mono", "#2F2F2F", "#9A9A9A", "#EDEDED", "#FFFFFF", title_font="SansBold", deco="none", tags=("black and white", "minimalist", "modern")),
    Theme("sunny", "Sunny Days", "#D99A2B", "#5E8C7E", "#FBEFD5", "#FFFBF2", deco="wave", tags=("yellow", "cheerful", "bright")),
    Theme("forest", "Forest Walk", "#3F5E4B", "#B5835A", "#E2EADF", "#F5F7F2", deco="corners", tags=("dark green", "nature", "earthy")),
    Theme("dusty", "Dusty Blue", "#6B85A6", "#C4A484", "#E3E9F2", "#F7F9FC", deco="band", tags=("dusty blue", "elegant", "calm")),
    Theme("noir", "Charcoal & Gold", "#3A3A40", "#C2A15A", "#ECE7DC", "#FAF8F3", deco="corners", tags=("gold", "luxury", "elegant")),
    Theme("cherry", "Cherry Red", "#A63D40", "#E9B44C", "#F6E0DF", "#FDF6F5", deco="dots", tags=("red", "festive", "classic")),
    Theme("mint", "Fresh Mint", "#4E9C8F", "#F2A65A", "#DDF1EC", "#F4FBF9", deco="wave", tags=("mint", "fresh", "pastel")),
]
THEME_BY_KEY = {t.key: t for t in THEMES}


def lowink(theme: Theme) -> Theme:
    """Printer-friendly variant: greys and outlines, no heavy fills."""
    return replace(theme, key=theme.key + "-lowink", primary="#555555", accent="#888888",
                   soft="#FFFFFF", paper="#FFFFFF", line="#BDBDBD", deco="none")


class Page:
    """Helper that wraps a reportlab canvas for one page."""

    def __init__(self, canvas, size, theme: Theme, brand: str = ""):
        self.cv = canvas
        self.W, self.H = size
        self.t = theme
        self.brand = brand
        self.m = self.W * 0.065          # outer margin
        self.low = theme.key.endswith("-lowink")

    # ---------- geometry helpers ----------
    @property
    def left(self):
        return self.m

    @property
    def right(self):
        return self.W - self.m

    @property
    def inner_w(self):
        return self.W - 2 * self.m

    def u(self, frac: float) -> float:
        """Unit relative to page width (keeps A4 and Letter proportional)."""
        return self.W * frac

    # ---------- primitives ----------
    def font(self, name: str, size: float, color: str = "ink"):
        self.cv.setFont(name, size)
        self.cv.setFillColor(self.t.c(color) if not color.startswith("#") else HexColor(color))

    def text(self, x, y, s, name="Sans", size=9, color="ink", align="left"):
        self.font(name, size, color)
        if align == "center":
            self.cv.drawCentredString(x, y, s)
        elif align == "right":
            self.cv.drawRightString(x, y, s)
        else:
            self.cv.drawString(x, y, s)

    def fit_text(self, x, y, s, max_w, name="Sans", size=9, color="ink", align="left", min_size=5):
        while size > min_size and pdfmetrics.stringWidth(s, name, size) > max_w:
            size -= 0.5
        self.text(x, y, s, name, size, color, align)
        return size

    def rect(self, x, y, w, h, fill=None, stroke="line", r=0, width=0.6):
        cv = self.cv
        cv.setLineWidth(width)
        if stroke:
            cv.setStrokeColor(self.t.c(stroke))
        if fill:
            cv.setFillColor(self.t.c(fill) if not fill.startswith("#") else HexColor(fill))
        if r:
            cv.roundRect(x, y, w, h, r, stroke=1 if stroke else 0, fill=1 if fill else 0)
        else:
            cv.rect(x, y, w, h, stroke=1 if stroke else 0, fill=1 if fill else 0)

    def hline(self, x1, x2, y, color="line", width=0.5, dash=None):
        cv = self.cv
        cv.setStrokeColor(self.t.c(color))
        cv.setLineWidth(width)
        if dash:
            cv.setDash(*dash)
        cv.line(x1, y, x2, y)
        cv.setDash()

    def vline(self, x, y1, y2, color="line", width=0.5):
        cv = self.cv
        cv.setStrokeColor(self.t.c(color))
        cv.setLineWidth(width)
        cv.line(x, y1, x, y2)

    def checkbox(self, x, y, s=None):
        s = s or self.u(0.018)
        self.rect(x, y, s, s, stroke="primary", r=s * 0.2, width=0.7)

    def circle(self, x, y, r, fill=None, stroke="line", width=0.6):
        cv = self.cv
        cv.setLineWidth(width)
        cv.setStrokeColor(self.t.c(stroke))
        if fill:
            cv.setFillColor(self.t.c(fill))
        cv.circle(x, y, r, stroke=1, fill=1 if fill else 0)

    # ---------- composite parts ----------
    def decorate(self):
        t, cv, W, H = self.t, self.cv, self.W, self.H
        if t.deco == "none":
            return
        cv.saveState()
        if t.deco == "corners":
            cv.setFillColor(t.c("soft"))
            p = cv.beginPath()
            p.moveTo(0, H); p.lineTo(W * 0.075, H); p.lineTo(0, H - W * 0.075); p.close()
            cv.drawPath(p, fill=1, stroke=0)
            p = cv.beginPath()
            p.moveTo(W, 0); p.lineTo(W - W * 0.075, 0); p.lineTo(W, W * 0.075); p.close()
            cv.drawPath(p, fill=1, stroke=0)
        elif t.deco == "dots":
            cv.setFillColor(t.c("soft"))
            step = W * 0.03
            for i in range(6):
                for j in range(4):
                    cv.circle(W - self.m * 0.35 - j * step, H - self.m * 0.35 - i * step, W * 0.004, stroke=0, fill=1)
        elif t.deco == "wave":
            cv.setFillColor(t.c("soft"))
            p = cv.beginPath()
            p.moveTo(0, 0); p.lineTo(0, H * 0.035)
            p.curveTo(W * 0.3, H * 0.06, W * 0.6, H * 0.0, W, H * 0.04)
            p.lineTo(W, 0); p.close()
            cv.drawPath(p, fill=1, stroke=0)
        elif t.deco == "band":
            cv.setFillColor(t.c("soft"))
            cv.rect(0, 0, W * 0.025, H, stroke=0, fill=1)
        cv.restoreState()

    def header(self, title: str, subtitle: str = "", right: str = "") -> float:
        """Draws the page title. Returns the y coordinate below the header."""
        self.decorate()
        top = self.H - self.m
        size = self.u(0.052)
        self.fit_text(self.left, top - size, title, self.inner_w * 0.7, self.t.title_font, size, "primary")
        if subtitle:
            self.text(self.left, top - size - self.u(0.028), subtitle.upper(), "SansMed", self.u(0.016), "accent")
        if right:
            self.text(self.right, top - size * 0.8, right, "SansMed", self.u(0.019), "ink", align="right")
        y = top - size - self.u(0.045)
        self.hline(self.left, self.right, y, "primary", 1.1)
        return y - self.u(0.025)

    def footer(self, note: str = ""):
        y = self.m * 0.45
        if self.brand:
            self.text(self.W / 2, y, self.brand, "SansLight", self.u(0.012), "accent", align="center")
        if note:
            self.text(self.right, y, note, "SansLight", self.u(0.012), "line", align="right")

    def label(self, x, y, s, w=None, size=None):
        """Small tinted label bar (section heading)."""
        size = size or self.u(0.017)
        h = size * 1.9
        w = w or (pdfmetrics.stringWidth(s.upper(), "SansBold", size) + size * 2)
        self.rect(x, y - h, w, h, fill="soft" if not self.low else None,
                  stroke=None if not self.low else "line", r=h * 0.25)
        self.text(x + size, y - h + size * 0.62, s.upper(), "SansBold", size, "primary")
        return y - h

    def box(self, x, y_top, w, h, title: str = "", lines: int = 0, checks: bool = False, dots: bool = False):
        """Bordered box with a title strip and optional writing lines/checkboxes."""
        self.rect(x, y_top - h, w, h, stroke="line", r=self.u(0.008))
        inner_top = y_top
        if title:
            th = self.u(0.034)
            self.rect(x, y_top - th, w, th, fill="soft" if not self.low else None,
                      stroke="line" if self.low else None, r=self.u(0.008))
            if not self.low:
                # square-off the strip bottom
                self.cv.setFillColor(self.t.c("soft"))
                self.cv.rect(x, y_top - th, w, th * 0.5, stroke=0, fill=1)
            self.fit_text(x + self.u(0.012), y_top - th + th * 0.32, title.upper(), w - self.u(0.024),
                          "SansBold", self.u(0.0145), "primary")
            inner_top = y_top - th
        if dots:
            self.dot_grid(x + self.u(0.012), y_top - h + self.u(0.012), w - self.u(0.024),
                          inner_top - (y_top - h) - self.u(0.024))
        elif lines:
            gap = (inner_top - (y_top - h)) / (lines + 0.4)
            for i in range(1, lines + 1):
                yy = inner_top - gap * i
                if checks:
                    s = min(gap * 0.5, self.u(0.016))
                    self.checkbox(x + self.u(0.012), yy + gap * 0.12, s)
                    self.hline(x + self.u(0.012) + s * 1.6, x + w - self.u(0.012), yy)
                else:
                    self.hline(x + self.u(0.012), x + w - self.u(0.012), yy)
        return y_top - h

    def lines(self, x, y_top, w, h, gap=None):
        gap = gap or self.u(0.032)
        n = int(h // gap)
        for i in range(1, n + 1):
            self.hline(x, x + w, y_top - i * gap)

    def dot_grid(self, x, y, w, h, gap=None):
        gap = gap or self.u(0.022)
        cv = self.cv
        cv.setFillColor(self.t.c("line"))
        nx, ny = int(w // gap), int(h // gap)
        ox = x + (w - nx * gap) / 2
        oy = y + (h - ny * gap) / 2
        r = self.u(0.0013)
        for i in range(nx + 1):
            for j in range(ny + 1):
                cv.circle(ox + i * gap, oy + j * gap, r, stroke=0, fill=1)

    def table(self, x, y_top, w, h, headers, rows: int, col_w=None, header_fill=True, zebra=True):
        """Writable table. col_w are relative widths. Returns bottom y."""
        col_w = col_w or [1] * len(headers)
        tot = sum(col_w)
        xs = [x]
        for cw in col_w:
            xs.append(xs[-1] + w * cw / tot)
        hh = self.u(0.034)
        rh = (h - hh) / rows
        if header_fill and not self.low:
            self.rect(x, y_top - hh, w, hh, fill="primary", stroke=None, r=0)
            hc = "#FFFFFF"
        else:
            self.rect(x, y_top - hh, w, hh, stroke="ink", width=0.8)
            hc = "ink"
        for i, hd in enumerate(headers):
            cw = xs[i + 1] - xs[i]
            self.fit_text(xs[i] + cw / 2, y_top - hh * 0.66, hd.upper(), cw - self.u(0.01),
                          "SansBold", self.u(0.0135), hc, align="center")
        for r in range(rows):
            yb = y_top - hh - (r + 1) * rh
            if zebra and r % 2 == 1 and not self.low:
                self.rect(x, yb, w, rh, fill="soft", stroke=None)
            self.hline(x, x + w, yb)
        for xx in xs:
            self.vline(xx, y_top - h, y_top - hh)
        self.rect(x, y_top - h, w, h, stroke="line", width=0.8)
        return y_top - h, xs, hh, rh

    def stars(self, cx, cy, n=5, r=None):
        import math
        r = r or self.u(0.008)
        cv = self.cv
        cv.setStrokeColor(self.t.c("accent"))
        cv.setLineWidth(0.6)
        for k in range(n):
            x0 = cx + k * r * 2.6
            p = cv.beginPath()
            for i in range(10):
                ang = math.pi / 2 + i * math.pi / 5
                rr = r if i % 2 == 0 else r * 0.45
                px, py = x0 + rr * math.cos(ang), cy + rr * math.sin(ang)
                p.moveTo(px, py) if i == 0 else p.lineTo(px, py)
            p.close()
            cv.drawPath(p, stroke=1, fill=0)

    def link_to(self, key: str, x, y, w, h):
        """Clickable area that jumps to a bookmarked page (tablet-friendly PDFs)."""
        self.cv.linkRect("", key, (x, y, x + w, y + h), relative=0, thickness=0)


def wrap(s: str, font: str, size: float, max_w: float) -> list[str]:
    words, out, cur = s.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if pdfmetrics.stringWidth(trial, font, size) <= max_w:
            cur = trial
        else:
            if cur:
                out.append(cur)
            cur = wd
    if cur:
        out.append(cur)
    return out


__all__ = ["Theme", "THEMES", "THEME_BY_KEY", "lowink", "Page", "register_fonts", "wrap", "white"]
