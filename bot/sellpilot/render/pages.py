"""Printable page templates. Each template draws one page on a Page helper.

Templates take keyword params (year, month, title...). PAGES maps a key to
(function, human label) so products are just lists of page specs.
"""
from __future__ import annotations

import calendar
import datetime as dt

from .kit import Page, wrap

MONTHS = list(calendar.month_name)[1:]
DAYS_MON = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _week_days(start: str):
    return DAYS_MON if start == "monday" else ["Sunday"] + DAYS_MON[:-1]


# ---------------------------------------------------------------- covers / info
def cover(p: Page, title="Planner", subtitle="", year=None, tagline=""):
    W, H, t, cv = p.W, p.H, p.t, p.cv
    cv.setFillColor(t.c("paper"))
    cv.rect(0, 0, W, H, stroke=0, fill=1)
    if not p.low:
        cv.setFillColor(t.c("soft"))
        cv.circle(W * 0.85, H * 0.86, W * 0.32, stroke=0, fill=1)
        cv.circle(W * 0.1, H * 0.12, W * 0.22, stroke=0, fill=1)
        cv.setFillColor(t.c("primary"))
        cv.rect(0, H * 0.43, W * 0.035, H * 0.16, stroke=0, fill=1)
    # frame
    p.rect(p.m, p.m, W - 2 * p.m, H - 2 * p.m, stroke="primary", width=0.8)
    cy = H * 0.55
    if year and str(year) not in title:
        p.text(W / 2, cy + p.u(0.17), str(year), "SansLight", p.u(0.09), "accent", align="center")
    lines_ = wrap(title, t.title_font, p.u(0.085), p.inner_w * 0.82)
    size = p.u(0.085) if len(lines_) <= 2 else p.u(0.068)
    lines_ = wrap(title, t.title_font, size, p.inner_w * 0.82)
    for i, ln in enumerate(lines_):
        p.text(W / 2, cy - i * size * 1.12, ln, t.title_font, size, "primary", align="center")
    y = cy - len(lines_) * size * 1.12 - p.u(0.02)
    if subtitle:
        p.hline(W * 0.4, W * 0.6, y + p.u(0.02), "accent", 1.2)
        p.text(W / 2, y - p.u(0.03), subtitle.upper(), "SansMed", p.u(0.022), "ink", align="center")
    if tagline:
        p.text(W / 2, p.m + p.u(0.07), tagline, "SansLight", p.u(0.018), "ink", align="center")
    # name line
    p.text(W / 2 - p.u(0.2), p.m + p.u(0.16), "THIS PLANNER BELONGS TO", "SansBold", p.u(0.013), "accent")
    p.hline(W / 2 - p.u(0.2), W / 2 + p.u(0.2), p.m + p.u(0.13), "primary", 0.8)


def contents(p: Page, items=(), title="Contents"):
    """Tablet-friendly index: every row links to its section."""
    y = p.header(title, "tap a section to jump there")
    row = p.u(0.058)
    for i, (label, key) in enumerate(items):
        yy = y - (i + 1) * row
        if yy < p.m * 1.5:
            break
        p.text(p.left + p.u(0.01), yy + row * 0.3, f"{i + 1:02d}", "SansBold", p.u(0.02), "accent")
        p.text(p.left + p.u(0.07), yy + row * 0.3, label, "Sans", p.u(0.024), "ink")
        p.hline(p.left, p.right, yy, "line", 0.5, dash=(1, 2))
        p.link_to(key, p.left, yy, p.inner_w, row)
    p.footer()


def how_to_use(p: Page, product="planner"):
    y = p.header("How to use", "print at home or write digitally")
    tips = [
        ("Print at home", "Open the PDF and print at 100% / 'actual size'. A4 and US Letter files are both included."),
        ("Save ink", "Use the low-ink version for everyday printing - same pages, lighter colours."),
        ("Print only what you need", "Choose a page range in your print settings and print extra copies of favourite pages."),
        ("Use it on a tablet", "Import the PDF into GoodNotes, Notability, Xodo or any PDF app. Contents links jump to each section."),
        ("Bind it", "Hole-punch for a binder, use a disc system, or ask a local print shop for spiral binding."),
        ("Personal use", f"This {product} is for your own personal use. Please do not resell or share the files."),
    ]
    for head, body in tips:
        p.label(p.left, y, head, w=p.inner_w * 0.4)
        yy = y - p.u(0.05)
        for ln in wrap(body, "Sans", p.u(0.02), p.inner_w):
            p.text(p.left, yy, ln, "Sans", p.u(0.02))
            yy -= p.u(0.03)
        y = yy - p.u(0.03)
    p.text(p.W / 2, p.m * 1.6, "Thank you for your purchase!", "Script" if not p.low else "Sans",
           p.u(0.05), "primary", align="center")
    p.footer()


