"""
Supplementary collection from the university's public events page (P1).

Ethical limits (proposal Sections 3.2 and 3.4): only the public events page
and the pages it links to are requested, with a descriptive User-Agent and a
delay between requests; social media, notices and news pages are never
scraped; every result enters the moderation queue as 'pending' (P3).

What the live page looks like (verified against inspector markup and a
screenshot of kabarak.ac.ke/events, October 2026):

    <article class="raxo-item-nor ...">
      <div class="raxo-image"><a href="..."><img src="..."></a></div>
      <div class="raxo-content">
        <h4 class="raxo-title"><a href="...">Title</a></h4>
        <div class="raxo-info"><span class="raxo-date">Jul 26, 2023</span></div>
        <div class="raxo-text">Short description...</div>
      </div>
    </article>

IMPORTANT: the date on each card is the date the item was POSTED, not the
date of the event (e.g. "Central Rift Innovation Week, 2023" is dated
Jul 26, 2023 while the event ran 11-15 September). So the posting date is only
used to ignore old items; the event date is looked for in the listing text and
then in the item's own page. If no event date is found, a recent item is still
queued but marked date_confirmed=False, and the administrator sets the date
before approving it.
"""
import re
import time
from datetime import date, datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app import db
from app.models import Category, Event

DEFAULT_URL = "https://kabarak.ac.ke/events"
SITE_ROOT = "https://kabarak.ac.ke/"
USER_AGENT = "KabarakEventAggregatorBot/1.0 (+student project; contact: cs-it@kabarak.ac.ke)"
LOOKBACK_DAYS = 180  # items posted longer ago than this are ignored

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
MONTH_RE = (r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|"
            r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?")
ORD = r"(?:st|nd|rd|th)?"
# "15th - 19th Sept. 2025" / "11th to 15th September" -> first day of the range
RANGE_RE = re.compile(rf"\b(\d{{1,2}}){ORD}\s*(?:-|–|—|to)\s*\d{{1,2}}{ORD}\s+{MONTH_RE},?\s*(\d{{4}})?", re.I)
# "21st July 2023" / "7 of June"
DAY_MONTH_RE = re.compile(rf"\b(\d{{1,2}}){ORD}\s+(?:of\s+)?{MONTH_RE},?\s*(\d{{4}})?", re.I)
# "July 21, 2023" / "Sept 15th"
MONTH_DAY_RE = re.compile(rf"\b{MONTH_RE}\s+(\d{{1,2}}){ORD}(?!\d),?\s*(\d{{4}})?", re.I)

CATEGORY_KEYWORDS = [
    ("career", ["career", "job", "internship", "recruit", "employ", "cv ", "attachment", "industry"]),
    ("sports", ["sport", "tournament", "football", "rugby", "athletic", "basketball", "volleyball", "games", "marathon", "match"]),
    ("religious", ["worship", "chapel", "prayer", "church", "fellowship", "mass", "devotion", "crusade", "gospel"]),
    ("social", ["party", "festival", "concert", "cultural", "gala", "dinner", "club", "talent", "fun day", "music"]),
    ("academic", ["conference", "seminar", "workshop", "lecture", "symposium", "innovation", "research",
                  "webinar", "training", "graduation", "orientation", "exhibition"]),
]


# ------------------------------------------------------------------ helpers
def _parse_card_date(raw):
    raw = raw.strip().rstrip(",")
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _make_date(day, month_word, year, posted):
    month = MONTHS[month_word.lower()[:3]]
    y = int(year) if year else posted.year
    try:
        d = date(y, month, int(day))
    except ValueError:
        return None
    if not year and d < posted - timedelta(days=30):
        try:
            d = date(y + 1, month, int(day))  # e.g. posted in Nov about an event in Feb
        except ValueError:
            return None
    return d


def extract_event_date(text, posted):
    """Return the earliest date mentioned in `text` that falls after the posting
    date, or None. Dates on or before the posting day (such as a 'published on'
    line) are ignored, since an event is announced before it happens."""
    found = []
    for m in RANGE_RE.finditer(text):
        found.append((m.start(), _make_date(m.group(1), m.group(2), m.group(3), posted)))
    for m in DAY_MONTH_RE.finditer(text):
        found.append((m.start(), _make_date(m.group(1), m.group(2), m.group(3), posted)))
    for m in MONTH_DAY_RE.finditer(text):
        found.append((m.start(), _make_date(m.group(2), m.group(1), m.group(3), posted)))
    candidates = sorted(d for _, d in found if d and d > posted)
    return candidates[0] if candidates else None


def categorise(text):
    t = f" {text.lower()} "
    for name, words in CATEGORY_KEYWORDS:
        if any(w in t for w in words):
            return name
    return "academic"


def fetch_page(url):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
    resp.raise_for_status()
    return resp.text


def page_text(html):
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one(".item-page") or soup.select_one("article") or soup.body or soup
    return node.get_text(" ", strip=True)


# ------------------------------------------------------------------ parsing
def parse_cards(html):
    """Return every card on the listing page with its posting date."""
    soup = BeautifulSoup(html, "html.parser")
    cards = []
    for card in soup.select("article[class*='raxo-item']"):
        title_el = card.select_one("h4.raxo-title a, .raxo-title a")
        if not title_el or not title_el.get_text(strip=True):
            continue
        date_el = card.select_one("span.raxo-date, .raxo-date")
        posted = _parse_card_date(date_el.get_text(strip=True)) if date_el else None
        if not posted:
            continue
        desc_el = card.select_one("div.raxo-text, .raxo-text")
        img_el = card.select_one(".raxo-image img")
        href = title_el.get("href", "")
        cards.append({
            "title": title_el.get_text(strip=True),
            "posted": posted,
            "description": desc_el.get_text(strip=True) if desc_el else None,
            "source_url": urljoin(SITE_ROOT, href) if href else DEFAULT_URL,
            "banner_image_url": urljoin(SITE_ROOT, img_el.get("src")) if img_el and img_el.get("src") else None,
        })
    seen, unique = set(), []
    for c in cards:
        if (c["title"], c["posted"]) not in seen:
            seen.add((c["title"], c["posted"]))
            unique.append(c)
    return unique


def collect(html, fetch_detail=None, today=None, include_past=False, delay=0):
    """Turn listing-page HTML into event records ready for moderation.

    fetch_detail(url) -> html is used to read an item's own page when the
    listing text holds no event date. Returns (records, summary)."""
    today = today or date.today()
    cards = parse_cards(html)
    records = []
    for c in cards:
        if not include_past and c["posted"] < today - timedelta(days=LOOKBACK_DAYS):
            continue
        text = f"{c['title']} {c['description'] or ''}"
        event_date = extract_event_date(text, c["posted"])
        if event_date is None and fetch_detail and c["source_url"] != DEFAULT_URL:
            try:
                if delay:
                    time.sleep(delay)
                detail = page_text(fetch_detail(c["source_url"]))
                event_date = extract_event_date(detail, c["posted"])
                text = f"{text} {detail[:2000]}"
            except requests.RequestException:
                pass
        if event_date is not None and event_date < today and not include_past:
            continue  # the event has already happened
        records.append({
            **c,
            "date": event_date or c["posted"],
            "date_confirmed": event_date is not None,
            "category": categorise(text),
        })
    summary = {
        "listings_found": len(cards),
        "latest_posted": max((c["posted"] for c in cards), default=None),
        "upcoming_or_undated": len(records),
    }
    return records, summary


def save(records):
    """Insert records as pending events, skipping ones already scraped."""
    cats = {c.name: c for c in Category.query.all()}
    created = 0
    for r in records:
        if Event.query.filter_by(title=r["title"], source="scraped").first():
            continue
        cat = cats.get(r["category"]) or cats.get("academic")
        db.session.add(Event(
            title=r["title"], description=r.get("description"), date=r["date"],
            banner_image_url=r.get("banner_image_url"), category_id=cat.id,
            source="scraped", status="pending", date_confirmed=r["date_confirmed"],
        ))
        created += 1
    db.session.commit()
    return created


def run(url=DEFAULT_URL, include_past=False, delay=2):
    """Fetch, collect and save. Used by the CLI script and the admin endpoint."""
    html = fetch_page(url)
    records, summary = collect(html, fetch_detail=fetch_page, include_past=include_past, delay=delay)
    summary["added"] = save(records)
    summary["unconfirmed_dates"] = sum(1 for r in records if not r["date_confirmed"])
    return summary
