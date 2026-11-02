"""
Registration / Login.

Passwords are hashed with bcrypt (never stored in plaintext) and sessions
are stateless JWTs, matching the OWASP-informed security posture described
in Chapter Two (parameterised queries via the ORM, hashed passwords, no
raw SQL string interpolation anywhere in this codebase).
"""
import re
from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app import db
from app.models import User, Category
from app.schools import SCHOOLS

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_ROLES = {"student", "organiser", "admin"}


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "student")
    organisation = (data.get("organisation") or "").strip() or None
    school = (data.get("school") or "").strip().lower() or None
    if school and school not in SCHOOLS:
        return jsonify(error="Unknown school"), 400

    if not full_name or not email or not password:
        return jsonify(error="full_name, email and password are required"), 400
    if not EMAIL_RE.match(email):
        return jsonify(error="Invalid email address"), 400
    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters"), 400
    if role not in VALID_ROLES:
        return jsonify(error="Invalid role"), 400
    # Admin accounts are provisioned manually (see scripts/seed.py), not self-registered.
    if role == "admin":
        return jsonify(error="Admin accounts cannot self-register"), 403
    if User.query.filter_by(email=email).first():
        return jsonify(error="An account with this email already exists"), 409

    user = User(full_name=full_name, email=email, role=role, organisation=organisation, school=school)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(token=token, user=user.to_dict()), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        # Deliberately generic message: do not reveal whether the email exists.
        return jsonify(error="Invalid email or password"), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(token=token, user=user.to_dict()), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get_or_404(get_jwt_identity())
    return jsonify(user=user.to_dict()), 200


@auth_bp.put("/me/interests")
@jwt_required()
def update_interests():
    """Stores the categories a student opted in to alerts for. P5 reads this
    (D2) when deciding who to notify about a newly published event."""
    user = User.query.get_or_404(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    requested = data.get("interests")
    if not isinstance(requested, list):
        return jsonify(error="interests must be a list of category names"), 400
    valid = {c.name for c in Category.query.all()}
    cleaned = sorted({str(i).strip().lower() for i in requested})
    if any(i not in valid for i in cleaned):
        return jsonify(error="Unknown category in interests"), 400
    user.interests = ",".join(cleaned)
    db.session.commit()
    return jsonify(user=user.to_dict()), 200


@auth_bp.put("/me/school")
@jwt_required()
def update_school():
    user = User.query.get_or_404(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    school = (data.get("school") or "").strip().lower() or None
    if school and school not in SCHOOLS:
        return jsonify(error="Unknown school"), 400
    user.school = school
    db.session.commit()
    return jsonify(user=user.to_dict()), 200


@auth_bp.get("/schools")
def list_schools():
    return jsonify(schools=[{"code": c, "name": n} for c, n in SCHOOLS.items()]), 200
