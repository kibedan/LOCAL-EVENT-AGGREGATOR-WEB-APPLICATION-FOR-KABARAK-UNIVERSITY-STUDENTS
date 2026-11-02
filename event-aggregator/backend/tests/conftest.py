import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Category


class TestConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-secret"
    TESTING = True
    SCRAPE_RATE_LIMIT_SECONDS = 0


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        for name in ["academic", "social", "career", "religious", "sports"]:
            db.session.add(Category(name=name))
        for full_name, email, role in [
            ("Test Admin", "admin@test.ke", "admin"),
            ("Test Organiser", "org@test.ke", "organiser"),
            ("Test Student", "stu@test.ke", "student"),
            ("Other Student", "stu2@test.ke", "student"),
        ]:
            u = User(full_name=full_name, email=email, role=role)
            u.set_password("Password123")
            db.session.add(u)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, password="Password123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.get_json()['token']}"}


@pytest.fixture()
def admin(client):
    return login(client, "admin@test.ke")


@pytest.fixture()
def organiser(client):
    return login(client, "org@test.ke")


@pytest.fixture()
def student(client):
    return login(client, "stu@test.ke")


@pytest.fixture()
def student2(client):
    return login(client, "stu2@test.ke")
