"""Makes one complete, ready-to-sell product package from a research pick."""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

from . import listing
from .catalog import fmt
from .render import builder, previews


@dataclass
class Package:
    name: str
    short: str
    description: str
    price_cents: int
    step: int
    files: dict
    images: list
    pin: tuple
    tags: list
    metadata: dict = field(default_factory=dict)
    page_count: int = 0


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def make(pick: dict, cfg: dict, today: dt.date | None = None) -> Package:
    today = today or dt.date.today()
    kind, theme, year = pick["kind"], pick["theme"], pick["year"]
    short, full = listing.title_for(kind, theme, year)
    spec = {"pages": kind["pages"](year), "title_short": short, "subtitle": kind["subtitle"],
            "year": year if kind.get("dated") else None, "brand": cfg["store_name"]}
    slug = slugify(f"{short}-{theme.key}")
    built = builder.build_files(spec, theme, cfg["store_name"], slug)
    has_contents = any(k == "contents" for k, _ in spec["pages"])
    feats = listing.features(kind, built.page_count, built.sections, has_contents)
    a4 = built.files[f"{slug}-A4.pdf"]
    images, pin = previews.make_images(theme, a4, built.page_count, spec, built.sections, feats)
    cents, step = listing.launch_price(kind, built.page_count, cfg.get("price_multiplier", 1.0))
    desc = listing.description(kind, theme, year, built.page_count, built.sections, pick.get("phrases", []),
                               cfg["store_name"])
    tags = listing.tags_for(kind, theme, year, pick.get("phrases", []))
    md = {"sp": "1", "sp_kind": kind["key"], "sp_theme": theme.key, "sp_year": str(year) if kind.get("dated") else "",
          "sp_made": today.isoformat(), "sp_step": step, "sp_slug": slug, "sp_cat": kind["category"],
          "sp_tags": ", ".join(tags)[:500], "sp_pages": built.page_count}
    return Package(full, short, desc, cents, step, built.files, images, pin, tags, md, built.page_count)
