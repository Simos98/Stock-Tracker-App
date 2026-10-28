from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, jwt_required

from src.models import NOTIFICATION_FREQUENCIES, UserPreference, db

preferences_bp = Blueprint("preferences_bp", __name__)

BOOLEAN_FIELDS = ("notification_type_email", "notification_type_inapp")


def _preferences_for(user):
    """Users get default preferences the first time they are read."""
    if not user.preferences:
        user.preferences = UserPreference(user_id=user.id)
        db.session.commit()
    return user.preferences


@preferences_bp.route("", methods=["GET"])
@jwt_required()
def get_preferences():
    return jsonify(_preferences_for(current_user).to_dict()), 200


@preferences_bp.route("", methods=["PUT"])
@jwt_required()
def update_preferences():
    data = request.get_json() or {}

    if "notification_frequency" in data and data["notification_frequency"] not in NOTIFICATION_FREQUENCIES:
        return jsonify({"message": f"notification_frequency must be one of {', '.join(NOTIFICATION_FREQUENCIES)}"}), 400
    for field in BOOLEAN_FIELDS:
        if field in data and not isinstance(data[field], bool):
            return jsonify({"message": f"{field} must be true or false"}), 400
    if "report_fields" in data and not isinstance(data["report_fields"], list):
        return jsonify({"message": "report_fields must be a list"}), 400

    prefs = _preferences_for(current_user)
    for field in ("notification_frequency", *BOOLEAN_FIELDS, "report_fields"):
        if field in data:
            setattr(prefs, field, data[field])

    db.session.commit()
    return jsonify({"message": "Preferences updated successfully", "preferences": prefs.to_dict()}), 200
