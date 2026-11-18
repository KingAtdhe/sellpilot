"""SellPilot daily cycle.

    python -m sellpilot run          # full automatic cycle (what the schedule runs)
    python -m sellpilot make -n 2    # just make products into ./out (no Polar needed)
    python -m sellpilot report       # print sales report
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import sys
import traceback

from . import factory, optimizer, publisher, research, storefront
from .polar import Polar, PolarError

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULTS = {
    "store_name": "Paper Pilot Studio",
    "headline": "Printable planners for a calmer life",
    "tagline": "Beautiful, practical printables you can download instantly, print at home or use on your tablet.",
    "site_url": "https://example.github.io/sellpilot/",
    "currency": "usd",
    "products_per_run": 3,
    "max_products": 400,
    "price_multiplier": 1.0,
    "price_tests": True,
    "raise_after_sales_30": 3,
    "bundles": True,
    "bundle_min_items": 3,
    "campaigns": True,
    "pins_per_run": 5,
    "only_kinds": [],
    "paused": False,
}


def load_config(path=None) -> dict:
    cfg = dict(DEFAULTS)
    path = path or os.path.join(HERE, "config.json")
    if os.path.exists(path):
        with open(path) as f:
            cfg.update(json.load(f))
    return cfg


class Log:
    def __init__(self):
        self.lines, self.errors = [], []

    def __call__(self, *a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True)
        self.lines.append(s)

    def err(self, where, e):
        msg = f"{where}: {e}"
        print("ERROR", msg, file=sys.stderr, flush=True)
        self.errors.append(msg)


def money(cents, cur):
    return f"{(cents or 0) / 100:.2f} {(cur or 'usd').upper()}"


def run(cfg, polar: Polar, today=None, live_research=True, site_dir=None, pinterest=None, rng=None, log=None):
    today = today or dt.date.today()
    log = log or Log()
    report = {"date": today.isoformat(), "made": [], "price_changes": [], "archived": [], "bundles": [],
              "campaign": None, "pins": 0}

    products = polar.products()
    ours = [p for p in products if (p.get("metadata") or {}).get("sp")]
    orders = polar.orders()
    st = optimizer.stats(ours, orders, today)
    tot = st["_total"]
    log(f"Shop: {len(ours)} products live · {tot['sales']} sales all time · earned {money(tot['earned'], tot['currency'])}"
        f" · last 30 days {tot['sales_30']} sales / {money(tot['earned_30'], tot['currency'])}")

    if cfg.get("paused"):
        log("Paused in settings - only syncing sales.")
    else:
        # 1. tidy: archive products whose date has passed
        for p in optimizer.stale_products(ours, today):
            try:
                polar.update_product(p["id"], is_archived=True)
                report["archived"].append(p["name"])
                log(f"Archived (out of date): {p['name']}")
            except Exception as e:
                log.err("archive", e)

        # 2. price tests
        if cfg.get("price_tests"):
            for a in optimizer.price_actions(ours, st, today, cfg):
                p = a["product"]
                try:
                    cur = cfg["currency"]
                    md = dict(p["metadata"], sp_step=a["step"], sp_pchg=today.isoformat())
                    polar.update_product(p["id"], prices=[{"amount_type": "fixed", "price_amount": a["cents"],
                                                           "price_currency": cur}], metadata=md)
                    report["price_changes"].append(f"{p['name'][:60]} -> {a['cents'] / 100:.2f} ({a['why']})")
                    log(f"Price: {p['name'][:60]} -> {a['cents'] / 100:.2f} ({a['why']})")
                except Exception as e:
                    log.err("price", e)

        # 3. make and publish new products
        active = [p for p in ours if not p.get("is_archived") and not p["metadata"].get("sp_bundle")]
        room = max(0, cfg["max_products"] - len(active))
        n = min(cfg["products_per_run"], room)
        picks = research.plan(ours, st, n, today, live=live_research, rng=rng, allowed=cfg.get("only_kinds") or None)
        for pick in picks:
            log(f"Making: {pick['kind']['key']} / {pick['theme'].name} ({pick['why']})")
            try:
                pkg = factory.make(pick, cfg, today)
                prod = publisher.publish(polar, pkg, cfg["currency"], log)
                report["made"].append(pkg.name)
                ours.append(prod)
            except Exception as e:
                log.err(f"make {pick['kind']['key']}", f"{e}\n{traceback.format_exc(limit=3)}")

        # 4. bundles
        if cfg.get("bundles"):
            fresh = [p for p in polar.products() if (p.get("metadata") or {}).get("sp")]
            for b in optimizer.bundle_plans(fresh, st, cfg):
                try:
                    md = {"sp": "1", "sp_bundle": "1", "sp_theme": b["theme"], "sp_count": len(b["items"]),
                          "sp_slug": f"collection-{b['theme']}-{len(b['items'])}", "sp_cat": "Bundles",
                          "sp_made": today.isoformat()}
                    publisher.publish_bundle(polar, b["name"], b["description"], b["cents"], cfg["currency"],
                                             b["benefits"], b["medias"], md)
                    if b["old"]:
                        polar.update_product(b["old"]["id"], is_archived=True)
                    report["bundles"].append(b["name"])
                    log(f"Bundle: {b['name']} at {b['cents'] / 100:.2f}")
                except Exception as e:
                    log.err("bundle", e)

        # 5. seasonal sale codes
        if cfg.get("campaigns"):
            try:
                existing = polar.discounts()
                tags = {(d.get("metadata") or {}).get("sp_campaign") for d in existing}
                for c in optimizer.campaign_due(today):
                    if c["tag"] in tags:
                        continue
                    code = f"{c['code']}{str(c['start_date'].year)[2:]}"
                    polar.create_discount(c["name"], code, c["pct"], f"{c['start_date']}T00:00:00Z",
                                          f"{c['end_date']}T23:59:59Z", metadata={"sp_campaign": c["tag"]})
                    log(f"Sale scheduled: {c['name']} {c['pct']}% code {code} ({c['start_date']} - {c['end_date']})")
            except Exception as e:
                log.err("campaign", e)

    # 6. storefront + promotion
    try:
        disc = polar.discounts() if cfg.get("campaigns") else []
        camp = optimizer.active_campaign(disc, today)
        report["campaign"] = camp and camp.get("code")
    except Exception as e:
        camp = None
        log.err("discounts", e)
    final = [p for p in polar.products() if (p.get("metadata") or {}).get("sp")]
    if site_dir:
        n = storefront.build(final, cfg, site_dir, camp)
        log(f"Storefront: {n} products -> {cfg['site_url']}")
    if pinterest and not cfg.get("paused"):
        site = cfg["site_url"].rstrip("/") + "/"
        for p in [p for p in final if not p["metadata"].get("sp_pin") and not p.get("is_archived")][:cfg["pins_per_run"]]:
            try:
                medias = p.get("medias") or []
                img = medias[-1]["public_url"] if medias else None
                if not img:
                    continue
                desc = p["name"] + ". " + (p["metadata"].get("sp_tags") or "")
                if camp:
                    desc = f"{camp['name']}: use code {camp.get('code')} at checkout. " + desc
                pinterest.pin(p["name"].split(" | ")[0], desc, f"{site}p/{p['metadata'].get('sp_slug')}.html", img)
                polar.update_product(p["id"], metadata=dict(p["metadata"], sp_pin=today.isoformat()))
                report["pins"] += 1
            except Exception as e:
                log.err("pinterest", e)
                break
        log(f"Pinterest: {report['pins']} new pins")
    report["totals"] = {k: v for k, v in tot.items() if k != "by_day"}
    report["errors"] = log.errors
    return report


def summary_md(report, cfg) -> str:
    t = report.get("totals", {})
    cur = t.get("currency") or cfg["currency"]
    lines = [f"## SellPilot run {report['date']}",
             f"**Earned:** today {money(t.get('earned_today'), cur)} · 30 days {money(t.get('earned_30'), cur)} "
             f"· all time {money(t.get('earned'), cur)} ({t.get('sales', 0)} sales)", ""]
    for key, label in [("made", "New products"), ("price_changes", "Price changes"), ("bundles", "Bundles"),
                       ("archived", "Archived"), ("errors", "Problems")]:
        if report.get(key):
            lines.append(f"**{label}**")
            lines += [f"- {x.splitlines()[0]}" for x in report[key]]
            lines.append("")
    return "\n".join(lines)


def make_local(cfg, n, out, today=None):
    today = today or dt.date.today()
    os.makedirs(out, exist_ok=True)
    for pick in research.plan([], {}, n, today, live=True, allowed=cfg.get("only_kinds") or None):
        pkg = factory.make(pick, cfg, today)
        d = os.path.join(out, pkg.metadata["sp_slug"])
        os.makedirs(d, exist_ok=True)
        for name, data in list(pkg.files.items()) + pkg.images + [pkg.pin]:
            with open(os.path.join(d, name), "wb") as f:
                f.write(data)
        with open(os.path.join(d, "listing.md"), "w") as f:
            f.write(f"# {pkg.name}\n\nPrice: {pkg.price_cents / 100:.2f}\n\nTags: {', '.join(pkg.tags)}\n\n{pkg.description}\n")
        print("made", d)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sellpilot")
    ap.add_argument("cmd", choices=["run", "make", "report"])
    ap.add_argument("-n", type=int, default=2)
    ap.add_argument("--out", default="out")
    ap.add_argument("--site", default=None)
    ap.add_argument("--config", default=None)
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    if a.cmd == "make":
        return make_local(cfg, a.n, a.out)
    token = os.environ.get("POLAR_TOKEN")
    if not token:
        sys.exit("POLAR_TOKEN is not set. Add it as a repository secret (see README).")
    polar = Polar(token, os.environ.get("POLAR_SERVER", "production"))
    if a.cmd == "report":
        ours = [p for p in polar.products() if (p.get("metadata") or {}).get("sp")]
        st = optimizer.stats(ours, polar.orders())
        print(json.dumps(st["_total"], indent=2))
        return
    pin = None
    if all(os.environ.get(k) for k in ("PINTEREST_APP_ID", "PINTEREST_APP_SECRET", "PINTEREST_REFRESH_TOKEN", "PINTEREST_BOARD_ID")):
        from .pinterest import Pinterest
        pin = Pinterest(os.environ["PINTEREST_APP_ID"], os.environ["PINTEREST_APP_SECRET"],
                        os.environ["PINTEREST_REFRESH_TOKEN"], os.environ["PINTEREST_BOARD_ID"])
    log = Log()
    try:
        report = run(cfg, polar, site_dir=a.site, pinterest=pin, log=log)
    except PolarError as e:
        if e.status in (401, 403):
            sys.exit(f"Polar refused the token ({e.status}). Create a new Organization Access Token with all scopes.")
        raise
    md = summary_md(report, cfg)
    print(md)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(md + "\n")
    os.makedirs(os.path.join(HERE, "state"), exist_ok=True)
    with open(os.path.join(HERE, "state", "last_run.json"), "w") as f:
        json.dump({"date": report["date"], "made": len(report["made"]), "errors": len(report["errors"])}, f)
    if report["errors"] and not report["made"] and cfg["products_per_run"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
