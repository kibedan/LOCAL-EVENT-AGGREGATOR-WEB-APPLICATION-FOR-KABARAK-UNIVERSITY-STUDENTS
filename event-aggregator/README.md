# Local Event Aggregator — Kabarak University

Implementation of the system proposed in the Chapter One–Three proposal
(Context Diagram, Level 1 DFD, Use Case Diagram, ERD, and UI prototypes).
Flask + SQLAlchemy backend, React (Vite) frontend.

## Quick start on Windows (no command line needed)

1. Install Python from python.org (tick **Add python.exe to PATH**).
2. Double-click **setup.bat** once. It installs the packages and creates the
   database with the demo accounts.
3. Double-click **start.bat** whenever you want to run the system. Your
   browser opens at http://localhost:5000. Close the black server window to stop.

The compiled interface is already included in `frontend/dist`, so Node.js is
only needed if you change the frontend code (`npm install`, `npm run build`).

## Architecture map (proposal → code)

| Proposal element | Where it lives |
|---|---|
| Context Diagram actors | `backend/app/routes/*` (Student/Organiser/Admin/University Website flows) |
| P1 Collect Data | `routes/events.py::submit_event`, `app/services/scraper.py` (CLI: `scripts/scraper.py`; dashboard: `POST /api/admin/scrape`) |
| P2 Process & Categorise | `models/event.py`, `routes/categories.py` |
| P3 Moderate Events | `routes/admin.py::approve_event` / `reject_event` |
| P4 Display & Filter | `routes/events.py::list_events` (public; upcoming events only unless `include_past=1`) |
| P5 Send Notifications | `utils/notify.py` (category-matched alerts), `routes/notifications.py`, `PUT /api/auth/me/interests` |
| ERD: USER, EVENT, CATEGORY, NOTIFICATION | `backend/app/models/` |
| Use Case Diagram | route + role guards in `utils/decorators.py` |
| Low/high-fidelity UI (Figures 6–7) | `frontend/src/pages/`, `frontend/src/index.css` |

## Audience ("For me" / "All events")

Students record their school (`backend/app/schools.py` holds the seven
schools). Organisers mark each event as open to all students or meant for
particular schools. Logged-in students see a **For me** view (open events plus
their school's) and can switch to **All events**; nothing is hidden from the
full listing. Alerts only go to students the event is open to.

## Layout

The interface is mobile-first (single column, bottom navigation). At 900px
and wider it switches to a desktop layout with a sidebar and a multi-column
event grid, so the same build works on phones, laptops and lab PCs.

## Prerequisites

- Python 3.10+
- Node.js 18+

## Backend setup

```bash
cd backend
pip install -r requirements.txt
python scripts/seed.py      # creates tables + demo accounts + sample events
python run.py                # runs on http://localhost:5000
```

Demo accounts (password for all: `Password123`). If you ran an older build, delete `backend/aggregator.db` first and re-seed:

| Role | Email |
|---|---|
| Student | student@kabarak.ac.ke |
| Organiser | organiser@kabarak.ac.ke |
| Admin | admin@kabarak.ac.ke |

By default the app uses a local SQLite file (`backend/aggregator.db`) so it
runs with zero external setup. To point it at PostgreSQL (the proposal's
target production database) instead, set an environment variable before
running:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/event_aggregator"
```

### Running the scraper (P1 supplementary collection)

From the admin dashboard, press **Import from university website**, or run:

```bash
cd backend
python scripts/scraper.py            # items posted in the last 180 days
python scripts/scraper.py --include-past
```

The date on each card of kabarak.ac.ke/events is the date the item was
*posted*, not the event date. The scraper therefore uses it only to skip old
items, looks for the event date in the listing text and then on the item's own
page, and assigns a category from keywords. Items with no recognisable event
date are queued with the date unconfirmed; the admin sets the date before
approving. Everything lands as `pending` and goes through moderation (P3).
A one-minute cooldown stops repeated imports from hammering the site.

### Running the tests

```bash
cd backend
pip install pytest
python -m pytest tests -q        # 38 tests, in-memory database
```

> If you ran an earlier build, delete `backend/aggregator.db` and re-run
> `python scripts/seed.py`: the `users` table gained an `interests` column.

## Frontend setup

```bash
cd frontend
npm install
npm run dev                  # runs on http://localhost:5173
```

The dev server proxies `/api/*` to `http://localhost:5000`, so start the
backend first. Open http://localhost:5173 and log in with a demo account.

To build for production:

```bash
npm run build                # outputs static files to frontend/dist/
```

## Project structure

```
backend/
  app/
    models/        # User, Event, Category, Notification (ERD entities)
    routes/        # auth, events, categories, admin, notifications
    utils/         # role-guard decorator, notification fan-out
    config.py
    __init__.py     # app factory
  scripts/
    seed.py          # DB bootstrap + demo data
    scraper.py       # BeautifulSoup collector
  run.py
  requirements.txt

frontend/
  src/
    api/client.js      # fetch wrapper
    context/            # auth state
    components/         # Header, BottomNav, EventCard, ProtectedRoute
    pages/               # Home, Search, EventDetail, Login, Register,
                          # SubmitEvent, MySubmissions, AdminDashboard,
                          # Notifications, Profile
    index.css            # design tokens (navy/blue/green, per Figure 7)
  vite.config.js
  package.json
```

## Security notes (Chapter Two alignment)

- Passwords hashed with bcrypt, never stored or logged in plaintext.
- Auth is stateless JWT (`flask-jwt-extended`); role is embedded as a claim
  and checked server-side on every protected route via `roles_required()`.
- All database access goes through SQLAlchemy's ORM — no raw/string-built
  SQL anywhere, which rules out SQL injection by construction.
- CORS is scoped to `/api/*` only.
- The scraper identifies itself with a descriptive `User-Agent`, rate-limits
  requests, and only ever targets the university's own public events page.

## Known limitations / next steps

This is a working proposal implementation, not a hardened production
deployment. Before any real deployment:

- Move `JWT_SECRET_KEY` out of source and into a real secrets manager.
- Add HTTPS termination (e.g. behind nginx) — JWTs must not travel over
  plain HTTP.
- Add automated tests (the manual test pass covered the core flows:
  register/login, submit → approve → notify → filter/search, and role
  enforcement, but there's no CI test suite yet).
- Notification delivery is in-app only; email/push is out of scope per
  the proposal's timeline.
- The scraper's CSS selectors are generic placeholders and need to be
  tailored to the actual university events page markup.
