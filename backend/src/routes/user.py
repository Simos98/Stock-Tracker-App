from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, jwt_required

from src.models import MIN_PASSWORD_LENGTH, User, db

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    return jsonify(current_user.to_dict()), 200


@user_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_current_user():
    data = request.get_json() or {}

    new_password = data.get("new_password")
    if new_password:
        # Changing the password requires proving you know the current one
        if not current_user.check_password(data.get("current_password") or ""):
            return jsonify({"message": "Current password is incorrect"}), 403
        if len(new_password) < MIN_PASSWORD_LENGTH:
            return jsonify({"message": f"Password must be at least {MIN_PASSWORD_LENGTH} characters"}), 400

    if "username" in data:
        if User.query.filter(User.username == data["username"], User.id != current_user.id).first():
            return jsonify({"message": "Username already taken"}), 409
        current_user.username = data["username"]

    if "email" in data:
        if User.query.filter(User.email == data["email"], User.id != current_user.id).first():
            return jsonify({"message": "Email already taken"}), 409
        current_user.email = data["email"]

    if new_password:
        current_user.set_password(new_password)

    db.session.commit()
    return jsonify({"message": "User updated successfully", "user": current_user.to_dict()}), 200