# ---------------------------------------------------------------- calendars / planners
def year_at_glance(p: Page, year=2027, start="monday", link_prefix=None):
    y = p.header(f"{year} at a glance", "year overview", right=str(year))
    cols, rows = 3, 4
    gw = p.inner_w / cols
    gh = (y - p.m * 1.2) / rows
    days = _week_days(start)
    fw = 0 if start == "monday" else 6
    cal = calendar.Calendar(firstweekday=fw)
    for mi in range(12):
        cx = p.left + (mi % cols) * gw
        cy = y - (mi // cols) * gh
        p.text(cx + gw / 2, cy - p.u(0.03), MONTHS[mi].upper(), "SansBold", p.u(0.018), "primary", align="center")
        if link_prefix:
            p.link_to(f"{link_prefix}{mi + 1}", cx, cy - gh, gw, gh)
        cw = (gw - p.u(0.02)) / 7
        for di, d in enumerate(days):
            p.text(cx + p.u(0.01) + cw * (di + 0.5), cy - p.u(0.055), d[0], "SansMed", p.u(0.012), "accent", align="center")
        for wi, week in enumerate(cal.monthdayscalendar(year, mi + 1)):
            for di, d in enumerate(week):
                if d:
                    p.text(cx + p.u(0.01) + cw * (di + 0.5), cy - p.u(0.08) - wi * p.u(0.024), str(d),
                           "Sans", p.u(0.0125), "ink", align="center")
    p.footer()


def monthly(p: Page, year=2027, month=1, start="monday", undated=False):
    title = "Month" if undated else MONTHS[month - 1]
    y = p.header(title, "monthly plan", right="" if undated else str(year))
    days = _week_days(start)
    notes_w = p.inner_w * 0.0
    gx, gw = p.left, p.inner_w - notes_w
    hh = p.u(0.03)
    cw = gw / 7
    if not p.low:
        p.rect(gx, y - hh, gw, hh, fill="primary", stroke=None)
    for i, d in enumerate(days):
        p.text(gx + cw * (i + 0.5), y - hh * 0.68, d[:3].upper(), "SansBold", p.u(0.0145),
               "#FFFFFF" if not p.low else "ink", align="center")
    if undated:
        weeks = [[0] * 7 for _ in range(6)]
    else:
        fw = 0 if start == "monday" else 6
        weeks = calendar.Calendar(firstweekday=fw).monthdayscalendar(year, month)
    bottom = p.m + p.u(0.2)
    rh = (y - hh - bottom) / len(weeks)
    for wi, week in enumerate(weeks):
        for di, d in enumerate(week):
            x0 = gx + di * cw
            y0 = y - hh - (wi + 1) * rh
            p.rect(x0, y0, cw, rh, stroke="line", width=0.5)
            if d:
                p.text(x0 + p.u(0.008), y0 + rh - p.u(0.022), str(d), "SansMed", p.u(0.015), "primary")
    # bottom: goals + notes
    bw = (p.inner_w - p.u(0.02)) / 2
    p.box(p.left, bottom - p.u(0.015), bw, p.u(0.17), "Goals this month", lines=4, checks=True)
    p.box(p.left + bw + p.u(0.02), bottom - p.u(0.015), bw, p.u(0.17), "Notes", lines=4)
    p.footer()


def weekly(p: Page, start="monday"):
    y = p.header("Weekly plan", "week of  ______________")
    days = _week_days(start)
    side_w = p.inner_w * 0.3
    main_w = p.inner_w - side_w - p.u(0.02)
    bottom = p.m * 1.1
    bh = (y - bottom) / 7
    for i, d in enumerate(days):
        top = y - i * bh
        p.box(p.left, top - p.u(0.004), main_w, bh - p.u(0.01), d, lines=3)
    sx = p.left + main_w + p.u(0.02)
    tot = y - bottom
    p.box(sx, y - p.u(0.004), side_w, tot * 0.28, "Top priorities", lines=4, checks=True)
    p.box(sx, y - tot * 0.3, side_w, tot * 0.38, "To do", lines=8, checks=True)
    p.box(sx, y - tot * 0.7, side_w, tot * 0.3 - p.u(0.006), "Notes", dots=True)
    p.footer()


def daily(p: Page):
    y = p.header("Daily plan", "date  ____ / ____ / ________")
    lw = p.inner_w * 0.55
    rw = p.inner_w - lw - p.u(0.02)
    bottom = p.m * 1.1
    # schedule
    p.label(p.left, y, "Schedule", w=lw)
    hours = list(range(6, 22))
    top = y - p.u(0.045)
    rh = (top - bottom) / len(hours)
    for i, h in enumerate(hours):
        yy = top - (i + 1) * rh
        p.text(p.left, yy + rh * 0.3, f"{h:02d}:00", "SansMed", p.u(0.0145), "accent")
        p.hline(p.left + p.u(0.07), p.left + lw, yy)
    rx = p.left + lw + p.u(0.02)
    tot = y - bottom
    p.box(rx, y, rw, tot * 0.22, "Top 3 today", lines=3, checks=True)
    p.box(rx, y - tot * 0.24, rw, tot * 0.34, "To do", lines=7, checks=True)
    wy = y - tot * 0.6
    p.box(rx, wy, rw, tot * 0.12, "Water")
    for i in range(8):
        cx = rx + p.u(0.022) + i * (rw - p.u(0.03)) / 8
        p.rect(cx, wy - tot * 0.1, p.u(0.022), p.u(0.032), stroke="primary", r=p.u(0.006))
    p.box(rx, y - tot * 0.74, rw, tot * 0.26, "Notes", dots=True)
    p.footer()


def habit_tracker(p: Page, month_label="Month", habits=12):
    y = p.header("Habit tracker", month_label)
    days = 31
    name_w = p.inner_w * 0.27
    cw = (p.inner_w - name_w) / days
    bottom = p.m * 1.1 + p.u(0.12)
    rh = (y - bottom - p.u(0.03)) / habits
    for d in range(days):
        p.text(p.left + name_w + cw * (d + 0.5), y - p.u(0.02), str(d + 1), "SansMed", p.u(0.0115), "accent", align="center")
    top = y - p.u(0.03)
    for h in range(habits):
        yy = top - (h + 1) * rh
        if h % 2 == 0 and not p.low:
            p.rect(p.left, yy, p.inner_w, rh, fill="soft", stroke=None)
        p.hline(p.left, p.right, yy)
        for d in range(days):
            cx = p.left + name_w + cw * (d + 0.5)
            p.circle(cx, yy + rh / 2, min(cw, rh) * 0.3, stroke="line", width=0.5)
    p.vline(p.left + name_w, bottom + p.u(0.0), top)
    p.text(p.left + p.u(0.005), top + p.u(0.005), "HABIT", "SansBold", p.u(0.013), "primary")
    p.box(p.left, bottom - p.u(0.01), p.inner_w, p.u(0.1), "Reflection", lines=2)
    p.footer()


def goals(p: Page, title="Goals"):
    y = p.header(title, "dream it, plan it, do it")
    bottom = p.m * 1.1
    tot = y - bottom
    hw = (p.inner_w - p.u(0.02)) / 2
    p.box(p.left, y, p.inner_w, tot * 0.16, "My main goal", lines=2)
    p.box(p.left, y - tot * 0.18, hw, tot * 0.3, "Why it matters", lines=5)
    p.box(p.left + hw + p.u(0.02), y - tot * 0.18, hw, tot * 0.3, "Reward", lines=5)
    p.box(p.left, y - tot * 0.5, p.inner_w, tot * 0.32, "Action steps", lines=7, checks=True)
    p.box(p.left, y - tot * 0.84, hw, tot * 0.16, "Deadline", lines=1)
    p.box(p.left + hw + p.u(0.02), y - tot * 0.84, hw, tot * 0.16, "Progress", lines=0)
    # progress bar
    bx, by = p.left + hw + p.u(0.035), y - tot * 0.84 - tot * 0.11
    bw = hw - p.u(0.03)
    for i in range(10):
        p.rect(bx + i * bw / 10, by, bw / 10 - p.u(0.004), p.u(0.03), stroke="primary", r=p.u(0.004))
        p.text(bx + i * bw / 10 + bw / 20, by - p.u(0.02), f"{(i + 1) * 10}%", "Sans", p.u(0.011), "accent", align="center")
    p.footer()


def todo(p: Page):
    y = p.header("To do list", "get it done")
    bottom = p.m * 1.1
    hw = (p.inner_w - p.u(0.02)) / 2
    tot = y - bottom
    p.box(p.left, y, hw, tot * 0.6, "Must do", lines=12, checks=True)
    p.box(p.left + hw + p.u(0.02), y, hw, tot * 0.6, "Should do", lines=12, checks=True)
    p.box(p.left, y - tot * 0.62, hw, tot * 0.38, "Calls & emails", lines=7, checks=True)
    p.box(p.left + hw + p.u(0.02), y - tot * 0.62, hw, tot * 0.38, "Notes", dots=True)
    p.footer()


def notes_lined(p: Page):
    y = p.header("Notes", "")
    p.lines(p.left, y, p.inner_w, y - p.m * 1.1)
    p.footer()


def notes_dotted(p: Page):
    y = p.header("Notes", "dot grid")
    p.dot_grid(p.left, p.m * 1.1, p.inner_w, y - p.m * 1.1)
    p.footer()


# ---------------------------------------------------------------- finance
def budget_monthly(p: Page):
    y = p.header("Monthly budget", "month  ______________")
    bottom = p.m * 1.1
    hw = (p.inner_w - p.u(0.02)) / 2
    tot = y - bottom
    p.table(p.left, y, hw, tot * 0.32, ["Income", "Expected", "Actual"], 7, [2, 1, 1])
    p.table(p.left + hw + p.u(0.02), y, hw, tot * 0.32, ["Savings", "Goal", "Saved"], 7, [2, 1, 1])
    p.table(p.left, y - tot * 0.35, p.inner_w, tot * 0.45, ["Expense", "Category", "Budget", "Actual", "Diff"], 12, [2.4, 1.4, 1, 1, 1])
    sy = y - tot * 0.83
    labels = ["Total income", "Total expenses", "Total saved", "Left over"]
    sw = (p.inner_w - p.u(0.06)) / 4
    for i, lb in enumerate(labels):
        p.box(p.left + i * (sw + p.u(0.02)), sy, sw, tot * 0.17 - p.u(0.006), lb, lines=1)
    p.footer()


def expense_tracker(p: Page):
    y = p.header("Expense tracker", "every penny counts")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1 - p.u(0.08), ["Date", "Description", "Category", "Amount", "Paid"], 24, [1, 3, 1.6, 1.1, 0.7])
    p.text(p.right, p.m * 1.1 + p.u(0.03), "TOTAL  ______________", "SansBold", p.u(0.018), "primary", align="right")
    p.footer()


