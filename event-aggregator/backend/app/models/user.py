from datetime import datetime
from app import db, bcrypt


class User(db.Model):
    """USER entity (ERD, Figure 5). Role gates which features are accessible."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    # role in {'student', 'organiser', 'admin'}
    organisation = db.Column(db.String(150), nullable=True)  # for organisers
    # Comma-separated category names the student opted in to alerts for (P5).
    interests = db.Column(db.String(200), nullable=True)
    # School code from app/schools.py; drives the feed's "For me" view.
    school = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    events = db.relationship("Event", backref="organiser", lazy=True,
                              foreign_keys="Event.organiser_id")
    notifications = db.relationship("Notification", backref="user", lazy=True)

    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "organisation": self.organisation,
            "interests": self.interest_list(),
            "school": self.school,
        }

    def interest_list(self):
        return [i for i in (self.interests or "").split(",") if i]
