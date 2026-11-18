"""Sales tracking and automatic selling decisions."""
from __future__ import annotations

import datetime as dt

from . import listing
from .catalog import KIND_BY_KEY
from .render.kit import THEME_BY_KEY

PAID = {"paid", "partially_refunded"}

# Store-wide sales. Dates are (month, day). Codes are shown on the storefront and pins.
CAMPAIGNS = [
    {"key": "newyear", "name": "New Year Fresh Start", "code": "FRESHSTART", "pct": 25, "start": (12, 26), "end": (1, 7)},
    {"key": "spring", "name": "Spring Reset", "code": "SPRING", "pct": 20, "start": (3, 14), "end": (3, 24)},
    {"key": "midyear", "name": "Mid-Year Reset", "code": "MIDYEAR", "pct": 20, "start": (6, 20), "end": (7, 1)},
    {"key": "school", "name": "Back to School", "code": "SCHOOL", "pct": 20, "start": (8, 1), "end": (8, 18)},
    {"key": "blackfriday", "name": "Black Friday", "code": "BLACKFRIDAY", "pct": 30, "start": (11, 23), "end": (12, 2)},
]


def _d(s):
    return dt.date.fromisoformat(s[:10]) if s else None


def stats(products: list[dict], orders: list[dict], today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    out = {p["id"]: {"sales": 0, "sales_30": 0, "earned": 0, "earned_30": 0, "last_sale": None} for p in products}
    total = {"sales": 0, "earned": 0, "sales_30": 0, "earned_30": 0, "today": 0, "earned_today": 0, "currency": None,
             "by_day": {}}
    for o in orders:
        if o.get("status") not in PAID:
            continue
        earned = (o.get("net_amount", 0) - o.get("platform_fee_amount", 0) - o.get("refunded_amount", 0))
        d = _d(o.get("created_at"))
        total["currency"] = total["currency"] or o.get("currency")
        total["sales"] += 1
        total["earned"] += earned
        day = d.isoformat() if d else "?"
        total["by_day"][day] = total["by_day"].get(day, 0) + earned
        recent = d and (today - d).days < 30
        if recent:
            total["sales_30"] += 1
            total["earned_30"] += earned
        if d == today:
            total["today"] += 1
            total["earned_today"] += earned
        s = out.setdefault(o.get("product_id"), {"sales": 0, "sales_30": 0, "earned": 0, "earned_30": 0, "last_sale": None})
        s["sales"] += 1
        s["earned"] += earned
        if recent:
            s["sales_30"] += 1
            s["earned_30"] += earned
        if d and (not s["last_sale"] or d.isoformat() > s["last_sale"]):
            s["last_sale"] = d.isoformat()
    out["_total"] = total
    return out


def price_actions(products, st, today, cfg) -> list[dict]:
    """Price tests: lower slow sellers once, raise proven sellers. At most one change per 14 days."""
    acts = []
    for p in products:
        md = p.get("metadata") or {}
        if not md.get("sp") or p.get("is_archived"):
            continue
        made = _d(md.get("sp_made"))
        last = _d(md.get("sp_pchg")) or made
        if not made or (today - last).days < 14:
            continue
        kind = KIND_BY_KEY.get(md.get("sp_kind"))
        base = listing.ladder_index(kind["base_price"]) if kind else int(md.get("sp_step", 3))
        step = int(md.get("sp_step", base))
        s = st.get(p["id"], {})
        new = step
        if md.get("sp_bundle"):
            continue
        if s.get("sales_30", 0) >= cfg.get("raise_after_sales_30", 3) and step < base + 3:
            new = step + 1
        elif (today - made).days >= 21 and s.get("sales_30", 0) == 0 and step > max(1, base - 2):
            new = step - 1
        if new != step:
            acts.append({"product": p, "step": new, "cents": int(round(listing.LADDER[new] * 100)),
                         "why": f"{s.get('sales_30', 0)} sales in 30 days"})
    return acts


def stale_products(products, today) -> list[dict]:
    """Dated products whose year is over (2026 calendar in 2027) get archived."""
    out = []
    for p in products:
        md = p.get("metadata") or {}
        y = md.get("sp_year")
        if md.get("sp") and not p.get("is_archived") and y and y.isdigit():
            kind = KIND_BY_KEY.get(md.get("sp_kind"), {})
            over = int(y) < today.year or (kind.get("dated_this_year") and int(y) == today.year and today >= dt.date(today.year, 12, 27))
            if over:
                out.append(p)
    return out


def bundle_plans(products, st, cfg) -> list[dict]:
    """One 'collection' per theme once 3+ different products share it, at ~50% of the separate prices."""
    by_theme: dict[str, list] = {}
    bundles: dict[str, dict] = {}
    for p in products:
        md = p.get("metadata") or {}
        if not md.get("sp") or p.get("is_archived"):
            continue
        if md.get("sp_bundle"):
            bundles[md.get("sp_theme")] = p
        elif p.get("benefits"):
            by_theme.setdefault(md.get("sp_theme"), []).append(p)
    plans = []
    for theme_key, items in by_theme.items():
        kinds = {(p["metadata"].get("sp_kind")) for p in items}
        if len(kinds) < cfg.get("bundle_min_items", 3):
            continue
        old = bundles.get(theme_key)
        if old and int(old["metadata"].get("sp_count", 0)) >= len(items):
            continue
        theme = THEME_BY_KEY.get(theme_key)
        total = sum(_price(p) for p in items)
        i = listing.ladder_index(total / 100 * 0.5)
        names = [p["name"].split(" – ")[0] for p in items]
        desc = "\n".join([
            f"**Everything in the {theme.name if theme else theme_key} design, in one download - save about 50%.**",
            "", "### Included", *[f"- {n}" for n in names], "",
            "Each planner comes as A4 and US Letter PDFs plus low-ink versions. Instant download after checkout.",
            "", "For personal use. This is a digital product; nothing is shipped."])
        plans.append({"theme": theme_key, "old": old, "items": items, "cents": int(listing.LADDER[i] * 100),
                      "name": f"{theme.name if theme else theme_key} Planner Collection – {len(items)} Printables in 1 Bundle",
                      "description": desc,
                      "benefits": [b["id"] for p in items for b in p.get("benefits", [])],
                      "medias": [m["id"] for p in items for m in (p.get("medias") or [])[:1]][:8]})
    return plans


def _price(p) -> int:
    for pr in p.get("prices") or []:
        if pr.get("amount_type") == "fixed" and not pr.get("is_archived"):
            return pr.get("price_amount", 0)
    return 0


def campaign_due(today: dt.date) -> list[dict]:
    """Campaigns that should exist now (created a few days before they start)."""
    due = []
    for c in CAMPAIGNS:
        for year in (today.year, today.year + 1):
            sy = year
            ey = year + 1 if c["end"] < c["start"] else year
            start = dt.date(sy, *c["start"])
            end = dt.date(ey, *c["end"])
            if start - dt.timedelta(days=3) <= today <= end:
                due.append({**c, "start_date": start, "end_date": end, "tag": f"{c['key']}-{sy}"})
    return due


def active_campaign(discounts: list[dict], today: dt.date) -> dict | None:
    for d in discounts:
        md = d.get("metadata") or {}
        if not md.get("sp_campaign"):
            continue
        s, e = _d(d.get("starts_at")), _d(d.get("ends_at"))
        if (not s or s <= today) and (not e or today <= e):
            return d
    return None