def bill_tracker(p: Page):
    y = p.header("Bill tracker", "never miss a payment")
    heads = ["Bill", "Due"] + [m[:3] for m in MONTHS]
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, heads, 18, [2.4, 0.9] + [0.6] * 12)
    p.footer()


def savings_tracker(p: Page):
    y = p.header("Savings tracker", "colour a circle for every step")
    p.box(p.left, y, p.inner_w * 0.48, p.u(0.09), "Saving for", lines=1)
    p.box(p.left + p.inner_w * 0.52, y, p.inner_w * 0.48, p.u(0.09), "Goal amount", lines=1)
    top = y - p.u(0.12)
    bottom = p.m * 1.1
    cols, rows = 10, 10
    cw = p.inner_w / cols
    rh = (top - bottom) / rows
    r = min(cw, rh) * 0.38
    for i in range(100):
        cx = p.left + cw * (i % cols + 0.5)
        cy = top - rh * (i // cols + 0.5)
        p.circle(cx, cy, r, stroke="primary", width=0.8)
        p.text(cx, cy - p.u(0.006), str(i + 1), "SansMed", p.u(0.014), "accent", align="center")
    p.footer()


def debt_payoff(p: Page):
    y = p.header("Debt payoff", "one payment at a time")
    p.box(p.left, y, p.inner_w, p.u(0.09), "Debt name / lender", lines=1)
    top = y - p.u(0.11)
    p.table(p.left, top, p.inner_w, top - p.m * 1.1, ["Date", "Payment", "Interest", "Balance", "Note"], 20, [1, 1, 1, 1.2, 2])
    p.footer()


def sinking_funds(p: Page):
    y = p.header("Sinking funds", "save for the expected")
    bottom = p.m * 1.1
    cols, rows = 2, 3
    gw = (p.inner_w - p.u(0.02)) / cols
    gh = (y - bottom) / rows
    for i in range(6):
        x = p.left + (i % cols) * (gw + p.u(0.02))
        top = y - (i // cols) * gh
        p.box(x, top, gw, gh - p.u(0.015), "Fund: __________   goal: _______", lines=0)
        bar_y = top - p.u(0.07)
        for k in range(10):
            p.rect(x + p.u(0.015) + k * (gw - p.u(0.03)) / 10, bar_y - p.u(0.035), (gw - p.u(0.03)) / 10 - p.u(0.004),
                   p.u(0.035), stroke="primary", r=p.u(0.004))
        p.lines(x + p.u(0.015), bar_y - p.u(0.05), gw - p.u(0.03), gh - p.u(0.16), gap=p.u(0.03))
    p.footer()


# ---------------------------------------------------------------- home / food / health
def meal_planner(p: Page, start="monday"):
    y = p.header("Meal planner", "week of  ______________")
    days = _week_days(start)
    bottom = p.m * 1.1
    gw = p.inner_w * 0.72
    p.table(p.left, y, gw, y - bottom, ["Day", "Breakfast", "Lunch", "Dinner", "Snacks"], 7, [0.9, 1.3, 1.3, 1.3, 1])
    rh = (y - bottom - p.u(0.034)) / 7
    for i, d in enumerate(days):
        p.text(p.left + p.u(0.008), y - p.u(0.034) - rh * (i + 0.55), d[:3].upper(), "SansBold", p.u(0.015), "primary")
    sx = p.left + gw + p.u(0.02)
    p.box(sx, y, p.inner_w - gw - p.u(0.02), y - bottom, "Grocery list", lines=24, checks=True)
    p.footer()


def grocery_list(p: Page):
    y = p.header("Grocery list", "shop smarter")
    cats = ["Produce", "Dairy & eggs", "Meat & fish", "Bakery", "Pantry", "Frozen", "Drinks", "Household"]
    bottom = p.m * 1.1
    gw = (p.inner_w - p.u(0.02)) / 2
    gh = (y - bottom) / 4
    for i, c in enumerate(cats):
        x = p.left + (i % 2) * (gw + p.u(0.02))
        top = y - (i // 2) * gh
        p.box(x, top, gw, gh - p.u(0.012), c, lines=5, checks=True)
    p.footer()


def recipe_card(p: Page):
    y = p.header("Recipe", "from my kitchen")
    bottom = p.m * 1.1
    tot = y - bottom
    p.box(p.left, y, p.inner_w, p.u(0.08), "Recipe name", lines=1)
    meta = ["Serves", "Prep time", "Cook time", "Temp"]
    mw = (p.inner_w - p.u(0.06)) / 4
    for i, m in enumerate(meta):
        p.box(p.left + i * (mw + p.u(0.02)), y - p.u(0.1), mw, p.u(0.075), m, lines=1)
    top = y - p.u(0.2)
    lw = p.inner_w * 0.38
    p.box(p.left, top, lw, top - bottom, "Ingredients", lines=16, checks=True)
    p.box(p.left + lw + p.u(0.02), top, p.inner_w - lw - p.u(0.02), top - bottom - tot * 0.2, "Method", lines=13)
    p.box(p.left + lw + p.u(0.02), bottom + tot * 0.18, p.inner_w - lw - p.u(0.02), tot * 0.18, "Notes", lines=2)
    p.footer()


def cleaning_schedule(p: Page):
    y = p.header("Cleaning schedule", "a tidy home, a calm mind")
    bottom = p.m * 1.1
    tot = y - bottom
    days = ["M", "T", "W", "T", "F", "S", "S"]
    tw = p.inner_w
    _, xs, hh, rh = p.table(p.left, y, tw, tot * 0.5, ["Daily task"] + days, 10, [3] + [0.5] * 7)
    for r in range(10):
        for c in range(7):
            cx = (xs[c + 1] + xs[c + 2]) / 2
            p.checkbox(cx - p.u(0.008), y - hh - (r + 1) * rh + rh * 0.3, p.u(0.016))
    hw = (p.inner_w - p.u(0.02)) / 2
    p.box(p.left, y - tot * 0.53, hw, tot * 0.47, "Weekly", lines=9, checks=True)
    p.box(p.left + hw + p.u(0.02), y - tot * 0.53, hw, tot * 0.47, "Monthly", lines=9, checks=True)
    p.footer()


def workout_log(p: Page):
    y = p.header("Workout log", "date  ______________")
    bottom = p.m * 1.1
    tot = y - bottom
    meta = ["Workout", "Duration", "Energy"]
    mw = (p.inner_w - p.u(0.04)) / 3
    for i, m in enumerate(meta):
        p.box(p.left + i * (mw + p.u(0.02)), y, mw, p.u(0.075), m, lines=1)
    top = y - p.u(0.095)
    p.table(p.left, top, p.inner_w, tot * 0.6, ["Exercise", "Set 1", "Set 2", "Set 3", "Set 4", "Notes"], 12, [2.2, 1, 1, 1, 1, 1.6])
    p.box(p.left, top - tot * 0.62, (p.inner_w - p.u(0.02)) / 2, top - tot * 0.62 - bottom, "Cardio", lines=4)
    p.box(p.left + (p.inner_w + p.u(0.02)) / 2, top - tot * 0.62, (p.inner_w - p.u(0.02)) / 2, top - tot * 0.62 - bottom, "How I felt", lines=4)
    p.footer()


def fitness_month(p: Page):
    y = p.header("Fitness tracker", "month  ______________")
    bottom = p.m * 1.1
    p.table(p.left, y, p.inner_w, y - bottom, ["Day", "Workout", "Steps", "Water", "Sleep", "Done"], 31, [0.5, 2.6, 1, 1, 1, 0.6])
    rh = (y - bottom - p.u(0.034)) / 31
    for i in range(31):
        p.text(p.left + p.u(0.012), y - p.u(0.034) - rh * (i + 0.72), str(i + 1), "SansMed", p.u(0.012), "accent")
    p.footer()


def water_sleep(p: Page):
    y = p.header("Water & sleep", "month  ______________")
    bottom = p.m * 1.1
    hw = (p.inner_w - p.u(0.03)) / 2
    for side, (ttl, n) in enumerate([("Glasses of water", 8), ("Hours of sleep", 10)]):
        x = p.left + side * (hw + p.u(0.03))
        p.label(x, y, ttl, w=hw)
        top = y - p.u(0.05)
        rh = (top - bottom) / 31
        cw = (hw - p.u(0.05)) / n
        for d in range(31):
            yy = top - (d + 1) * rh
            p.text(x, yy + rh * 0.3, str(d + 1), "SansMed", p.u(0.011), "accent")
            for k in range(n):
                p.circle(x + p.u(0.05) + cw * (k + 0.5), yy + rh * 0.5, min(cw, rh) * 0.32, stroke="line", width=0.5)
    p.footer()


def mood_tracker(p: Page):
    y = p.header("Mood tracker", "month  ______________")
    moods = ["Great", "Good", "Okay", "Low", "Tired", "Stressed"]
    p.label(p.left, y, "Colour key", w=p.inner_w)
    kw = p.inner_w / len(moods)
    for i, m in enumerate(moods):
        p.rect(p.left + i * kw, y - p.u(0.085), p.u(0.025), p.u(0.025), stroke="primary", r=p.u(0.004))
        p.text(p.left + i * kw + p.u(0.032), y - p.u(0.078), m, "Sans", p.u(0.015))
    top = y - p.u(0.12)
    bottom = p.m * 1.1
    cols = 7
    cw = p.inner_w / cols
    rows = 5
    rh = (top - bottom) / rows
    for i in range(31):
        cx = p.left + cw * (i % cols + 0.5)
        cy = top - rh * (i // cols + 0.5)
        p.circle(cx, cy, min(cw, rh) * 0.38, stroke="primary", width=0.8)
        p.text(cx, cy - p.u(0.007), str(i + 1), "SansMed", p.u(0.016), "accent", align="center")
    p.footer()


def self_care(p: Page):
    y = p.header("Self-care check-in", "date  ______________")
    bottom = p.m * 1.1
    tot = y - bottom
    hw = (p.inner_w - p.u(0.02)) / 2
    p.box(p.left, y, hw, tot * 0.3, "Today I feel", lines=4)
    p.box(p.left + hw + p.u(0.02), y, hw, tot * 0.3, "I need", lines=4)
    items = ["Drink water", "Move my body", "Eat something good", "Get fresh air", "Rest", "Connect with someone", "Do something fun", "Unplug"]
    p.box(p.left, y - tot * 0.32, hw, tot * 0.4, "Self-care list", lines=len(items), checks=True)
    gap = (tot * 0.4 - p.u(0.034)) / (len(items) + 0.4)
    for i, it in enumerate(items):
        p.text(p.left + p.u(0.04), y - tot * 0.32 - p.u(0.034) - gap * (i + 1) + p.u(0.006), it, "Sans", p.u(0.015))
    p.box(p.left + hw + p.u(0.02), y - tot * 0.32, hw, tot * 0.4, "Small wins", lines=7)
    p.box(p.left, y - tot * 0.74, p.inner_w, tot * 0.26, "Notes to self", lines=4)
    p.footer()


def gratitude(p: Page):
    y = p.header("Gratitude", "date  ______________")
    bottom = p.m * 1.1
    tot = y - bottom
    p.box(p.left, y, p.inner_w, tot * 0.28, "Today I am grateful for", lines=3)
    for i in range(3):
        p.text(p.left + p.u(0.015), y - p.u(0.034) - (tot * 0.28 - p.u(0.034)) / 3.4 * (i + 1) + p.u(0.006), f"{i + 1}.",
               "SansBold", p.u(0.016), "accent")
    p.box(p.left, y - tot * 0.3, p.inner_w, tot * 0.14, "Today's affirmation", lines=1)
    hw = (p.inner_w - p.u(0.02)) / 2
    p.box(p.left, y - tot * 0.46, hw, tot * 0.26, "What made today great", lines=4)
    p.box(p.left + hw + p.u(0.02), y - tot * 0.46, hw, tot * 0.26, "Something I learned", lines=4)
    p.box(p.left, y - tot * 0.74, p.inner_w, tot * 0.26, "Reflection", lines=4)
    p.footer()


def journal_prompt(p: Page, prompt="What would make today wonderful?"):
    y = p.header("Journal", "date  ______________")
    p.label(p.left, y, "Prompt", w=p.inner_w)
    yy = y - p.u(0.06)
    for ln in wrap(prompt, p.t.title_font, p.u(0.03), p.inner_w):
        p.text(p.left, yy, ln, p.t.title_font, p.u(0.03), "primary")
        yy -= p.u(0.04)
    p.lines(p.left, yy - p.u(0.01), p.inner_w, yy - p.m * 1.1)
    p.footer()


# ---------------------------------------------------------------- reading / study / teaching
def reading_log(p: Page):
    y = p.header("Reading log", "books I have read")
    bottom = p.m * 1.1
    _, xs, hh, rh = p.table(p.left, y, p.inner_w, y - bottom, ["#", "Title", "Author", "Started", "Finished", "Rating"], 20,
                            [0.4, 2.6, 1.8, 1, 1, 1.3])
    for r in range(20):
        p.text(xs[0] + (xs[1] - xs[0]) / 2, y - hh - rh * (r + 0.7), str(r + 1), "SansMed", p.u(0.012), "accent", align="center")
        p.stars(xs[5] + p.u(0.012), y - hh - rh * (r + 0.5), 5, r=min(rh * 0.25, p.u(0.007)))
    p.footer()


def book_review(p: Page):
    y = p.header("Book review", "")
    bottom = p.m * 1.1
    tot = y - bottom
    hw = (p.inner_w - p.u(0.02)) / 2
    p.box(p.left, y, hw, p.u(0.08), "Title", lines=1)
    p.box(p.left + hw + p.u(0.02), y, hw, p.u(0.08), "Author", lines=1)
    top = y - p.u(0.1)
    meta = ["Genre", "Pages", "Format", "Rating"]
    mw = (p.inner_w - p.u(0.06)) / 4
    for i, m in enumerate(meta):
        p.box(p.left + i * (mw + p.u(0.02)), top, mw, p.u(0.075), m, lines=0 if m == "Rating" else 1)
    p.stars(p.left + 3 * (mw + p.u(0.02)) + p.u(0.02), top - p.u(0.052), 5, r=p.u(0.01))
    top -= p.u(0.095)
    p.box(p.left, top, p.inner_w, tot * 0.3, "Summary", lines=5)
    p.box(p.left, top - tot * 0.32, hw, tot * 0.28, "Favourite quotes", lines=5)
    p.box(p.left + hw + p.u(0.02), top - tot * 0.32, hw, tot * 0.28, "Characters", lines=5)
    p.box(p.left, top - tot * 0.62, p.inner_w, top - tot * 0.62 - bottom, "My thoughts", lines=4)
    p.footer()


def tbr_list(p: Page):
    y = p.header("To be read", "my book wishlist")
    bottom = p.m * 1.1
    cols = 2
    gw = (p.inner_w - p.u(0.02)) / cols
    for c in range(cols):
        p.box(p.left + c * (gw + p.u(0.02)), y, gw, y - bottom, "Title / author", lines=22, checks=True)
    p.footer()


def assignment_tracker(p: Page):
    y = p.header("Assignment tracker", "stay on top of it")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Subject", "Assignment", "Due", "Status", "Grade"], 20, [1.3, 3, 0.9, 1, 0.8])
    p.footer()


def class_schedule(p: Page):
    y = p.header("Class schedule", "timetable")
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    p.table(p.left, y, p.inner_w, (y - p.m * 1.1) * 0.7, ["Time"] + days, 9, [0.9] + [1.2] * 5)
    p.box(p.left, y - (y - p.m * 1.1) * 0.73, p.inner_w, (y - p.m * 1.1) * 0.27, "Teachers & rooms", lines=4)
    p.footer()


def study_planner(p: Page):
    y = p.header("Study planner", "week of  ______________")
    bottom = p.m * 1.1
    tot = y - bottom
    hw = (p.inner_w - p.u(0.02)) / 2
    p.box(p.left, y, hw, tot * 0.3, "This week's goals", lines=5, checks=True)
    p.box(p.left + hw + p.u(0.02), y, hw, tot * 0.3, "Exams & deadlines", lines=5)
    p.table(p.left, y - tot * 0.33, p.inner_w, tot * 0.45, ["Day", "Subject", "Topic", "Time", "Done"], 7, [1, 1.5, 2.4, 0.8, 0.6])
    p.box(p.left, y - tot * 0.8, p.inner_w, tot * 0.2, "Notes", lines=3)
    p.footer()


def lesson_plan_week(p: Page):
    y = p.header("Weekly lesson plan", "week of  ______________")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    bottom = p.m * 1.1
    p.table(p.left, y, p.inner_w, y - bottom, ["Subject"] + days, 7, [1.1] + [1.4] * 5, zebra=True)
    p.footer()


def gradebook(p: Page):
    y = p.header("Grade book", "class  ______________")
    heads = ["Student"] + [""] * 10 + ["Avg"]
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, heads, 25, [3] + [0.7] * 10 + [0.9])
    p.footer()


def attendance(p: Page):
    y = p.header("Attendance", "month  ______________")
    heads = ["Student"] + [str(i) for i in range(1, 24)]
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, heads, 25, [3.2] + [0.5] * 23)
    p.footer()


def parent_contact(p: Page):
    y = p.header("Parent contact log", "")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Date", "Student", "Parent", "Reason", "Outcome"], 18, [0.9, 1.4, 1.4, 2, 2])
    p.footer()


# ---------------------------------------------------------------- business
def sales_tracker(p: Page):
    y = p.header("Sales tracker", "month  ______________")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Date", "Order #", "Customer", "Item", "Qty", "Total", "Paid"], 22,
            [0.9, 1, 1.6, 2, 0.5, 0.9, 0.6])
    p.footer()


def inventory(p: Page):
    y = p.header("Inventory", "stock list")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Item", "SKU", "Cost", "Price", "In stock", "Reorder"], 22, [2.6, 1, 0.9, 0.9, 1, 1])
    p.footer()


def income_expense(p: Page):
    y = p.header("Income & expenses", "month  ______________")
    bottom = p.m * 1.1
    hw = (p.inner_w - p.u(0.02)) / 2
    p.table(p.left, y, hw, y - bottom - p.u(0.1), ["Date", "Income", "Amount"], 18, [0.9, 2, 1])
    p.table(p.left + hw + p.u(0.02), y, hw, y - bottom - p.u(0.1), ["Date", "Expense", "Amount"], 18, [0.9, 2, 1])
    for i, lb in enumerate(["Total income", "Total expenses", "Profit"]):
        sw = (p.inner_w - p.u(0.04)) / 3
        p.box(p.left + i * (sw + p.u(0.02)), bottom + p.u(0.085), sw, p.u(0.08), lb, lines=1)
    p.footer()


def social_planner(p: Page):
    y = p.header("Social media planner", "week of  ______________")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Day", "Platform", "Content idea", "Caption / hook", "Posted"], 14,
            [0.8, 1.1, 2.2, 2.4, 0.7])
    p.footer()


