"""End-to-end tests: python -m unittest discover -s tests"""
import datetime as dt
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sellpilot import main, optimizer, research  # noqa: E402
from sellpilot.catalog import KINDS  # noqa: E402
from sellpilot.polar import Polar  # noqa: E402
from tests.fake_polar import FakePolar  # noqa: E402


def cfg(**kw):
    c = dict(main.DEFAULTS, site_url="https://x.github.io/shop/", products_per_run=2)
    c.update(kw)
    return c


class Cycle(unittest.TestCase):
    def setUp(self):
        self.fake = FakePolar()
        self.polar = Polar("t", base_url="https://api.fake", opener=self.fake)
        import sellpilot.polar as sp
        sp.time.sleep = lambda s: None

    def run_day(self, day, **kw):
        site = tempfile.mkdtemp()
        rep = main.run(cfg(**kw), self.polar, today=day, live_research=False, site_dir=site, rng=random.Random(1),
                       log=main.Log())
        return rep, site

    def test_first_run_publishes_sellable_products(self):
        rep, site = self.run_day(dt.date(2026, 11, 18))
        self.assertEqual(len(rep["made"]), 2, rep)
        self.assertEqual(rep["errors"], [])
        for p in self.fake.products.values():
            self.assertTrue(p["metadata"]["sp_link"].startswith("https://buy.polar.sh/"))
            self.assertEqual(len(p["benefits"]), 1)
            self.assertEqual(len(p["benefits"][0]["properties"]["files"]), 4)   # A4, Letter, 2x low ink
            self.assertEqual(len(p["medias"]), 5)
            self.assertGreaterEqual(p["prices"][0]["price_amount"], 299)
        html = open(os.path.join(site, "index.html")).read()
        self.assertIn("buy", open(os.path.join(site, "p", os.listdir(os.path.join(site, "p"))[0])).read())
        self.assertIn("card", html)
        self.assertTrue(os.path.exists(os.path.join(site, "sitemap.xml")))
        # Black Friday sale is due (starts Nov 23, scheduled 3 days ahead? not yet on Nov 18)
        self.assertEqual(len(self.fake.discounts), 0)

    def test_campaign_bundle_and_price_tests_over_time(self):
        self.run_day(dt.date(2026, 11, 18), products_per_run=3)
        rep, site = self.run_day(dt.date(2026, 11, 21), products_per_run=0)
        self.assertEqual(len(self.fake.discounts), 1)
        code = list(self.fake.discounts.values())[0]["code"]
        self.assertEqual(code, "BLACKFRIDAY26")
        # running again must not duplicate the sale
        self.run_day(dt.date(2026, 11, 22), products_per_run=0)
        self.assertEqual(len(self.fake.discounts), 1)
        # banner shows during the sale
        rep, site = self.run_day(dt.date(2026, 11, 25), products_per_run=0)
        self.assertIn("BLACKFRIDAY26", open(os.path.join(site, "index.html")).read())
        # sell one product a lot, leave others unsold for > 21 days
        pids = list(self.fake.products)
        hot = pids[0]
        for d in range(4):
            self.fake.sell(hot, 999, f"2026-12-{10 + d:02d}")
        rep, _ = self.run_day(dt.date(2026, 12, 15), products_per_run=0)
        changes = " ".join(rep["price_changes"])
        self.assertIn("4 sales", changes)
        self.assertIn("0 sales", changes)
        self.assertEqual(rep["totals"]["sales"], 4)
        self.assertEqual(rep["totals"]["earned"], 4 * (999 - 49))
        # no second change within 14 days
        rep, _ = self.run_day(dt.date(2026, 12, 20), products_per_run=0)
        self.assertEqual(rep["price_changes"], [])

    def test_bundle_when_three_kinds_share_a_theme(self):
        # force three different kinds in the same theme by limiting themes to one
        from sellpilot.render import kit
        keep = kit.THEMES[:]
        research.THEMES[:] = keep[:1]
        try:
            for i, k in enumerate(["budget-planner", "meal-planner", "reading-journal"]):
                self.run_day(dt.date(2026, 11, 18), products_per_run=1, only_kinds=[k], bundles=False)
            rep, site = self.run_day(dt.date(2026, 11, 19), products_per_run=0)
        finally:
            research.THEMES[:] = keep
        self.assertEqual(len(rep["bundles"]), 1, rep)
        b = [p for p in self.fake.products.values() if p["metadata"].get("sp_bundle")][0]
        self.assertEqual(len(b["benefits"]), 3)
        singles = sum(p["prices"][0]["price_amount"] for p in self.fake.products.values() if not p["metadata"].get("sp_bundle"))
        self.assertLess(b["prices"][0]["price_amount"], singles * 0.6)
        # no duplicate bundle next run
        rep, _ = self.run_day(dt.date(2026, 11, 20), products_per_run=0)
        self.assertEqual(rep["bundles"], [])

    def test_out_of_date_products_get_archived(self):
        self.run_day(dt.date(2026, 11, 18), products_per_run=1, only_kinds=["wall-calendar"])
        p = list(self.fake.products.values())[0]
        self.assertEqual(p["metadata"]["sp_year"], "2027")
        rep, _ = self.run_day(dt.date(2028, 1, 2), products_per_run=0)
        self.assertTrue(p["is_archived"])

    def test_retries_server_errors_and_survives_one_failed_product(self):
        self.fake.fail_next = [("POST", r"^/v1/files/$", 503)]
        rep, _ = self.run_day(dt.date(2026, 11, 18))
        self.assertEqual(len(rep["made"]), 2)
        self.fake.fail_next = [("POST", r"^/v1/benefits/$", 422)]
        rep, _ = self.run_day(dt.date(2026, 11, 18))
        self.assertEqual(len(rep["made"]), 1)
        self.assertEqual(len(rep["errors"]), 1)

    def test_paused(self):
        rep, _ = self.run_day(dt.date(2026, 11, 18), paused=True)
        self.assertEqual(rep["made"], [])


class Research(unittest.TestCase):
    def test_seasonality(self):
        nov = research.plan([], {}, 20, dt.date(2026, 11, 18), live=False, rng=random.Random(0))
        keys = [p["kind"]["key"] for p in nov]
        self.assertIn("christmas-planner", keys)
        apr = research.plan([], {}, 20, dt.date(2027, 4, 10), live=False, rng=random.Random(0))
        self.assertNotIn("christmas-planner", [p["kind"]["key"] for p in apr])
        top_nov = sorted(nov, key=lambda p: -p["score"])[0]["kind"]["key"]
        self.assertIn(top_nov, ("christmas-planner", "wall-calendar", "annual-planner"))

    def test_every_kind_renders(self):
        from sellpilot import factory
        c = cfg()
        for kind in KINDS:
            from sellpilot.render.kit import THEMES
            pkg = factory.make({"kind": kind, "theme": THEMES[0], "year": 2027, "phrases": []}, c, dt.date(2026, 11, 18))
            self.assertEqual(len(pkg.files), 4, kind["key"])
            self.assertEqual(len(pkg.images), 4)
            self.assertLessEqual(len(pkg.name), 120)
            for data in pkg.files.values():
                self.assertTrue(data.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
