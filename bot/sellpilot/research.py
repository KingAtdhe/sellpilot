"""Decides what to make next.

Score per product kind =
    base demand (catalog)
  x seasonal timing (list 6-12 weeks before the buying season)
  x live search interest (Google autocomplete depth for the main keywords)
  x what already sells in this shop (winners get more variations)
  / saturation (how many we already have of that kind)
Then a theme is chosen that this kind does not have yet, favouring themes of
best sellers.
"""
from __future__ import annotations

import datetime as dt
import json
import random
import urllib.parse
import urllib.request

from .catalog import KINDS, fmt, kind_year, season_boost
from .render.kit import THEMES

SUGGEST = "https://suggestqueries.google.com/complete/search?client=firefox&hl=en&q="


def google_suggest(q: str, timeout=8) -> list[str]:
    try:
        req = urllib.request.Request(SUGGEST + urllib.parse.quote(q), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        return [s for s in data[1] if isinstance(s, str)]
    except Exception:
        return []


def search_interest(kind: dict, year: int, live: bool = True) -> tuple[float, list[str]]:
    """0.8-1.3 multiplier from autocomplete depth, plus long-tail phrases for SEO."""
    if not live:
        return 1.0, []
    seeds = [fmt(k, year) for k in kind["keywords"][:2]]
    phrases, depth = [], 0
    for s in seeds:
        sug = google_suggest(s + " ")
        depth += len(sug)
        phrases += [p for p in sug if len(p) <= 40]
        if "printable" not in s:
            sug2 = google_suggest(s + " printable")
            depth += len(sug2) * 0.5
            phrases += [p for p in sug2 if len(p) <= 40]
    if depth == 0:
        return 1.0, []
    mult = 0.8 + min(depth, 30) / 30 * 0.5
    seen, uniq = set(), []
    for p in phrases:
        if p not in seen and not any(b in p for b in BANNED):
            seen.add(p)
            uniq.append(p)
    return round(mult, 3), uniq[:15]


# trademarks / brands we must never use in titles or tags
BANNED = ["happy planner", "erin condren", "goodnotes 6 template by", "disney", "cricut", "canva pro", "etsy", "amazon",
          "notion", "harry potter", "taylor swift", "barbie", "hobonichi", "passion planner", "clever fox", "panda planner"]


def plan(products: list[dict], stats: dict, n: int, today: dt.date | None = None, live: bool = True,
         rng: random.Random | None = None, allowed: list[str] | None = None) -> list[dict]:
    """Return up to n picks: {kind, theme, year, score, phrases, why}."""
    today = today or dt.date.today()
    rng = rng or random.Random()
    have: dict[str, set] = {}
    sold_kind: dict[str, float] = {}
    sold_theme: dict[str, float] = {}
    for p in products:
        md = p.get("metadata") or {}
        k = md.get("sp_kind")
        if not k or md.get("sp_bundle"):
            continue
        have.setdefault(f"{k}:{md.get('sp_year', '')}", set()).add(md.get("sp_theme"))
        s = stats.get(p["id"], {})
        sold_kind[k] = sold_kind.get(k, 0) + s.get("sales_30", 0) * 2 + s.get("sales", 0)
        sold_theme[md.get("sp_theme")] = sold_theme.get(md.get("sp_theme"), 0) + s.get("sales", 0)

    scored = []
    for kind in KINDS:
        if allowed and kind["key"] not in allowed:
            continue
        year = kind_year(kind, today)
        sb = season_boost(kind, today.month)
        if sb == 0:
            continue
        themes_have = have.get(f"{kind['key']}:{year if kind.get('dated') else ''}", set())
        if len(themes_have) >= len(THEMES):
            continue
        interest, phrases = search_interest(kind, year, live)
        winners = 1 + min(sold_kind.get(kind["key"], 0), 20) / 10      # up to x3
        saturation = 1 + len(themes_have) * 0.35
        score = kind["demand"] * sb * interest * winners / saturation
        scored.append({"kind": kind, "year": year, "score": round(score, 3), "phrases": phrases,
                       "why": f"demand {kind['demand']} x season {sb} x search {interest} x sales {winners:.2f} / have {len(themes_have)}",
                       "themes_have": themes_have})
    picks = []
    pool = list(scored)
    while pool and len(picks) < n:
        tot = sum(s["score"] for s in pool)
        r = rng.random() * tot
        acc = 0
        for s in pool:
            acc += s["score"]
            if acc >= r:
                break
        free = [t for t in THEMES if t.key not in s["themes_have"]]
        free.sort(key=lambda t: -(sold_theme.get(t.key, 0) + rng.random()))
        theme = free[0]
        s["themes_have"].add(theme.key)
        picks.append({**{k: v for k, v in s.items() if k != "themes_have"}, "theme": theme})
        pool.remove(s)   # one per kind per run keeps the shop varied
    return picks