def order_tracker(p: Page):
    y = p.header("Order tracker", "")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Date", "Customer", "Order details", "Due", "Shipped", "Paid"], 20,
            [0.9, 1.5, 2.8, 0.9, 0.8, 0.6])
    p.footer()


def client_info(p: Page):
    y = p.header("Client information", "")
    bottom = p.m * 1.1
    tot = y - bottom
    fields = ["Name", "Business", "Email", "Phone", "Address", "Website / social"]
    hw = (p.inner_w - p.u(0.02)) / 2
    for i, f in enumerate(fields):
        p.box(p.left + (i % 2) * (hw + p.u(0.02)), y - (i // 2) * p.u(0.095), hw, p.u(0.08), f, lines=1)
    top = y - 3 * p.u(0.095)
    p.box(p.left, top, p.inner_w, tot * 0.28, "Project details", lines=5)
    p.table(p.left, top - tot * 0.3, p.inner_w, top - tot * 0.3 - bottom, ["Date", "Notes", "Follow up"], 8, [1, 4, 1.2])
    p.footer()


# ---------------------------------------------------------------- life events
def wedding_checklist(p: Page):
    y = p.header("Wedding checklist", "countdown to the big day")
    bottom = p.m * 1.1
    groups = [
        ("12 months before", ["Set the budget", "Draft guest list", "Book venue", "Choose wedding party"]),
        ("9 months before", ["Book photographer", "Book caterer", "Shop for dress / suit", "Book music"]),
        ("6 months before", ["Send save the dates", "Order cake", "Book florist", "Plan honeymoon"]),
        ("3 months before", ["Send invitations", "Buy rings", "Final dress fitting", "Plan seating"]),
        ("1 month before", ["Confirm vendors", "Marriage licence", "Final headcount", "Write vows"]),
        ("1 week before", ["Pack for honeymoon", "Pay final balances", "Rehearsal", "Relax!"]),
    ]
    gw = (p.inner_w - p.u(0.02)) / 2
    gh = (y - bottom) / 3
    for i, (head, items) in enumerate(groups):
        x = p.left + (i % 2) * (gw + p.u(0.02))
        top = y - (i // 2) * gh
        p.box(x, top, gw, gh - p.u(0.012), head, lines=6, checks=True)
        gap = (gh - p.u(0.012) - p.u(0.034)) / 6.4
        for k, it in enumerate(items):
            p.text(x + p.u(0.04), top - p.u(0.034) - gap * (k + 1) + p.u(0.006), it, "Sans", p.u(0.015))
    p.footer()


def wedding_budget(p: Page):
    y = p.header("Wedding budget", "")
    items = ["Venue", "Catering", "Photography", "Video", "Attire", "Rings", "Flowers", "Music", "Cake", "Stationery",
             "Decor", "Hair & makeup", "Transport", "Favours", "Honeymoon", "Other"]
    _, xs, hh, rh = p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Item", "Budget", "Actual", "Deposit", "Balance", "Paid"],
                            len(items), [2, 1, 1, 1, 1, 0.6])
    for i, it in enumerate(items):
        p.text(xs[0] + p.u(0.01), y - hh - rh * (i + 0.65), it, "Sans", p.u(0.0145))
    p.footer()


def guest_list(p: Page):
    y = p.header("Guest list", "")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Name", "Address", "Party of", "RSVP", "Meal", "Gift"], 22,
            [2, 2.6, 0.8, 0.7, 0.9, 1])
    p.footer()


def vendor_contacts(p: Page):
    y = p.header("Vendor contacts", "")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Vendor", "Contact", "Phone", "Email", "Deposit", "Notes"], 16,
            [1.4, 1.4, 1.2, 1.8, 0.8, 1.4])
    p.footer()


