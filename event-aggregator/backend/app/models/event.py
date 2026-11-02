from datetime import datetime
from app import db
from app.schools import audience_list


class Event(db.Model):
    """EVENT entity (ERD, Figure 5).

    status gates visibility to students: Pending -> Approved / Rejected,
    implementing P3 (Moderate Events) from the Level 1 DFD.
    source distinguishes organiser submissions from scraped listings,
    matching the two inbound data flows on the Context Diagram.
    """

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    banner_image_url = db.Column(db.String(300), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pending")
    # status in {'pending', 'approved', 'rejected'}
    source = db.Column(db.String(20), nullable=False, default="organiser")
    # source in {'organiser', 'scraped'}

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    organiser_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.String(300), nullable=True)
    # False for scraped items whose event date could not be found; the
    # administrator must set the date before the event can be approved.
    date_confirmed = db.Column(db.Boolean, nullable=False, default=True)
    # 'all' or comma-separated school codes (app/schools.py).
    audience = db.Column(db.String(200), nullable=False, default="all")

    notifications = db.relationship("Notification", backref="event", lazy=True)

    def to_dict(self, include_organiser=False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "time": self.time,
            "location": self.location,
            "banner_image_url": self.banner_image_url,
            "status": self.status,
            "source": self.source,
            "category": self.category.name if self.category else None,
            "category_id": self.category_id,
            "rejection_reason": self.rejection_reason,
            "date_confirmed": self.date_confirmed,
            "audience": audience_list(self.audience),
            # Stored as naive UTC; the trailing "Z" lets browsers convert to local time (EAT).
            "created_at": (self.created_at.isoformat() + "Z") if self.created_at else None,
        }
        if include_organiser and self.organiser:
            data["organiser"] = self.organiser.full_name
        return data
