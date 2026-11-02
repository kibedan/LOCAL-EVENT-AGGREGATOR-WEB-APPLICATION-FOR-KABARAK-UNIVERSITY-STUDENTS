"""Scraper tests. The fixtures reproduce the card markup of the live
kabarak.ac.ke/events page (Raxo module), where the date on each card is the
POSTING date, e.g. 'Central Rift Innovation Week, 2023' posted Jul 26, 2023
for an event held 11-15 September 2023."""
from datetime import date

import requests

from app import db
from app.models import Event
from app.services import scraper
from app.services.scraper import collect, extract_event_date, categorise, parse_cards

TODAY = date(2026, 10, 28)


def card(title, posted, href="/events/sample", text="Short description."):
    return f"""
    <article class="raxo-item-nor raxo-item-1">
      <div class="raxo-image"><a href="{href}"><img src="/images/a.jpg"></a></div>
      <div class="raxo-content">
        <h4 class="raxo-title"><a href="{href}">{title}</a></h4>
        <div class="raxo-info"><span class="raxo-date">{posted}</span></div>
        <div class="raxo-text">{text}</div>
      </div>
    </article>"""


def test_card_date_is_read_as_posting_date():
    cards = parse_cards(card("Central Rift Innovation Week, 2023", "Jul 26, 2023", href="/events/criw-2023"))
    assert cards[0]["posted"] == date(2023, 7, 26)
    assert cards[0]["source_url"] == "https://kabarak.ac.ke/events/criw-2023"


def test_event_date_found_in_text_after_posting_date():
    posted = date(2025, 8, 1)
    assert extract_event_date("2025 Central Rift Innovation Week, 15th - 19th Sept. 2025", posted) == date(2025, 9, 15)
    assert extract_event_date("Career Day, Friday 21st July", date(2023, 7, 1)) == date(2023, 7, 21)
    assert extract_event_date("Published May 08, 2026. Join us on June 12, 2026.", date(2026, 5, 8)) == date(2026, 6, 12)
    assert extract_event_date("Our Vice-Chancellor is leading the delegation", posted) is None


def test_year_rolls_over_when_missing():
    assert extract_event_date("Opening ceremony on 14th February", date(2026, 11, 20)) == date(2027, 2, 14)


def test_old_posts_ignored_and_past_events_dropped():
    html = (card("Annual Law Conference, 2023", "Jul 20, 2023")
            + card("Hackathon", "Oct 01, 2026", text="Teams meet on 2nd October 2026 in the CS lab."))
    records, summary = collect(html, today=TODAY)
    assert records == []
    assert summary["listings_found"] == 2
    assert summary["latest_posted"] == date(2026, 10, 1)


def test_upcoming_event_found_on_detail_page():
    html = card("Science Fair", "Oct 20, 2026", href="/events/fair", text="All students invited.")
    pages = {"https://kabarak.ac.ke/events/fair": "<div class='item-page'>Posted Oct 20, 2026. The fair runs 12th - 14th November 2026.</div>"}
    records, _ = collect(html, fetch_detail=pages.__getitem__, today=TODAY)
    assert records[0]["date"] == date(2026, 11, 12)
    assert records[0]["date_confirmed"] is True


def test_recent_post_without_event_date_is_queued_unconfirmed():
    html = card("Innovation Week Concept Note", "Oct 15, 2026", text="The delegation will attend.")
    records, _ = collect(html, fetch_detail=lambda url: "<p>No date given.</p>", today=TODAY)
    assert records[0]["date_confirmed"] is False


def test_keyword_categories():
    assert categorise("Career Day for final year students") == "career"
    assert categorise("Inter-faculty football tournament") == "sports"
    assert categorise("Annual Law Conference") == "academic"
    assert categorise("Something else entirely") == "academic"


def test_admin_import_endpoint_saves_pending_events(client, admin, monkeypatch):
    listing = card("Career Day", "Oct 25, 2026", text="Friday 6th November 2026, main hall.")
    monkeypatch.setattr(scraper, "fetch_page", lambda url: listing)
    scraper_route = __import__("app.routes.admin", fromlist=["_last_scrape"])
    scraper_route._last_scrape["at"] = 0
    res = client.post("/api/admin/scrape", headers=admin)
    assert res.status_code == 200
    assert res.get_json()["added"] == 1
    ev = Event.query.filter_by(source="scraped").one()
    assert ev.status == "pending" and ev.category.name == "career" and ev.date == date(2026, 11, 6)
    again = client.post("/api/admin/scrape", headers=admin)
    assert again.status_code == 429  # cooldown protects the university site


def test_admin_import_reports_unreachable_site(client, admin, monkeypatch):
    def boom(url):
        raise requests.ConnectionError("offline")
    monkeypatch.setattr(scraper, "fetch_page", boom)
    __import__("app.routes.admin", fromlist=["_last_scrape"])._last_scrape["at"] = 0
    res = client.post("/api/admin/scrape", headers=admin)
    assert res.status_code == 502


def test_unconfirmed_listing_needs_date_before_approval(client, admin, app):
    from app.models import Category
    ev = Event(title="Undated Listing", date=date.today(), category_id=Category.query.first().id,
               source="scraped", status="pending", date_confirmed=False)
    db.session.add(ev)
    db.session.commit()
    refused = client.post(f"/api/admin/events/{ev.id}/approve", headers=admin)
    assert refused.status_code == 409
    future = date.today().replace(year=date.today().year + 1).isoformat()
    ok = client.post(f"/api/admin/events/{ev.id}/approve", json={"date": future}, headers=admin)
    assert ok.status_code == 200
    assert ok.get_json()["event"]["date"] == future