def baby_feeding(p: Page):
    y = p.header("Feeding log", "date  ______________")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Time", "Left", "Right", "Bottle (ml/oz)", "Diaper", "Notes"], 22,
            [0.9, 0.8, 0.8, 1.2, 0.9, 2])
    p.footer()


def baby_sleep(p: Page):
    y = p.header("Sleep log", "week of  ______________")
    hours = [f"{h}" for h in range(24)]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    bottom = p.m * 1.1 + p.u(0.2)
    name_w = p.inner_w * 0.1
    cw = (p.inner_w - name_w) / 24
    for i, h in enumerate(hours):
        p.text(p.left + name_w + cw * (i + 0.5), y - p.u(0.02), h, "SansMed", p.u(0.011), "accent", align="center")
    top = y - p.u(0.03)
    rh = (top - bottom) / 7
    for d, dn in enumerate(days):
        yy = top - (d + 1) * rh
        p.text(p.left, yy + rh * 0.4, dn.upper(), "SansBold", p.u(0.014), "primary")
        for i in range(24):
            p.rect(p.left + name_w + i * cw, yy, cw, rh, stroke="line", width=0.4)
    p.box(p.left, bottom - p.u(0.015), p.inner_w, p.u(0.18), "Notes", lines=3)
    p.footer()


