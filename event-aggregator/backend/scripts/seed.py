"""
Creates all tables and seeds the fixed category taxonomy plus one demo
account per role, so the app is usable immediately after clone.

Run:  python scripts/seed.py
"""
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Category, Event

CATEGORIES = ["academic", "social", "career", "religious", "sports"]

DEMO_USERS = [
    dict(full_name="Amina Wanjiru", email="student@kabarak.ac.ke",
         password="Password123", role="student",
         interests="academic,career,sports", school="sset"),
    dict(full_name="Brian Otieno", email="organiser@kabarak.ac.ke",
         password="Password123", role="organiser", organisation="CS Student Association"),
    dict(full_name="System Admin", email="admin@kabarak.ac.ke",
         password="Password123", role="admin"),
]


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        cat_objs = {}
        for name in CATEGORIES:
            cat = Category.query.filter_by(name=name).first()
            if not cat:
                cat = Category(name=name)
                db.session.add(cat)
            cat_objs[name] = cat
        db.session.commit()

        users = {}
        for u in DEMO_USERS:
            existing = User.query.filter_by(email=u["email"]).first()
            if existing:
                users[u["role"]] = existing
                continue
            user = User(full_name=u["full_name"], email=u["email"], role=u["role"],
                        organisation=u.get("organisation"),
                        interests=u.get("interests"), school=u.get("school"))
            user.set_password(u["password"])
            db.session.add(user)
            users[u["role"]] = user
        db.session.commit()

        if Event.query.count() == 0:
            demo_events = [
                dict(title="Python for Beginners Workshop",
                     description="Hands-on intro to Python scripting for CS Lab 3.",
                     date=date.today() + timedelta(days=7), time="14:00",
                     location="CS Lab 3, Block B", category="academic", status="approved"),
                dict(title="Inter-Faculty Rugby Tournament",
                     description="Knockout rounds on the main sports field.",
                     date=date.today() + timedelta(days=10), time="08:00",
                     location="Sports Field", category="sports", status="approved"),
                dict(title="Career Fair 2026",
                     description="Meet recruiters from 20+ companies.",
                     date=date.today() + timedelta(days=14), time="09:00",
                     location="Main Hall", category="career", status="pending"),
            ]
            organiser = users["organiser"]
            for e in demo_events:
                db.session.add(Event(
                    title=e["title"], description=e["description"], date=e["date"],
                    time=e["time"], location=e["location"],
                    category_id=cat_objs[e["category"]].id,
                    organiser_id=organiser.id, source="organiser", status=e["status"],
                ))
            db.session.commit()

        print("Seed complete.")
        print("Demo accounts (password: Password123):")
        for u in DEMO_USERS:
            print(f"  - {u['role']:<10} {u['email']}")


if __name__ == "__main__":
    run()
