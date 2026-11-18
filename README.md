# SellPilot

A fully automatic bot that **makes, sells and promotes digital products** every day, plus an Android app that
shows what it earned.

Every day it:

1. **Researches** what to make: season (seasonal printables sell when listed 6-12 weeks early), live Google
   search suggestions, what already sells in your shop, and what you already have.
2. **Makes** a professional printable product: a multi-page PDF in A4 and US Letter plus low-ink versions,
   with bookmarks and a clickable contents page for tablets (GoodNotes, Notability). 17 product types,
   63 page designs, 12 colour themes.
3. **Creates listing photos** from the real pages (hero, what's inside, close-up, tablet) and a Pinterest pin.
4. **Writes the listing**: search-friendly title, description, tags, price.
5. **Puts it on sale on Polar** with instant delivery: the buyer pays, gets a download link by email, done.
6. **Sells smarter over time**:
   - price tests: slow sellers drop one step after 3 weeks, proven sellers go up a step (max one change per 2 weeks)
   - **bundles**: when 3+ products share a design, a "collection" bundle at about half price appears
   - **seasonal sales**: Black Friday, New Year, Spring, Mid-year and Back to School codes are created on time and
     shown on the shop website and pins
   - out-of-date products (last year's calendar) are archived automatically
7. **Promotes**: rebuilds your shop website (SEO pages with Google product data and a sitemap) and posts new
   products to Pinterest.
8. **Reports**: earnings after fees in the app and in each run summary on GitHub.

No human step is needed per product. That is why it sells through **Polar** and not Etsy or Gumroad: Etsy wants a
person to approve AI/automated listings and Gumroad's API cannot create products.

## Why Polar
- **Merchant of record**: Polar is the legal seller, so it charges and pays EU VAT and other sales taxes for you.
  You do not need a registered business or a VAT number to start. You still report your own income.
- Full API: products, files, delivery, discount codes, sales.
- Fee for new shops (Starter plan): **5% + $0.50 per sale**, plus small payout fees. Prices never go under $3.99 so
  the fixed fee does not eat small sales.

## Set up once (about 15 minutes, all from your phone)

**1. Polar**
1. Sign up at polar.sh, create an organization (your shop name), and finish **Settings > Payouts** (identity check
   and bank account) so you can receive money.
2. **Settings > Developers > New token** (Organization Access Token), select **all scopes**, no expiry. Copy it.

**2. This repository**
1. **Settings > Secrets and variables > Actions > New repository secret**: name `POLAR_TOKEN`, paste the token.
2. **Settings > Pages > Source: GitHub Actions** (for your shop website).
3. Edit `bot/config.json`: shop name, and `site_url` = `https://<your-github-name>.github.io/<repo-name>/`.
4. **Actions > SellPilot bot > Run workflow**. In ~5 minutes the first 3 products are on sale and the website is live.

From then on it runs **every day at 06:23** by itself. Keep the repository **public**: scheduled runs are then free
(the product files never go into the repository; only previews are public on your website).

Want to test first? Add a repository **variable** (not secret) `POLAR_SERVER` = `sandbox` and use a token from
sandbox.polar.sh. Delete the variable to go live.

**3. The app**
Every change to `app/` builds an APK: **Releases > newest SellPilot-N.apk** on your phone, install. In the app's
Settings paste your Polar token, the repo name, a GitHub fine-grained token (this repo only, **Contents** and
**Actions**: read and write) and your website address. From the app you can see earnings, best sellers and every
sale, run the bot now, pause it, and change products per day, price level, currency, which product types to make,
bundles, sales and price tests.

**4. Pinterest (optional, recommended)**
Pinterest is the biggest free traffic source for printables. Create an app at developers.pinterest.com, get a
refresh token with `pins:write` and `boards:read`, then add secrets `PINTEREST_APP_ID`, `PINTEREST_APP_SECRET`,
`PINTEREST_REFRESH_TOKEN`, `PINTEREST_BOARD_ID`. New pins appear daily (5 by default), linking to your shop pages.
New Pinterest apps start in trial access; pins become public once Pinterest grants Standard access.

## Settings (`bot/config.json`, also editable in the app)
| Setting | Default | Meaning |
|---|---|---|
| `products_per_run` | 3 | new products each day |
| `max_products` | 400 | stop making new ones at this many live products |
| `price_multiplier` | 1.0 | 1.2 = all new prices 20% higher |
| `currency` | usd | currency for new products (usd, eur, gbp) |
| `price_tests`, `bundles`, `campaigns` | true | the automatic selling features above |
| `pins_per_run` | 5 | Pinterest pins per day |
| `only_kinds` | [] | limit to some product types, e.g. `["budget-planner","wedding-planner"]` |
| `paused` | false | only sync sales, make nothing |

## Product types
Yearly planner, printable calendar, budget planner, meal planner, fitness planner, self-care journal, reading
journal, cleaning planner, student planner, teacher planner, small business planner, wedding planner, baby log,
pet planner, travel planner, Christmas planner, New Year planner. Add more in `bot/sellpilot/catalog.py` (pages are
in `render/pages.py`).

## Run it on your phone (Termux)
```
pkg install python
cd bot && pip install -r requirements.txt
python -m sellpilot make -n 2           # makes 2 products into ./out to look at
POLAR_TOKEN=... python -m sellpilot run  # one full cycle
```

## Tests
`cd bot && python -m unittest discover -s tests -t .` runs the whole selling cycle against a fake Polar API
(publishing, retries, failures, price tests, bundles, sale codes, archiving, every product type). They run on every
push.

## Good to know
- Expect the first sales after a few weeks: new websites and pins need time to be found. More products and
  Pinterest speed this up.
- Products are designed by code (no AI images or AI text), and every listing photo shows the real pages.
- Product files are for buyers' personal use; Polar handles refunds and receipts.
- Fonts: DM Serif Display, Poppins, Great Vibes, Amatic SC (SIL Open Font License, `bot/sellpilot/fonts/OFL.txt`).