def baby_milestones(p: Page):
    y = p.header("Milestones", "precious firsts")
    items = ["First smile", "First laugh", "Rolled over", "Sat up", "First tooth", "First food", "Crawled", "First word",
             "Stood up", "First steps", "First haircut", "First birthday"]
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Milestone", "Date", "Memory"], len(items), [1.6, 1, 3])
    rh = (y - p.m * 1.1 - p.u(0.034)) / len(items)
    for i, it in enumerate(items):
        p.text(p.left + p.u(0.01), y - p.u(0.034) - rh * (i + 0.6), it, "Sans", p.u(0.015))
    p.footer()


def pet_profile(p: Page):
    y = p.header("Pet profile", "")
    bottom = p.m * 1.1
    tot = y - bottom
    p.rect(p.left, y - tot * 0.32, p.inner_w * 0.36, tot * 0.32, stroke="primary", r=p.u(0.01))
    p.text(p.left + p.inner_w * 0.18, y - tot * 0.17, "photo", "SansLight", p.u(0.02), "line", align="center")
    fields = ["Name", "Breed", "Birthday", "Microchip #", "Vet", "Insurance"]
    fx = p.left + p.inner_w * 0.39
    fw = p.inner_w * 0.61
    fh = tot * 0.32 / len(fields)
    for i, f in enumerate(fields):
        yy = y - (i + 1) * fh
        p.text(fx, yy + fh * 0.3, f.upper(), "SansBold", p.u(0.013), "primary")
        p.hline(fx + fw * 0.32, fx + fw, yy + fh * 0.25)
    p.table(p.left, y - tot * 0.36, p.inner_w, tot * 0.36, ["Vaccine", "Date", "Next due", "Vet"], 8, [1.6, 1, 1, 1.4])
    p.box(p.left, y - tot * 0.75, p.inner_w, tot * 0.25, "Food, allergies & notes", lines=4)
    p.footer()


