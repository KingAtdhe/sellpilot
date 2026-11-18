"""What the bot can make.

Each product kind lists its pages, its search keywords, when it sells best and
its base price. Seasonal multipliers are keyed by the month the product is
*listed*: seasonal printables sell best when listed 6-12 weeks before the
season, so e.g. Christmas planners peak when listed Sep-Nov.
"""
from __future__ import annotations

import datetime as dt

MONTHS = range(1, 13)


def selling_year(today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    return today.year + 1 if today.month >= 9 else today.year


def _rep(key, n, **params):
    return [(key, dict(params))] * n


def _months(year, start="monday"):
    return [("monthly", {"year": year, "month": m, "start": start}) for m in MONTHS]


# Each pages() returns a list of (page_key, params). Sections are grouped by page key.
KINDS: list[dict] = [
    {
        "key": "annual-planner", "name": "{year} Planner", "category": "Planners", "dated": True,
        "subtitle": "monthly, weekly & daily", "base_price": 9.99, "demand": 1.0,
        "keywords": ["{year} planner", "printable planner {year}", "planner printable", "daily planner", "weekly planner",
                     "monthly planner", "goodnotes planner", "digital planner", "planner bundle", "a4 planner",
                     "letter planner", "undated planner", "life planner"],
        "season": {9: 1.4, 10: 1.7, 11: 1.9, 12: 2.0, 1: 1.6, 2: 0.9},
        "audience": "anyone who wants a calm, organised year",
        "pages": lambda y: [("contents", {}), ("year_at_glance", {"year": y, "link_prefix": "m"})] + _months(y)
        + _rep("weekly", 4) + _rep("daily", 3) + [("goals", {}), ("habit_tracker", {}), ("todo", {}),
                                                  ("notes_lined", {}), ("notes_dotted", {}), ("how_to_use", {"product": "planner"})],
    },
    {
        "key": "wall-calendar", "name": "{year} Printable Calendar", "category": "Calendars", "dated": True,
        "subtitle": "12 months + year at a glance", "base_price": 4.99, "demand": 0.9,
        "keywords": ["{year} calendar", "printable calendar", "{year} printable calendar", "monthly calendar",
                     "wall calendar", "desk calendar", "minimalist calendar", "calendar template", "family calendar",
                     "monday start calendar", "a4 calendar", "letter calendar", "year calendar"],
        "season": {9: 1.3, 10: 1.6, 11: 2.0, 12: 2.2, 1: 1.5},
        "audience": "families, home offices and classrooms",
        "pages": lambda y: [("year_at_glance", {"year": y, "link_prefix": "m"})] + _months(y) + [("how_to_use", {"product": "calendar"})],
    },
    {
        "key": "budget-planner", "name": "Budget Planner", "category": "Finance", "dated": False,
        "subtitle": "budget, bills, savings & debt", "base_price": 7.99, "demand": 1.0,
        "keywords": ["budget planner", "budget planner printable", "finance planner", "monthly budget",
                     "expense tracker", "bill tracker", "savings tracker", "debt payoff tracker", "budget template",
                     "money planner", "financial planner", "budget binder", "sinking funds"],
        "season": {12: 1.4, 1: 1.8, 2: 1.3, 3: 1.1, 8: 1.1},
        "audience": "anyone who wants to take control of their money",
        "pages": lambda y: [("contents", {}), ("budget_monthly", {}), ("expense_tracker", {}), ("bill_tracker", {}),
                            ("savings_tracker", {}), ("sinking_funds", {}), ("debt_payoff", {}), ("goals", {"title": "Money goals"}),
                            ("notes_lined", {}), ("how_to_use", {"product": "budget planner"})],
    },
    {
        "key": "meal-planner", "name": "Meal Planner & Grocery List", "category": "Home", "dated": False,
        "subtitle": "plan meals, shop smarter", "base_price": 4.99, "demand": 0.9,
        "keywords": ["meal planner", "meal planner printable", "grocery list", "weekly meal plan", "meal prep planner",
                     "recipe template", "food planner", "shopping list printable", "menu planner", "kitchen printable",
                     "family meal planner", "meal planning", "recipe card"],
        "season": {12: 1.2, 1: 1.6, 2: 1.2, 8: 1.1, 9: 1.2},
        "audience": "busy families and meal-preppers",
        "pages": lambda y: [("meal_planner", {}), ("grocery_list", {}), ("recipe_card", {}), ("recipe_card", {}),
                            ("budget_monthly", {}), ("how_to_use", {"product": "meal planner"})],
    },
    {
        "key": "fitness-planner", "name": "Fitness & Workout Planner", "category": "Health & fitness", "dated": False,
        "subtitle": "workouts, habits, water & sleep", "base_price": 5.99, "demand": 0.85,
        "keywords": ["fitness planner", "workout planner", "workout log", "fitness tracker printable", "gym planner",
                     "exercise log", "health planner", "habit tracker", "water tracker", "sleep tracker",
                     "fitness journal", "weight loss planner", "wellness planner"],
        "season": {12: 1.4, 1: 2.0, 2: 1.4, 3: 1.1, 4: 1.1, 5: 1.1},
        "audience": "anyone building a healthy routine",
        "pages": lambda y: [("goals", {"title": "Fitness goals"}), ("workout_log", {}), ("workout_log", {}), ("fitness_month", {}),
                            ("water_sleep", {}), ("habit_tracker", {}), ("meal_planner", {}), ("how_to_use", {"product": "planner"})],
    },
    {
        "key": "self-care-journal", "name": "Self-Care & Gratitude Journal", "category": "Wellbeing", "dated": False,
        "subtitle": "gratitude, mood & reflection", "base_price": 5.99, "demand": 0.85,
        "keywords": ["self care planner", "gratitude journal", "mood tracker", "self care journal", "wellness journal",
                     "mindfulness journal", "journal prompts", "daily journal", "reflection journal",
                     "positive journal", "gratitude printable", "self love journal", "mental wellness planner"],
        "season": {12: 1.3, 1: 1.7, 2: 1.2, 5: 1.1, 9: 1.1},
        "audience": "anyone making time for themselves",
        "pages": lambda y: [("self_care", {}), ("gratitude", {}), ("mood_tracker", {}), ("habit_tracker", {}),
                            ("journal_prompt", {"prompt": "What would make today wonderful?"}),
                            ("journal_prompt", {"prompt": "What am I proud of this week, however small?"}),
                            ("journal_prompt", {"prompt": "What do I want more of in my life - and less of?"}),
                            ("journal_prompt", {"prompt": "Describe a perfect, ordinary day."}),
                            ("how_to_use", {"product": "journal"})],
    },
    {
        "key": "reading-journal", "name": "Reading Journal", "category": "Hobbies", "dated": False,
        "subtitle": "log, review & track your books", "base_price": 4.99, "demand": 0.8,
        "keywords": ["reading journal", "reading log", "book journal", "reading tracker", "book review template",
                     "tbr list", "book lover gift", "reading planner", "bookish printable", "book tracker",
                     "reading challenge", "library log", "book club"],
        "season": {12: 1.3, 1: 1.5, 6: 1.2, 7: 1.2},
        "audience": "book lovers and book clubs",
        "pages": lambda y: [("reading_log", {}), ("book_review", {}), ("book_review", {}), ("tbr_list", {}),
                            ("goals", {"title": "Reading goals"}), ("how_to_use", {"product": "reading journal"})],
    },
    {
        "key": "cleaning-planner", "name": "Cleaning Schedule & Home Planner", "category": "Home", "dated": False,
        "subtitle": "daily, weekly & monthly chores", "base_price": 3.99, "demand": 0.75,
        "keywords": ["cleaning schedule", "cleaning checklist", "cleaning planner", "chore chart", "home planner",
                     "housekeeping planner", "household binder", "home management", "cleaning printable",
                     "weekly cleaning", "spring cleaning", "home organization", "family chores"],
        "season": {1: 1.4, 2: 1.2, 3: 1.6, 4: 1.5, 9: 1.1},
        "audience": "anyone who wants a calm, tidy home",
        "pages": lambda y: [("cleaning_schedule", {}), ("todo", {}), ("grocery_list", {}), ("meal_planner", {}),
                            ("bill_tracker", {}), ("how_to_use", {"product": "home planner"})],
    },
    {
        "key": "student-planner", "name": "Student Planner", "category": "School", "dated": False,
        "subtitle": "classes, assignments & study", "base_price": 5.99, "demand": 0.8,
        "keywords": ["student planner", "academic planner", "study planner", "homework planner", "assignment tracker",
                     "college planner", "school planner", "class schedule", "study schedule", "exam planner",
                     "university planner", "high school planner", "back to school"],
        "season": {6: 1.3, 7: 1.8, 8: 2.0, 9: 1.3, 1: 1.3},
        "audience": "students who want to stay on top of school",
        "pages": lambda y: [("class_schedule", {}), ("assignment_tracker", {}), ("study_planner", {}), ("weekly", {}),
                            ("goals", {"title": "Semester goals"}), ("todo", {}), ("notes_dotted", {}),
                            ("how_to_use", {"product": "planner"})],
    },
    {
        "key": "teacher-planner", "name": "Teacher Planner", "category": "School", "dated": False,
        "subtitle": "lesson plans, grades & attendance", "base_price": 7.99, "demand": 0.8,
        "keywords": ["teacher planner", "lesson planner", "teacher printable", "gradebook", "attendance sheet",
                     "lesson plan template", "classroom planner", "teacher binder", "teacher gift", "homeschool planner",
                     "parent contact log", "teacher organizer", "school year planner"],
        "season": {6: 1.4, 7: 1.9, 8: 2.0, 9: 1.2, 12: 1.1, 1: 1.2},
        "audience": "teachers and homeschool parents",
        "pages": lambda y: [("contents", {}), ("lesson_plan_week", {}), ("gradebook", {}), ("attendance", {}),
                            ("parent_contact", {}), ("class_schedule", {}), ("todo", {}), ("notes_lined", {}),
                            ("how_to_use", {"product": "planner"})],
    },
    {
        "key": "small-business-planner", "name": "Small Business Planner", "category": "Business", "dated": False,
        "subtitle": "sales, orders, inventory & social", "base_price": 8.99, "demand": 0.9,
        "keywords": ["small business planner", "business planner", "sales tracker", "inventory tracker",
                     "order tracker", "income expense tracker", "social media planner", "etsy shop planner",
                     "side hustle planner", "entrepreneur planner", "bookkeeping printable", "client tracker",
                     "business binder"],
        "season": {12: 1.3, 1: 1.7, 2: 1.2, 9: 1.1},
        "audience": "makers, shop owners and side hustlers",
        "pages": lambda y: [("contents", {}), ("goals", {"title": "Business goals"}), ("sales_tracker", {}), ("order_tracker", {}),
                            ("inventory", {}), ("income_expense", {}), ("social_planner", {}), ("client_info", {}),
                            ("todo", {}), ("how_to_use", {"product": "business planner"})],
    },
    {
        "key": "wedding-planner", "name": "Wedding Planner", "category": "Life events", "dated": False,
        "subtitle": "checklist, budget, guests & vendors", "base_price": 8.99, "demand": 0.8,
        "keywords": ["wedding planner", "wedding planner printable", "wedding checklist", "wedding budget",
                     "guest list template", "wedding organizer", "bride to be gift", "engagement gift",
                     "wedding binder", "wedding planning", "vendor list", "wedding timeline", "seating chart"],
        "season": {12: 1.7, 1: 1.8, 2: 1.5, 3: 1.2},
        "audience": "couples planning their big day",
        "pages": lambda y: [("contents", {}), ("wedding_checklist", {}), ("wedding_budget", {}), ("guest_list", {}),
                            ("guest_list", {}), ("vendor_contacts", {}), ("todo", {}), ("notes_lined", {}),
                            ("how_to_use", {"product": "wedding planner"})],
    },
    {
        "key": "baby-log", "name": "Baby Log Book", "category": "Life events", "dated": False,
        "subtitle": "feeding, sleep & milestones", "base_price": 4.99, "demand": 0.7,
        "keywords": ["baby log", "newborn log", "baby tracker", "feeding log", "baby sleep log", "breastfeeding log",
                     "new mom gift", "baby milestones", "nursing log", "newborn printable", "baby schedule",
                     "baby shower gift", "diaper log"],
        "season": {},
        "audience": "new parents",
        "pages": lambda y: [("baby_feeding", {}), ("baby_sleep", {}), ("baby_milestones", {}), ("todo", {}),
                            ("notes_lined", {}), ("how_to_use", {"product": "log book"})],
    },
    {
        "key": "pet-planner", "name": "Pet Care Planner", "category": "Pets", "dated": False,
        "subtitle": "profile, vaccines & daily care", "base_price": 4.99, "demand": 0.65,
        "keywords": ["pet planner", "dog planner", "cat planner", "pet care log", "pet health record",
                     "vaccine record", "puppy planner", "pet printable", "dog mom gift", "pet journal",
                     "pet sitter", "pet binder", "vet record"],
        "season": {12: 1.2, 1: 1.1},
        "audience": "dog and cat parents",
        "pages": lambda y: [("pet_profile", {}), ("pet_care", {}), ("todo", {}), ("expense_tracker", {}), ("notes_lined", {}),
                            ("how_to_use", {"product": "pet planner"})],
    },
    {
        "key": "travel-planner", "name": "Travel Planner", "category": "Travel", "dated": False,
        "subtitle": "itinerary, packing & budget", "base_price": 4.99, "demand": 0.75,
        "keywords": ["travel planner", "travel planner printable", "packing list", "itinerary template",
                     "vacation planner", "trip planner", "travel budget", "holiday planner", "travel checklist",
                     "road trip planner", "travel journal", "honeymoon planner", "packing checklist"],
        "season": {1: 1.3, 2: 1.3, 3: 1.4, 4: 1.5, 5: 1.6, 6: 1.4},
        "audience": "travellers and holiday planners",
        "pages": lambda y: [("itinerary", {}), ("packing_list", {}), ("travel_budget", {}), ("todo", {}),
                            ("notes_dotted", {}), ("how_to_use", {"product": "travel planner"})],
    },
    {
        "key": "christmas-planner", "name": "Christmas Planner", "category": "Seasonal", "dated": True, "dated_this_year": True,
        "subtitle": "gifts, cards, menu & countdown", "base_price": 5.99, "demand": 1.0,
        "keywords": ["christmas planner", "holiday planner", "christmas printable", "gift list", "christmas gift tracker",
                     "christmas card list", "holiday menu planner", "advent calendar printable", "christmas countdown",
                     "holiday budget", "christmas checklist", "festive planner", "holiday organizer"],
        "season": {9: 1.3, 10: 2.2, 11: 2.6, 12: 1.6},
        "off_season": [1, 2, 3, 4, 5, 6, 7],
        "audience": "anyone who wants a stress-free holiday season",
        "pages": lambda y: [("christmas_gifts", {}), ("christmas_cards", {}), ("christmas_menu", {}),
                            ("advent_countdown", {"year": y}), ("budget_monthly", {}), ("todo", {}),
                            ("how_to_use", {"product": "christmas planner"})],
    },
    {
        "key": "new-year-planner", "name": "New Year Reset Planner", "category": "Seasonal", "dated": True,
        "subtitle": "review, vision & goals", "base_price": 5.99, "demand": 0.9,
        "keywords": ["new year planner", "goal planner", "vision board printable", "year review", "{year} goals",
                     "new year resolutions", "goal setting", "intention planner", "reflection worksheet",
                     "new year reset", "goal tracker", "manifestation planner", "annual review"],
        "season": {11: 1.4, 12: 2.4, 1: 2.0},
        "off_season": [3, 4, 5, 6, 7, 8, 9],
        "audience": "anyone ready for a fresh start",
        "pages": lambda y: [("new_year_review", {"year": y - 1}), ("vision_board", {"year": y}), ("goals", {}), ("goals", {}),
                            ("habit_tracker", {}), ("year_at_glance", {"year": y}), ("how_to_use", {"product": "planner"})],
    },
]
KIND_BY_KEY = {k["key"]: k for k in KINDS}


def kind_year(kind: dict, today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    if kind.get("dated_this_year"):
        return today.year  # e.g. a Christmas planner made in November is for this December
    return selling_year(today)


def season_boost(kind: dict, month: int) -> float:
    if month in kind.get("off_season", []):
        return 0.0
    return kind.get("season", {}).get(month, 1.0)


def fmt(s: str, year: int) -> str:
    return s.replace("{year}", str(year))
