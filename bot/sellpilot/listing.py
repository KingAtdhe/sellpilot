"""Listing copy and prices."""
from __future__ import annotations

from .catalog import fmt

LADDER = [2.99, 3.99, 4.99, 5.99, 6.99, 7.99, 8.99, 9.99, 11.99, 12.99, 14.99, 17.99, 19.99, 24.99, 29.99]


def ladder_index(price: float) -> int:
    return min(range(len(LADDER)), key=lambda i: abs(LADDER[i] - price))


def launch_price(kind: dict, page_count: int, multiplier: float = 1.0) -> tuple[int, int]:
    """(cents, ladder step). Bigger products cost a little more."""
    base = kind["base_price"] * multiplier
    if page_count >= 30:
        base += 2
    elif page_count >= 12:
        base += 1
    i = max(1, ladder_index(base))   # never under 3.99: Polar's fixed 50c fee would eat cheap sales
    return int(round(LADDER[i] * 100)), i


def title_for(kind, theme, year) -> tuple[str, str]:
    """(short title for cover/images, full listing title for search)."""
    short = fmt(kind["name"], year)
    sub = kind["subtitle"]
    full = f"{short} – {theme.name} | Printable {sub.title().replace('&', 'and')} | A4 & US Letter PDF"
    return short, full[:120]


def features(kind, page_count, sections, has_contents=False) -> list[str]:
    return [
        f"{page_count} pages: {', '.join(s.lower() for s in sections[:4])} and more",
        "A4 and US Letter sizes - print at home or at a print shop",
        "Low-ink versions included to save printer ink",
        "Works in GoodNotes, Notability and any PDF app",
        "Clickable contents page to jump between sections" if has_contents else
        "Clean, uncluttered layouts with room to write",
        "Instant download right after checkout",
    ]


def description(kind, theme, year, page_count, sections, phrases, store_name) -> str:
    short = fmt(kind["name"], year)
    lines = [
        f"**{short} in the {theme.name} design** - made for {kind['audience']}.",
        "",
        f"A printable {kind['subtitle']} set you can download right after checkout, print at home "
        "and start using today. Prefer paper-free? Import it into GoodNotes, Notability or any PDF app.",
        "",
        "### What's inside",
    ]
    lines += [f"- {s}" for s in sections]
    lines += [
        "",
        "### What you get",
        f"- {page_count}-page PDF in **A4** and **US Letter**",
        "- **Low-ink** version of both sizes",
        "- Bookmarks in every file; tap the contents page to jump to a section",
        "",
        "### How it works",
        "1. Complete checkout - you get a download link by email straight away.",
        "2. Download the PDF files (also available any time in your customer portal).",
        "3. Print at 100% / actual size, or open in your favourite tablet app.",
        "",
        "### Good to know",
        "- This is a **digital product**; nothing is shipped.",
        "- For personal use. Please do not share or resell the files.",
        "- Colours can look slightly different on screen and on paper.",
    ]
    if phrases:
        lines += ["", "*Great for: " + ", ".join(phrases[:8]) + ".*"]
    lines += ["", f"Designed by {store_name}."]
    return "\n".join(lines)


def tags_for(kind, theme, year, phrases) -> list[str]:
    tags, seen = [], set()
    for t in [fmt(k, year) for k in kind["keywords"]] + list(theme.tags) + phrases:
        t = t.lower().strip()
        if t and t not in seen and len(t) <= 40:
            seen.add(t)
            tags.append(t)
    return tags[:20]