def pet_care(p: Page):
    y = p.header("Pet care log", "week of  ______________")
    days = ["M", "T", "W", "T", "F", "S", "S"]
    bottom = p.m * 1.1
    tot = y - bottom
    rows = ["Morning food", "Evening food", "Fresh water", "Walk / play", "Medication", "Grooming", "Litter / clean up"]
    _, xs, hh, rh = p.table(p.left, y, p.inner_w, tot * 0.55, ["Task"] + days, len(rows), [2.4] + [0.6] * 7)
    for r, it in enumerate(rows):
        p.text(xs[0] + p.u(0.01), y - hh - rh * (r + 0.62), it, "Sans", p.u(0.015))
        for c in range(7):
            cx = (xs[c + 1] + xs[c + 2]) / 2
            p.checkbox(cx - p.u(0.008), y - hh - (r + 1) * rh + rh * 0.3, p.u(0.016))
    p.box(p.left, y - tot * 0.58, p.inner_w, tot * 0.42, "Notes", lines=7)
    p.footer()


def packing_list(p: Page):
    y = p.header("Packing list", "trip to  ______________")
    cats = ["Clothes", "Toiletries", "Documents", "Electronics", "Health", "Extras"]
    bottom = p.m * 1.1
    gw = (p.inner_w - p.u(0.02)) / 2
    gh = (y - bottom) / 3
    for i, c in enumerate(cats):
        x = p.left + (i % 2) * (gw + p.u(0.02))
        top = y - (i // 2) * gh
        p.box(x, top, gw, gh - p.u(0.012), c, lines=8, checks=True)
    p.footer()


def itinerary(p: Page):
    y = p.header("Travel itinerary", "")
    bottom = p.m * 1.1
    tot = y - bottom
    meta = ["Destination", "Dates", "Flight / train"]
    mw = (p.inner_w - p.u(0.04)) / 3
    for i, m in enumerate(meta):
        p.box(p.left + i * (mw + p.u(0.02)), y, mw, p.u(0.08), m, lines=1)
    top = y - p.u(0.1)
    p.table(p.left, top, p.inner_w, tot * 0.62, ["Day", "Morning", "Afternoon", "Evening"], 7, [0.6, 2, 2, 2])
    hw = (p.inner_w - p.u(0.02)) / 2
    p.box(p.left, top - tot * 0.64, hw, top - tot * 0.64 - bottom, "Stay", lines=3)
    p.box(p.left + hw + p.u(0.02), top - tot * 0.64, hw, top - tot * 0.64 - bottom, "Must see / eat", lines=3, checks=True)
    p.footer()


def travel_budget(p: Page):
    y = p.header("Travel budget", "")
    items = ["Flights", "Accommodation", "Transport", "Food", "Activities", "Shopping", "Insurance", "Other"]
    bottom = p.m * 1.1
    tot = y - bottom
    _, xs, hh, rh = p.table(p.left, y, p.inner_w, tot * 0.45, ["Category", "Budget", "Actual", "Difference"], len(items), [2, 1, 1, 1])
    for i, it in enumerate(items):
        p.text(xs[0] + p.u(0.01), y - hh - rh * (i + 0.62), it, "Sans", p.u(0.015))
    p.table(p.left, y - tot * 0.48, p.inner_w, tot * 0.52, ["Date", "Spent on", "Amount"], 12, [1, 3, 1])
    p.footer()


# ---------------------------------------------------------------- seasonal
def christmas_gifts(p: Page):
    y = p.header("Gift list", "christmas")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["For", "Gift idea", "Budget", "Bought", "Wrapped"], 22, [1.6, 2.8, 0.9, 0.8, 0.8])
    p.footer()


def christmas_cards(p: Page):
    y = p.header("Card list", "christmas")
    p.table(p.left, y, p.inner_w, y - p.m * 1.1, ["Name", "Address", "Sent", "Received"], 22, [1.8, 3.6, 0.7, 0.9])
    p.footer()


