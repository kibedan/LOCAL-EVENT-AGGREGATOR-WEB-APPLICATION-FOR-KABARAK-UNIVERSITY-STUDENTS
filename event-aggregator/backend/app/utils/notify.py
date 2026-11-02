"""
P5 (Send Notifications) from the Level 1 DFD: when an event relevant to a
user's interests is published, a Notification row is created. A real
deployment would also push this over email/websocket; for this build the
row itself is the deliverable and the frontend polls GET /api/notifications.
"""
from app import db
from app.models import Notification, User
from app.schools import audience_list


def notify_students_of_new_event(event):
    """P5: when an event is approved, create an in-app notification only for
    students who opted in to that event's category (preferences held in D2).
    Students with no matching interest are not notified; they can still find
    the event by pulling the feed (P4)."""
    category_name = event.category.name if event.category else None
    schools = audience_list(event.audience)  # empty list = open to everyone
    students = [
        s for s in User.query.filter_by(role="student").all()
        if category_name and category_name in s.interest_list()
        and (not schools or s.school in schools)
    ]
    for student in students:
        db.session.add(Notification(
            user_id=student.id,
            event_id=event.id,
            message=f'New event published: "{event.title}" on {event.date}.',
        ))
    db.session.commit()


def notify_organiser_of_decision(event):
    if not event.organiser_id:
        return
    verb = "approved" if event.status == "approved" else "rejected"
    db.session.add(Notification(
        user_id=event.organiser_id,
        event_id=event.id,
        message=f'Your submission "{event.title}" was {verb}.',
    ))
    db.session.commit()
