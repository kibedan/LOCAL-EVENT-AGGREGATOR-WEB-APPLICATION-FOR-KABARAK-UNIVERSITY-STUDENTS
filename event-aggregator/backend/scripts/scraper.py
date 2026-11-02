"""
Command-line entry point for the supplementary scraper (P1).
The logic lives in app/services/scraper.py, which the admin dashboard's
"Import from university website" button also uses.

Run:  py scripts/scraper.py            (only items posted in the last 180 days)
      py scripts/scraper.py --include-past
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.config import Config
from app.services import scraper


def main():
    parser = argparse.ArgumentParser(description="Import upcoming events from the university's public events page.")
    parser.add_argument("url", nargs="?", default=scraper.DEFAULT_URL)
    parser.add_argument("--include-past", action="store_true",
                        help="Also keep old items and events that have already happened (for testing)")
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        s = scraper.run(args.url, include_past=args.include_past, delay=Config.SCRAPE_RATE_LIMIT_SECONDS)
    latest = s["latest_posted"].strftime("%d %B %Y") if s["latest_posted"] else "none"
    print(f"Listings on the page: {s['listings_found']} (latest posted {latest}). "
          f"Upcoming or undated: {s['upcoming_or_undated']}. Added to the moderation queue: {s['added']}"
          f" ({s['unconfirmed_dates']} need a date set by the administrator).")


if __name__ == "__main__":
    main()
