from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Notification

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("")
@jwt_required()
def list_notifications():
    user_id = get_jwt_identity()
    notes = (Notification.query.filter_by(user_id=user_id)
             .order_by(Notification.created_at.desc()).limit(50).all())
    return jsonify(notifications=[n.to_dict() for n in notes]), 200


@notifications_bp.post("/<int:note_id>/read")
@jwt_required()
def mark_read(note_id):
    user_id = get_jwt_identity()
    note = Notification.query.get_or_404(note_id)
    if str(note.user_id) != str(user_id):
        return jsonify(error="Forbidden"), 403
    note.is_read = True
    db.session.commit()
    return jsonify(notification=note.to_dict()), 200
