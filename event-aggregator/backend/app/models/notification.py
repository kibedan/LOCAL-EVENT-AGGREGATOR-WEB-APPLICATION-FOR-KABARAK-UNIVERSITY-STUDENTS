from datetime import datetime
from app import db


class Notification(db.Model):
    """NOTIFICATION entity (ERD, Figure 5). Links a User to an Event and
    tracks read status, implementing P5 (Send Notifications)."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "message": self.message,
            "is_read": self.is_read,
            # Stored as naive UTC; the trailing "Z" lets browsers convert to local time (EAT).
            "created_at": (self.created_at.isoformat() + "Z") if self.created_at else None,
        }
