from datetime import date, timedelta

from app import db
from app.models import Category, Event, Notification, User


def cat_id(name):
    return Category.query.filter_by(name=name).first().id


def future(days):
    return (date.today() + timedelta(days=days)).isoformat()


def submit(client, headers, title="Chess Night", category="social", days=5, **extra):
    body = dict(title=title, date=future(days), category_id=cat_id(category), **extra)
    return client.post("/api/events", json=body, headers=headers)


def publish(client, organiser, admin, **kw):
    res = submit(client, organiser, **kw)
    event_id = res.get_json()["event"]["id"]
    client.post(f"/api/admin/events/{event_id}/approve", headers=admin)
    return event_id


# ---------- Authentication and access control ----------

def test_register_student_succeeds(client):
    res = client.post("/api/auth/register", json={
        "full_name": "New Student", "email": "new@kabarak.ac.ke", "password": "Password123"})
    assert res.status_code == 201
    assert res.get_json()["user"]["role"] == "student"


def test_register_duplicate_email_rejected(client):
    res = client.post("/api/auth/register", json={
        "full_name": "Dup", "email": "stu@test.ke", "password": "Password123"})
    assert res.status_code == 409


def test_register_short_password_rejected(client):
    res = client.post("/api/auth/register", json={
        "full_name": "Short", "email": "short@test.ke", "password": "abc"})
    assert res.status_code == 400


def test_admin_cannot_self_register(client):
    res = client.post("/api/auth/register", json={
        "full_name": "Evil", "email": "evil@test.ke", "password": "Password123", "role": "admin"})
    assert res.status_code == 403


