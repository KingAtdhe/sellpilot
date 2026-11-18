"""Listing photos made from the real PDF pages (what the buyer sees is what they get)."""
from __future__ import annotations

import io

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .builder import font_path, rasterize
from .kit import Theme

W, H = 1600, 1200


def _f(name, size):
    return ImageFont.truetype(font_path(name), size)


def _rgb(hexs):
    hexs = hexs.lstrip("#")
    return tuple(int(hexs[i:i + 2], 16) for i in (0, 2, 4))


def _png(img) -> bytes:
    b = io.BytesIO()
    img.save(b, "PNG", optimize=True)
    return b.getvalue()


def _shadowed(canvas: Image.Image, page: Image.Image, xy, angle=0, blur=18, offset=(10, 16)):
    pg = page.copy()
    border = Image.new("RGB", (pg.width + 2, pg.height + 2), (225, 225, 225))
    border.paste(pg, (1, 1))
    pg = border.convert("RGBA")
    if angle:
        pg = pg.rotate(angle, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (pg.width + blur * 4, pg.height + blur * 4), (0, 0, 0, 0))
    mask = pg.split()[3].point(lambda a: 70 if a else 0)
    sh.paste((0, 0, 0, 255), (blur * 2, blur * 2), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    x, y = xy
    canvas.alpha_composite(sh, (int(x - blur * 2 + offset[0]), int(y - blur * 2 + offset[1])))
    canvas.alpha_composite(pg, (int(x), int(y)))


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _pill(d, x, y, text, theme: Theme, font):
    tw = d.textlength(text, font=font)
    d.rounded_rectangle((x, y, x + tw + 44, y + 54), 27, fill=_rgb(theme.primary))
    d.text((x + 22, y + 10), text, font=font, fill="white")
    return x + tw + 44 + 14


def _base(theme: Theme, size=(W, H)):
    img = Image.new("RGBA", size, _rgb(theme.paper) + (255,))
    d = ImageDraw.Draw(img)
    w, h = size
    d.ellipse((w * 0.62, -h * 0.25, w * 1.25, h * 0.55), fill=_rgb(theme.soft))
    d.ellipse((-w * 0.18, h * 0.7, w * 0.25, h * 1.3), fill=_rgb(theme.soft))
    return img, d


def hero(theme, title, subtitle, pages_img, page_count, brand):
    img, d = _base(theme)
    cover, p1, p2 = pages_img[0], pages_img[1], pages_img[2]
    s = 560 / cover.height
    rs = lambda im: im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    _shadowed(img, rs(p2), (1040, 380), angle=-8)
    _shadowed(img, rs(p1), (930, 330), angle=-3)
    _shadowed(img, rs(cover), (780, 300), angle=4)
    d = ImageDraw.Draw(img)
    tf = _f("DMSerifDisplay-Regular.ttf", 92)
    y = 210
    for ln in _wrap(d, title, tf, 680)[:3]:
        d.text((90, y), ln, font=tf, fill=_rgb(theme.primary))
        y += 104
    d.text((94, y + 10), subtitle.upper(), font=_f("Poppins-Medium.ttf", 30), fill=_rgb(theme.ink))
    pf = _f("Poppins-SemiBold.ttf", 26)
    x = 90
    by = y + 90
    for t in (f"{page_count} pages", "A4 + US Letter"):
        x = _pill(d, x, by, t, theme, pf)
    _pill(d, 90, by + 70, "Instant download", theme, pf)
    d.text((94, H - 90), "Printable PDF  ·  tablet friendly  ·  low-ink version included",
           font=_f("Poppins-Regular.ttf", 24), fill=_rgb(theme.ink))
    return img.convert("RGB")


def included(theme, labels, thumbs):
    img, d = _base(theme)
    d.text((90, 70), "What's inside", font=_f("DMSerifDisplay-Regular.ttf", 76), fill=_rgb(theme.primary))
    n = min(len(thumbs), 8)
    cols = 4
    tw = 300
    for i in range(n):
        th = thumbs[i]
        s = tw / th.width
        th = th.resize((tw, int(th.height * s)), Image.LANCZOS)
        th = th.crop((0, 0, tw, min(th.height, 380)))
        x = 90 + (i % cols) * (tw + 60)
        y = 200 + (i // cols) * 490
        _shadowed(img, th, (x, y), blur=10, offset=(6, 8))
        d = ImageDraw.Draw(img)
        lab = labels[i] if i < len(labels) else ""
        d.text((x + tw / 2, y + 400), lab, font=_f("Poppins-Medium.ttf", 26), fill=_rgb(theme.ink), anchor="ma")
    return img.convert("RGB")


def closeup(theme, a, b, heading):
    img, d = _base(theme)
    d.text((W / 2, 60), heading, font=_f("DMSerifDisplay-Regular.ttf", 64), fill=_rgb(theme.primary), anchor="ma")
    s = 1000 / a.height
    for i, pg in enumerate((a, b)):
        pg = pg.resize((int(pg.width * s), int(pg.height * s)), Image.LANCZOS)
        pg = pg.crop((0, 0, pg.width, 1000))
        _shadowed(img, pg, (W / 2 - pg.width - 25 + i * (pg.width + 50), 170), blur=14)
    return img.convert("RGB")


def formats(theme, page, features):
    img, d = _base(theme)
    # tablet
    tx, ty, tw, th = 860, 120, 640, 960
    d.rounded_rectangle((tx, ty, tx + tw, ty + th), 48, fill=(40, 40, 44))
    s = (th - 90) / page.height
    pg = page.resize((int(page.width * s), int(page.height * s)), Image.LANCZOS)
    if pg.width > tw - 60:
        s2 = (tw - 60) / pg.width
        pg = pg.resize((int(pg.width * s2), int(pg.height * s2)), Image.LANCZOS)
    img.paste(pg, (int(tx + (tw - pg.width) / 2), int(ty + (th - pg.height) / 2)))
    d = ImageDraw.Draw(img)
    d.text((90, 140), "Print it or", font=_f("DMSerifDisplay-Regular.ttf", 76), fill=_rgb(theme.primary))
    d.text((90, 230), "use it on a tablet", font=_f("DMSerifDisplay-Regular.ttf", 76), fill=_rgb(theme.primary))
    f = _f("Poppins-Regular.ttf", 32)
    y = 390
    for feat in features[:7]:
        d.ellipse((92, y + 12, 112, y + 32), fill=_rgb(theme.accent))
        for ln in _wrap(d, feat, f, 640):
            d.text((132, y), ln, font=f, fill=_rgb(theme.ink))
            y += 42
        y += 22
    return img.convert("RGB")


def pin(theme, title, subtitle, cover, page):
    """Vertical 1000x1500 image for Pinterest."""
    img, d = _base(theme, (1000, 1500))
    d.rectangle((0, 0, 1000, 330), fill=_rgb(theme.primary))
    tf = _f("DMSerifDisplay-Regular.ttf", 78)
    lines = _wrap(d, title, tf, 880)[:2]
    y = 70 if len(lines) == 2 else 110
    for ln in lines:
        d.text((500, y), ln, font=tf, fill="white", anchor="ma")
        y += 92
    d.text((500, y + 10), subtitle.upper(), font=_f("Poppins-Medium.ttf", 28), fill=_rgb(theme.soft), anchor="ma")
    s = 880 / cover.height
    rs = lambda im: im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    _shadowed(img, rs(page), (330, 470), angle=-5)
    _shadowed(img, rs(cover), (110, 430), angle=4)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((250, 1395, 750, 1465), 35, fill=_rgb(theme.accent))
    d.text((500, 1410), "PRINTABLE · INSTANT DOWNLOAD", font=_f("Poppins-SemiBold.ttf", 26), fill="white", anchor="ma")
    return img.convert("RGB")


def make_images(theme: Theme, pdf_bytes: bytes, page_count: int, spec: dict, sections: list[str], features: list[str]):
    """Returns [(filename, png bytes)] - hero first."""
    # choose representative pages: cover, then first page of distinct sections
    from .builder import plan_sections
    sec = plan_sections(spec["pages"])
    idx = [i + 1 for _lb, _k, i in sec]          # +1 for cover
    pick = [0] + idx[:10]
    imgs = rasterize(pdf_bytes, pick, 900)
    cover = imgs[0]
    inner = imgs[1:] or [cover]
    while len(inner) < 3:
        inner.append(inner[-1])
    out = [
        ("1-hero.png", hero(theme, spec["title_short"], spec["subtitle"], [cover, inner[0], inner[1]], page_count, spec.get("brand", ""))),
        ("2-inside.png", included(theme, [lb for lb, _k, _i in sec], inner)),
        ("3-closeup.png", closeup(theme, inner[min(1, len(inner) - 1)], inner[min(2, len(inner) - 1)], "Thoughtfully designed pages")),
        ("4-formats.png", formats(theme, inner[0], features)),
    ]
    pin_img = pin(theme, spec["title_short"], spec["subtitle"], cover, inner[0])
    return [(n, _png(im)) for n, im in out], ("pin.png", _png(pin_img))