def christmas_menu(p: Page):
    y = p.header("Holiday menu", "christmas dinner")
    bottom = p.m * 1.1
    tot = y - bottom
    hw = (p.inner_w - p.u(0.02)) / 2
    for i, c in enumerate(["Starters", "Main", "Sides", "Desserts"]):
        p.box(p.left + (i % 2) * (hw + p.u(0.02)), y - (i // 2) * tot * 0.26, hw, tot * 0.24, c, lines=4)
    p.box(p.left, y - tot * 0.53, hw, tot * 0.47, "Shopping list", lines=10, checks=True)
    p.box(p.left + hw + p.u(0.02), y - tot * 0.53, hw, tot * 0.47, "Cooking timeline", lines=10)
    p.footer()


def advent_countdown(p: Page, year=2026):
    y = p.header("Countdown", f"december {year}")
    bottom = p.m * 1.1
    cols, rows = 5, 5
    cw = p.inner_w / cols
    rh = (y - bottom) / rows
    for i in range(25):
        x = p.left + (i % cols) * cw
        top = y - (i // cols) * rh
        p.rect(x + p.u(0.006), top - rh + p.u(0.006), cw - p.u(0.012), rh - p.u(0.012), stroke="primary", r=p.u(0.01))
        p.text(x + cw / 2, top - rh * 0.42, str(i + 1), p.t.title_font, p.u(0.05), "accent", align="center")
        p.hline(x + p.u(0.02), x + cw - p.u(0.02), top - rh * 0.75)
    p.footer()


def new_year_review(p: Page, year=2026):
    y = p.header("Year in review", str(year))
    bottom = p.m * 1.1
    tot = y - bottom
    hw = (p.inner_w - p.u(0.02)) / 2
    boxes = ["Best moments", "Biggest lessons", "Proud of", "Let go of", "Books & films", "People to thank"]
    for i, b in enumerate(boxes):
        p.box(p.left + (i % 2) * (hw + p.u(0.02)), y - (i // 2) * tot / 3, hw, tot / 3 - p.u(0.012), b, lines=5)
    p.footer()


def vision_board(p: Page, year=2027):
    y = p.header("Vision board", str(year))
    bottom = p.m * 1.1
    tot = y - bottom
    areas = ["Health", "Career", "Money", "Relationships", "Home", "Fun & travel", "Growth", "Giving back"]
    hw = (p.inner_w - p.u(0.02)) / 2
    gh = tot / 4
    for i, a in enumerate(areas):
        p.box(p.left + (i % 2) * (hw + p.u(0.02)), y - (i // 2) * gh, hw, gh - p.u(0.012), a, lines=3)
    p.footer()


PAGES = {
    "cover": (cover, "Cover"),
    "contents": (contents, "Clickable contents"),
    "how_to_use": (how_to_use, "How to use"),
    "year_at_glance": (year_at_glance, "Year at a glance"),
    "monthly": (monthly, "Monthly calendar"),
    "weekly": (weekly, "Weekly planner"),
    "daily": (daily, "Daily planner"),
    "habit_tracker": (habit_tracker, "Habit tracker"),
    "goals": (goals, "Goal planner"),
    "todo": (todo, "To-do list"),
    "notes_lined": (notes_lined, "Lined notes"),
    "notes_dotted": (notes_dotted, "Dot grid notes"),
    "budget_monthly": (budget_monthly, "Monthly budget"),
    "expense_tracker": (expense_tracker, "Expense tracker"),
    "bill_tracker": (bill_tracker, "Bill tracker"),
    "savings_tracker": (savings_tracker, "Savings tracker"),
    "debt_payoff": (debt_payoff, "Debt payoff tracker"),
    "sinking_funds": (sinking_funds, "Sinking funds"),
    "meal_planner": (meal_planner, "Weekly meal planner"),
    "grocery_list": (grocery_list, "Grocery list"),
    "recipe_card": (recipe_card, "Recipe page"),
    "cleaning_schedule": (cleaning_schedule, "Cleaning schedule"),
    "workout_log": (workout_log, "Workout log"),
    "fitness_month": (fitness_month, "Monthly fitness tracker"),
    "water_sleep": (water_sleep, "Water & sleep tracker"),
    "mood_tracker": (mood_tracker, "Mood tracker"),
    "self_care": (self_care, "Self-care check-in"),
    "gratitude": (gratitude, "Gratitude page"),
    "journal_prompt": (journal_prompt, "Journal prompts"),
    "reading_log": (reading_log, "Reading log"),
    "book_review": (book_review, "Book review"),
    "tbr_list": (tbr_list, "To-be-read list"),
    "assignment_tracker": (assignment_tracker, "Assignment tracker"),
    "class_schedule": (class_schedule, "Class schedule"),
    "study_planner": (study_planner, "Study planner"),
    "lesson_plan_week": (lesson_plan_week, "Weekly lesson plan"),
    "gradebook": (gradebook, "Grade book"),
    "attendance": (attendance, "Attendance sheet"),
    "parent_contact": (parent_contact, "Parent contact log"),
    "sales_tracker": (sales_tracker, "Sales tracker"),
    "inventory": (inventory, "Inventory sheet"),
    "income_expense": (income_expense, "Income & expenses"),
    "social_planner": (social_planner, "Social media planner"),
    "order_tracker": (order_tracker, "Order tracker"),
    "client_info": (client_info, "Client information"),
    "wedding_checklist": (wedding_checklist, "Wedding checklist"),
    "wedding_budget": (wedding_budget, "Wedding budget"),
    "guest_list": (guest_list, "Guest list"),
    "vendor_contacts": (vendor_contacts, "Vendor contacts"),
    "baby_feeding": (baby_feeding, "Feeding log"),
    "baby_sleep": (baby_sleep, "Sleep log"),
    "baby_milestones": (baby_milestones, "Milestones"),
    "pet_profile": (pet_profile, "Pet profile"),
    "pet_care": (pet_care, "Pet care log"),
    "packing_list": (packing_list, "Packing list"),
    "itinerary": (itinerary, "Travel itinerary"),
    "travel_budget": (travel_budget, "Travel budget"),
    "christmas_gifts": (christmas_gifts, "Gift list"),
    "christmas_cards": (christmas_cards, "Card list"),
    "christmas_menu": (christmas_menu, "Holiday menu"),
    "advent_countdown": (advent_countdown, "Christmas countdown"),
    "new_year_review": (new_year_review, "Year in review"),
    "vision_board": (vision_board, "Vision board"),
}
