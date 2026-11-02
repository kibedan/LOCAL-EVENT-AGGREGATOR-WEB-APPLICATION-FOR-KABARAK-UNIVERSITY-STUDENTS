from flask import Blueprint, request, jsonify

from app import db
from app.models import Category
from app.utils.decorators import roles_required

categories_bp = Blueprint("categories", __name__)


@categories_bp.get("")
def list_categories():
    cats = Category.query.order_by(Category.name).all()
    return jsonify(categories=[c.to_dict() for c in cats]), 200


@categories_bp.post("")
@roles_required("admin")
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(error="name is required"), 400
    if Category.query.filter_by(name=name).first():
        return jsonify(error="Category already exists"), 409
    cat = Category(name=name)
    db.session.add(cat)
    db.session.commit()
    return jsonify(category=cat.to_dict()), 201


@categories_bp.delete("/<int:category_id>")
@roles_required("admin")
def delete_category(category_id):
    cat = Category.query.get_or_404(category_id)
    if cat.events:
        return jsonify(error="Cannot delete a category with existing events"), 409
    db.session.delete(cat)
    db.session.commit()
    return jsonify(message="Deleted"), 200
