from app import db


class Category(db.Model):
    """CATEGORY entity (ERD, Figure 5). Decoupled from EVENT so the fixed
    taxonomy (academic, social, career, religious, sports) can be managed
    independently by the Admin, per the Natalia (2013) design rationale
    discussed in Chapter Two."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    events = db.relationship("Event", backref="category", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name}
