"""Static, search-engine friendly shop website (deployed free to GitHub Pages).

Every product gets its own page with structured data (Google Shopping-style
rich results), a sitemap, and a Buy button that opens Polar's checkout.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re

CSS = """
:root{--ink:#24221f;--muted:#6d675f;--line:#e7e1d8;--bg:#fbf9f6;--brand:#3f5e4b;--accent:#c2a15a}
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg);line-height:1.55}
a{color:inherit}.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
header{border-bottom:1px solid var(--line);background:#fff;position:sticky;top:0;z-index:5}
header .wrap{display:flex;align-items:center;justify-content:space-between;height:64px}
.logo{font-family:Georgia,'Times New Roman',serif;font-size:24px;text-decoration:none;font-style:italic}
.banner{background:var(--brand);color:#fff;text-align:center;padding:9px 14px;font-size:14px;letter-spacing:.02em}
.banner b{background:#fff;color:var(--brand);padding:2px 8px;border-radius:4px;margin:0 4px}
.hero{padding:56px 0 28px}.hero h1{font-family:Georgia,serif;font-weight:400;font-size:clamp(32px,5vw,52px);margin:0 0 10px;line-height:1.1}
.hero p{color:var(--muted);max-width:620px;margin:0;font-size:17px}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:26px 0 8px}.chip{border:1px solid var(--line);background:#fff;border-radius:99px;padding:7px 14px;font-size:14px;cursor:pointer}
.chip.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:22px;padding:18px 0 60px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;text-decoration:none;display:flex;flex-direction:column;transition:transform .15s,box-shadow .15s}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 30px rgba(0,0,0,.07)}
.card img{width:100%;aspect-ratio:4/3;object-fit:cover;background:#eee}.card .b{padding:14px 16px 16px}
.card h3{font-size:15px;font-weight:600;margin:0 0 6px;line-height:1.35}.price{font-weight:700}.was{color:var(--muted);text-decoration:line-through;font-weight:400;margin-left:6px;font-size:14px}
.cat{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);font-weight:600}
.pd{display:grid;grid-template-columns:1.25fr 1fr;gap:44px;padding:36px 0 70px}@media(max-width:860px){.pd{grid-template-columns:1fr}}
.gal img{width:100%;border-radius:12px;border:1px solid var(--line);margin-bottom:14px;background:#fff}
.pd h1{font-family:Georgia,serif;font-weight:400;font-size:34px;line-height:1.15;margin:6px 0 14px}
.buy{display:block;text-align:center;background:var(--ink);color:#fff;text-decoration:none;padding:16px;border-radius:10px;font-weight:600;font-size:17px;margin:18px 0 10px}
.buy:hover{background:#000}.trust{font-size:13px;color:var(--muted);display:grid;gap:4px;margin-bottom:22px}
.desc h3{font-size:16px;margin:22px 0 6px}.desc ul,.desc ol{padding-left:20px;margin:6px 0}.desc p{margin:8px 0}
footer{border-top:1px solid var(--line);padding:30px 0;color:var(--muted);font-size:14px;background:#fff}
"""


def _md(text: str) -> str:
    """Tiny markdown to HTML (headings, lists, bold, italics, paragraphs)."""
    out, lst = [], None
    for raw in text.split("\n"):
        line = html.escape(raw.strip())
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        line = re.sub(r"\*(.+?)\*", r"<i>\1</i>", line)
        m_ul, m_ol = re.match(r"^- (.*)", line), re.match(r"^\d+\. (.*)", line)
        tag = "ul" if m_ul else "ol" if m_ol else None
        if lst and tag != lst:
            out.append(f"</{lst}>")
            lst = None
        if tag:
            if not lst:
                out.append(f"<{tag}>")
                lst = tag
            out.append(f"<li>{(m_ul or m_ol).group(1)}</li>")
        elif line.startswith("### "):
            out.append(f"<h3>{line[4:]}</h3>")
        elif line:
            out.append(f"<p>{line}</p>")
    if lst:
        out.append(f"</{lst}>")
    return "\n".join(out)


def _price(p):
    for pr in p.get("prices") or []:
        if pr.get("amount_type") == "fixed" and not pr.get("is_archived"):
            return pr.get("price_amount", 0), pr.get("price_currency", "usd")
    return 0, "usd"


def _money(cents, cur):
    sym = {"usd": "$", "eur": "€", "gbp": "£"}.get(cur.lower(), cur.upper() + " ")
    return f"{sym}{cents / 100:.2f}"


def _page(title, desc, body, cfg, canonical, banner="", extra_head=""):
    t = html.escape(title)
    d = html.escape(desc[:300])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{t}</title>
<meta name="description" content="{d}"><link rel="canonical" href="{canonical}">
<meta property="og:title" content="{t}"><meta property="og:description" content="{d}">
<meta property="og:type" content="website"><meta property="og:url" content="{canonical}">{extra_head}
<style>{CSS}</style></head><body>{banner}
<header><div class="wrap"><a class="logo" href="{cfg['site_url']}">{html.escape(cfg['store_name'])}</a>
<span style="font-size:14px;color:#6d675f">Printable planners · instant download</span></div></header>
{body}
<footer><div class="wrap">© {dt.date.today().year} {html.escape(cfg['store_name'])} · Digital downloads for personal use ·
Payments, tax and delivery by Polar (merchant of record). Questions or refunds: use the link in your receipt email.</div></footer>
</body></html>"""


def build(products: list[dict], cfg: dict, out_dir: str, campaign: dict | None = None):
    os.makedirs(os.path.join(out_dir, "p"), exist_ok=True)
    site = cfg["site_url"].rstrip("/") + "/"
    live = [p for p in products if (p.get("metadata") or {}).get("sp") and not p.get("is_archived")
            and (p.get("metadata") or {}).get("sp_link") and p.get("visibility", "public") == "public"]
    live.sort(key=lambda p: ((p["metadata"].get("sp_bundle") != "1"), p.get("created_at", "")), reverse=False)
    live = sorted(live, key=lambda p: (0 if p["metadata"].get("sp_bundle") else 1, -_ts(p)))
    banner = ""
    pct = 0
    if campaign:
        pct = (campaign.get("basis_points") or 0) / 100
        banner = (f'<div class="banner">{html.escape(campaign["name"])}: {pct:.0f}% off everything with code '
                  f'<b>{html.escape(campaign.get("code") or "")}</b> at checkout</div>')
    cats = sorted({p["metadata"].get("sp_cat", "Other") for p in live})
    cards = []
    urls = [site]
    for p in live:
        md = p["metadata"]
        slug = md.get("sp_slug") or p["id"]
        cents, cur = _price(p)
        img = (p.get("medias") or [{}])[0].get("public_url", "")
        name = p["name"].split(" | ")[0]
        cards.append(f'<a class="card" data-cat="{html.escape(md.get("sp_cat", "Other"))}" href="p/{slug}.html">'
                     f'<img loading="lazy" src="{img}" alt="{html.escape(name)}"><div class="b">'
                     f'<div class="cat">{html.escape(md.get("sp_cat", ""))}</div><h3>{html.escape(name)}</h3>'
                     f'<span class="price">{_money(cents, cur)}</span></div></a>')
        gallery = "".join(f'<img src="{m["public_url"]}" alt="{html.escape(name)} preview {i + 1}" loading="lazy">'
                          for i, m in enumerate((p.get("medias") or [])[:4]))
        ld = {"@context": "https://schema.org", "@type": "Product", "name": name,
              "image": [m["public_url"] for m in (p.get("medias") or [])[:4]],
              "description": (p.get("description") or "")[:500], "brand": {"@type": "Brand", "name": cfg["store_name"]},
              "sku": slug, "category": md.get("sp_cat", ""),
              "offers": {"@type": "Offer", "price": f"{cents / 100:.2f}", "priceCurrency": cur.upper(),
                         "availability": "https://schema.org/InStock", "url": f"{site}p/{slug}.html"}}
        body = f"""<div class="wrap pd"><div class="gal">{gallery}</div><div>
<div class="cat">{html.escape(md.get('sp_cat', ''))}</div><h1>{html.escape(p['name'])}</h1>
<div class="price" style="font-size:26px">{_money(cents, cur)}</div>
<a class="buy" href="{md['sp_link']}" rel="nofollow">Buy now · instant download</a>
<div class="trust"><span>✓ Download link emailed right after payment</span><span>✓ Secure checkout, taxes included where required</span>
<span>✓ A4 + US Letter + low-ink PDFs</span></div>
<div class="desc">{_md(p.get('description') or '')}</div></div></div>"""
        extra = (f'<meta property="og:image" content="{img}"><script type="application/ld+json">'
                 f'{json.dumps(ld)}</script>')
        with open(os.path.join(out_dir, "p", f"{slug}.html"), "w") as f:
            f.write(_page(f"{name} | {cfg['store_name']}", (p.get('description') or name).replace("*", ""), body, cfg,
                          f"{site}p/{slug}.html", banner, extra))
        urls.append(f"{site}p/{slug}.html")
    chips = '<span class="chip on" data-c="">All</span>' + "".join(
        f'<span class="chip" data-c="{html.escape(c)}">{html.escape(c)}</span>' for c in cats)
    body = f"""<div class="wrap"><section class="hero"><h1>{html.escape(cfg.get('headline', 'Printable planners for a calmer life'))}</h1>
<p>{html.escape(cfg.get('tagline', 'Beautiful, practical printables you can download instantly, print at home or use on your tablet.'))}</p>
<div class="chips">{chips}</div></section><div class="grid" id="g">{''.join(cards) or '<p>New printables are on their way.</p>'}</div></div>
<script>document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));
c.classList.add('on');document.querySelectorAll('.card').forEach(k=>k.style.display=(!c.dataset.c||k.dataset.cat===c.dataset.c)?'':'none')}})</script>"""
    with open(os.path.join(out_dir, "index.html"), "w") as f:
        f.write(_page(f"{cfg['store_name']} – Printable Planners & Templates", cfg.get("tagline", "Printable planners"),
                      body, cfg, site, banner))
    today = dt.date.today().isoformat()
    with open(os.path.join(out_dir, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                + "".join(f"<url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls) + "</urlset>")
    with open(os.path.join(out_dir, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {site}sitemap.xml\n")
    open(os.path.join(out_dir, ".nojekyll"), "w").close()
    return len(live)


def _ts(p):
    try:
        return dt.datetime.fromisoformat(p.get("created_at", "").replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0
