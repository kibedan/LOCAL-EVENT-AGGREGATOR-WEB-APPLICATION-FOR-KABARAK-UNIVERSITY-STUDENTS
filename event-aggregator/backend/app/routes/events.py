"""
P4 (Display and Filter): GET /api/events supports category, date, location
and keyword filters, matching the Level 1 DFD and the low/high-fidelity
UI prototypes (Figures 6-7).

P1 (Collect Data, organiser branch): POST /api/events lets a verified
organiser submit an event, landing in D1 with status='pending' until an
Admin actions it (P3).
"""
from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app import db
from app.models import Event, Category
from app.utils.decorators import roles_required
from app.schools import SCHOOLS, parse_audience

events_bp = Blueprint("events", __name__)


@events_bp.get("")
def list_events():
    """Public feed. Only approved events are visible to unauthenticated /
    student users - Process 4 never reads from D2 (User Database), so
    browsing works for anonymous guests as well as logged-in students."""
    query = Event.query.filter_by(status="approved")

    # Events are transient: once the date has passed the listing is no longer
    # useful, so the feed shows today and later unless include_past=1 is sent.
    if request.args.get("include_past") != "1":
        query = query.filter(Event.date >= date.today())

    category = request.args.get("category")
    if category:
        query = query.join(Category).filter(Category.name.ilike(category))

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if date_from:
        query = query.filter(Event.date >= date_from)
    if date_to:
        query = query.filter(Event.date <= date_to)

    location = request.args.get("location")
    if location:
        query = query.filter(Event.location.ilike(f"%{location}%"))

    # "For me" view: events open to everyone plus those for the student's school.
    for_school = (request.args.get("for_school") or "").strip().lower()
    if for_school in SCHOOLS:
        query = query.filter(db.or_(
            Event.audience == "all",
            Event.audience == for_school,
            Event.audience.like(f"{for_school},%"),
            Event.audience.like(f"%,{for_school}"),
            Event.audience.like(f"%,{for_school},%"),
        ))

    keyword = request.args.get("q")
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(db.or_(Event.title.ilike(like), Event.description.ilike(like)))

    query = query.order_by(Event.date.asc())
    events = query.all()
    return jsonify(events=[e.to_dict(include_organiser=True) for e in events]), 200


@events_bp.get("/<int:event_id>")
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.status != "approved":
        return jsonify(error="Event not found"), 404
    return jsonify(event=event.to_dict(include_organiser=True)), 200


@events_bp.post("")
@roles_required("organiser", "admin")
def submit_event():
    """P1: verified-organiser submission portal branch."""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    date_str = data.get("date")
    category_id = data.get("category_id")

    if not title or not date_str or not category_id:
        return jsonify(error="title, date and category_id are required"), 400
    try:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify(error="date must be in YYYY-MM-DD format"), 400
    if event_date < date.today():
        return jsonify(error="Event date cannot be in the past"), 400
    if not Category.query.get(category_id):
        return jsonify(error="Unknown category_id"), 400
    try:
        audience = parse_audience(data.get("audience"))
    except ValueError as err:
        return jsonify(error=str(err)), 400

    event = Event(
        title=title,
        description=(data.get("description") or "").strip(),
        date=event_date,
        time=data.get("time"),
        location=(data.get("location") or "").strip(),
        banner_image_url=data.get("banner_image_url"),
        category_id=category_id,
        organiser_id=get_jwt_identity(),
        source="organiser",
        status="pending",
        audience=audience,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event=event.to_dict()), 201


@events_bp.get("/mine")
@roles_required("organiser", "admin")
def my_submissions():
    """Use case: Event Organiser 'Track Submission Status'."""
    user_id = get_jwt_identity()
    events = (Event.query.filter_by(organiser_id=user_id)
              .order_by(Event.created_at.desc()).all())
    return jsonify(events=[e.to_dict() for e in events]), 200


@events_bp.put("/<int:event_id>")
@roles_required("organiser", "admin")
def update_event(event_id):
    """Organiser can edit/withdraw their own submission before it is
    reviewed (per the organiser survey's requested feature)."""
    event = Event.query.get_or_404(event_id)
    claims = get_jwt()
    if claims.get("role") != "admin" and str(event.organiser_id) != get_jwt_identity():
        return jsonify(error="Forbidden"), 403
    if event.status != "pending":
        return jsonify(error="Only pending submissions can be edited"), 409

    data = request.get_json(silent=True) or {}
    for field in ["title", "description", "time", "location", "banner_image_url"]:
        if field in data:
            setattr(event, field, data[field])
    if "date" in data:
        try:
            new_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify(error="date must be in YYYY-MM-DD format"), 400
        if new_date < date.today():
            return jsonify(error="Event date cannot be in the past"), 400
        event.date = new_date
    if "audience" in data:
        try:
            event.audience = parse_audience(data["audience"])
        except ValueError as err:
            return jsonify(error=str(err)), 400
    if "category_id" in data:
        if not Category.query.get(data["category_id"]):
            return jsonify(error="Unknown category_id"), 400
        event.category_id = data["category_id"]

    db.session.commit()
    return jsonify(event=event.to_dict()), 200


@events_bp.delete("/<int:event_id>")
@roles_required("organiser", "admin")
def withdraw_event(event_id):
    event = Event.query.get_or_404(event_id)
    claims = get_jwt()
    if claims.get("role") != "admin" and str(event.organiser_id) != get_jwt_identity():
        return jsonify(error="Forbidden"), 403
    db.session.delete(event)
    db.session.commit()
    return jsonify(message="Withdrawn"), 200