def test_login_failure_message_is_generic(client):
    wrong_pw = client.post("/api/auth/login", json={"email": "stu@test.ke", "password": "nope"})
    no_user = client.post("/api/auth/login", json={"email": "ghost@test.ke", "password": "nope"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.get_json() == no_user.get_json()


def test_passwords_are_stored_hashed(app):
    user = User.query.filter_by(email="stu@test.ke").first()
    assert user.password_hash != "Password123"
    assert user.password_hash.startswith("$2")


def test_student_cannot_submit_event(client, student):
    assert submit(client, student).status_code == 403


def test_anonymous_cannot_read_admin_analytics(client):
    assert client.get("/api/admin/analytics").status_code == 401


def test_organiser_cannot_approve_events(client, organiser):
    event_id = submit(client, organiser).get_json()["event"]["id"]
    res = client.post(f"/api/admin/events/{event_id}/approve", headers=organiser)
    assert res.status_code == 403


# ---------- P1 / P3: submission and moderation ----------

def test_submission_starts_pending_and_is_hidden_from_feed(client, organiser):
    res = submit(client, organiser, title="Hidden Until Approved")
    assert res.status_code == 201
    assert res.get_json()["event"]["status"] == "pending"
    feed = client.get("/api/events").get_json()["events"]
    assert all(e["title"] != "Hidden Until Approved" for e in feed)


def test_submission_requires_valid_fields(client, organiser):
    assert client.post("/api/events", json={"title": "No date"}, headers=organiser).status_code == 400
    bad_date = client.post("/api/events", json={
        "title": "Bad", "date": "05/06/2026", "category_id": cat_id("social")}, headers=organiser)
    assert bad_date.status_code == 400
    past = client.post("/api/events", json={
        "title": "Too Late", "date": (date.today() - timedelta(days=1)).isoformat(),
        "category_id": cat_id("social")}, headers=organiser)
    assert past.status_code == 400
    assert "past" in past.get_json()["error"]


def test_approved_event_appears_in_feed(client, organiser, admin):
    publish(client, organiser, admin, title="Now Visible")
    feed = client.get("/api/events").get_json()["events"]
    assert [e["title"] for e in feed] == ["Now Visible"]


def test_reject_records_reason_and_stays_hidden(client, organiser, admin):
    event_id = submit(client, organiser).get_json()["event"]["id"]
    res = client.post(f"/api/admin/events/{event_id}/reject",
                      json={"reason": "Incomplete details"}, headers=admin)
    assert res.status_code == 200
    assert res.get_json()["event"]["status"] == "rejected"
    mine = client.get("/api/events/mine", headers=organiser).get_json()["events"]
    assert mine[0]["rejection_reason"] == "Incomplete details"
    assert client.get(f"/api/events/{event_id}").status_code == 404


def test_cannot_approve_twice(client, organiser, admin):
    event_id = publish(client, organiser, admin)
    res = client.post(f"/api/admin/events/{event_id}/approve", headers=admin)
    assert res.status_code == 409


def test_organiser_can_track_own_submissions(client, organiser):
    submit(client, organiser, title="Tracked")
    mine = client.get("/api/events/mine", headers=organiser).get_json()["events"]
    assert [e["title"] for e in mine] == ["Tracked"]


# ---------- P4: display and filter ----------

def test_filters_by_category_keyword_location_and_date(client, organiser, admin):
    publish(client, organiser, admin, title="Python Workshop", category="academic",
            days=3, location="CS Lab", description="Learn scripting")
    publish(client, organiser, admin, title="Rugby Finals", category="sports",
            days=20, location="Sports Field", description="Free food at halftime")

    def titles(qs):
        return [e["title"] for e in client.get(f"/api/events?{qs}").get_json()["events"]]

    assert titles("category=sports") == ["Rugby Finals"]
    assert titles("q=free food") == ["Rugby Finals"]
    assert titles("location=lab") == ["Python Workshop"]
    assert titles(f"date_to={future(10)}") == ["Python Workshop"]
    assert titles(f"date_from={future(10)}") == ["Rugby Finals"]
    assert titles("") == ["Python Workshop", "Rugby Finals"]


def test_past_events_hidden_unless_requested(client, organiser, admin, app):
    event_id = publish(client, organiser, admin, title="Upcoming Talk", days=2)
    old = Event.query.get(event_id)
    db.session.add(Event(title="Last Year's Fair", date=date.today() - timedelta(days=30),
                         category_id=old.category_id, status="approved", source="organiser"))
    db.session.commit()
    titles = [e["title"] for e in client.get("/api/events").get_json()["events"]]
    assert titles == ["Upcoming Talk"]
    with_past = [e["title"] for e in client.get("/api/events?include_past=1").get_json()["events"]]
    assert "Last Year's Fair" in with_past


# ---------- P5: notifications ----------

def set_interests(client, headers, interests):
    return client.put("/api/auth/me/interests", json={"interests": interests}, headers=headers)


def test_only_opted_in_students_are_notified(client, organiser, admin, student, student2):
    assert set_interests(client, student, ["sports"]).status_code == 200
    assert set_interests(client, student2, ["career"]).status_code == 200
    publish(client, organiser, admin, title="Rugby Finals", category="sports")

    mine = client.get("/api/notifications", headers=student).get_json()["notifications"]
    other = client.get("/api/notifications", headers=student2).get_json()["notifications"]
    assert len(mine) == 1 and "Rugby Finals" in mine[0]["message"]
    assert other == []


def test_student_with_no_interests_receives_nothing(client, organiser, admin, student):
    publish(client, organiser, admin, category="sports")
    assert client.get("/api/notifications", headers=student).get_json()["notifications"] == []


def test_organiser_notified_of_decision(client, organiser, admin):
    publish(client, organiser, admin, title="Decided")
    notes = client.get("/api/notifications", headers=organiser).get_json()["notifications"]
    assert any("approved" in n["message"] for n in notes)


def test_unknown_interest_category_rejected(client, student):
    assert set_interests(client, student, ["underwater-basket-weaving"]).status_code == 400


def test_cannot_mark_another_users_notification_read(client, organiser, admin, student, student2):
    set_interests(client, student, ["sports"])
    publish(client, organiser, admin, category="sports")
    note_id = client.get("/api/notifications", headers=student).get_json()["notifications"][0]["id"]
    assert client.post(f"/api/notifications/{note_id}/read", headers=student2).status_code == 403
    assert client.post(f"/api/notifications/{note_id}/read", headers=student).status_code == 200


# ---------- Admin analytics ----------

def test_analytics_counts(client, organiser, admin):
    publish(client, organiser, admin, category="sports")
    submit(client, organiser)
    data = client.get("/api/admin/analytics", headers=admin).get_json()
    assert data["approved"] == 1 and data["pending"] == 1
    assert data["events_by_category"] == {"sports": 1}


# ---------- Timestamps ----------

def test_timestamps_are_marked_as_utc(client, organiser, admin, student):
    set_interests(client, student, ["sports"])
    publish(client, organiser, admin, category="sports")
    note = client.get("/api/notifications", headers=student).get_json()["notifications"][0]
    assert note["created_at"].endswith("Z")


# ---------- Audience: "For me" view and school-aware alerts ----------

def set_school(client, headers, school):
    return client.put("/api/auth/me/school", json={"school": school}, headers=headers)


def test_for_me_view_shows_open_events_and_own_school_only(client, organiser, admin):
    publish(client, organiser, admin, title="Open Lecture")
    publish(client, organiser, admin, title="Gastroenterology Case Seminar", audience=["medicine"])
    publish(client, organiser, admin, title="Moot Court on Jurisdiction", audience=["law", "business"])

    def titles(qs):
        return sorted(e["title"] for e in client.get(f"/api/events?{qs}").get_json()["events"])

    assert titles("for_school=music") == ["Open Lecture"]
    assert titles("for_school=law") == ["Moot Court on Jurisdiction", "Open Lecture"]
    assert len(titles("")) == 3  # "All events" still shows everything


def test_unknown_school_rejected(client, organiser):
    res = submit(client, organiser, audience=["astrology"])
    assert res.status_code == 400
    reg = client.post("/api/auth/register", json={
        "full_name": "X", "email": "x@test.ke", "password": "Password123", "school": "nowhere"})
    assert reg.status_code == 400


def test_register_with_school(client):
    res = client.post("/api/auth/register", json={
        "full_name": "Music Student", "email": "music@test.ke", "password": "Password123", "school": "music"})
    assert res.status_code == 201 and res.get_json()["user"]["school"] == "music"


def test_alerts_respect_event_audience(client, organiser, admin, student, student2):
    set_interests(client, student, ["academic"])
    set_interests(client, student2, ["academic"])
    set_school(client, student, "music")
    set_school(client, student2, "medicine")
    publish(client, organiser, admin, title="Clinical Seminar", category="academic", audience=["medicine"])
    publish(client, organiser, admin, title="Public Lecture", category="academic")

    def alerts(h):
        return sorted(n["message"] for n in client.get("/api/notifications", headers=h).get_json()["notifications"])

    assert len(alerts(student)) == 1 and "Public Lecture" in alerts(student)[0]
    assert len(alerts(student2)) == 2
