"""
P3 (Moderate Events): presents pending submissions to the Admin for
approval; only Admin-approved records become visible to students (P4).
Also covers the Admin use cases: manage users, view usage analytics.
"""
import time
from datetime import datetime, date

import requests
from flask import Blueprint, request, jsonify

from app import db
from app.models import Event, User, Notification
from app.utils.decorators import roles_required
from app.utils.notify import notify_students_of_new_event, notify_organiser_of_decision
from app.services import scraper

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/events/pending")
@roles_required("admin")
def pending_events():
    events = (Event.query.filter_by(status="pending")
              .order_by(Event.created_at.asc()).all())
    return jsonify(events=[e.to_dict(include_organiser=True) for e in events]), 200


@admin_bp.post("/events/<int:event_id>/approve")
@roles_required("admin")
def approve_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.status != "pending":
        return jsonify(error="Only pending events can be approved"), 409
    data = request.get_json(silent=True) or {}
    if data.get("date"):
        try:
            event.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify(error="date must be in YYYY-MM-DD format"), 400
        event.date_confirmed = True
    if not event.date_confirmed:
        return jsonify(error="Set the event date before approving this listing"), 409
    if event.date < date.today():
        return jsonify(error="This event's date has already passed, so it cannot be published"), 409
    event.status = "approved"
    event.reviewed_at = datetime.utcnow()
    db.session.commit()

    notify_students_of_new_event(event)
    notify_organiser_of_decision(event)
    return jsonify(event=event.to_dict()), 200


@admin_bp.post("/events/<int:event_id>/reject")
@roles_required("admin")
def reject_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.status != "pending":
        return jsonify(error="Only pending events can be rejected"), 409
    data = request.get_json(silent=True) or {}
    event.status = "rejected"
    event.reviewed_at = datetime.utcnow()
    event.rejection_reason = (data.get("reason") or "").strip() or None
    db.session.commit()

    notify_organiser_of_decision(event)
    return jsonify(event=event.to_dict()), 200


@admin_bp.get("/users")
@roles_required("admin")
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify(users=[u.to_dict() for u in users]), 200


@admin_bp.get("/analytics")
@roles_required("admin")
def analytics():
    """Admin use case: 'View aggregated usage analytics'."""
    total_events = Event.query.count()
    approved = Event.query.filter_by(status="approved").count()
    pending = Event.query.filter_by(status="pending").count()
    rejected = Event.query.filter_by(status="rejected").count()
    scraped = Event.query.filter_by(source="scraped").count()
    total_users = User.query.count()
    total_notifications = Notification.query.count()

    by_category = (
        db.session.query(Event.category_id, db.func.count(Event.id))
        .filter(Event.status == "approved")
        .group_by(Event.category_id)
        .all()
    )
    from app.models import Category
    category_breakdown = {}
    for cat_id, count in by_category:
        cat = Category.query.get(cat_id)
        category_breakdown[cat.name if cat else "Unknown"] = count

    return jsonify({
        "total_events": total_events,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "scraped_events": scraped,
        "total_users": total_users,
        "total_notifications": total_notifications,
        "events_by_category": category_breakdown,
    }), 200


_last_scrape = {"at": 0.0}
SCRAPE_COOLDOWN_SECONDS = 60


@admin_bp.post("/scrape")
@roles_required("admin")
def scrape_university_site():
    """P1 supplementary collection, started from the dashboard. A cooldown
    stops repeated clicks from sending a burst of requests to the site."""
    now = time.time()
    if now - _last_scrape["at"] < SCRAPE_COOLDOWN_SECONDS:
        return jsonify(error="Please wait a minute before importing again"), 429
    _last_scrape["at"] = now
    try:
        summary = scraper.run()
    except requests.RequestException:
        return jsonify(error="Could not reach the university website"), 502
    latest = summary["latest_posted"]
    summary["latest_posted"] = latest.isoformat() if latest else None
    return jsonify(summary), 200
