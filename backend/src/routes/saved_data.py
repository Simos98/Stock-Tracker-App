from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, jwt_required

from src.models import SavedStockData, Stock, db

saved_data_bp = Blueprint("saved_data_bp", __name__)


@saved_data_bp.route("", methods=["POST"])
@jwt_required()
def save_stock_data_point():
    data = request.get_json() or {}

    stock_symbol = data.get("stock_symbol")
    data_point_name = data.get("data_point_name")
    data_value = data.get("data_value")

    # data_value may legitimately be falsy (0, "", false), so only None counts as missing
    if not all([stock_symbol, data_point_name, data_value is not None]):
        return jsonify({"message": "Missing required fields: stock_symbol, data_point_name, data_value"}), 400

    stock = Stock.query.filter_by(symbol=stock_symbol.upper()).first()
    if not stock:
        return jsonify({"message": f"Stock with symbol {stock_symbol.upper()} not found"}), 404

    new_saved_data = SavedStockData(
        user_id=current_user.id, stock_id=stock.id, data_point_name=data_point_name, data_value=str(data_value)
    )
    db.session.add(new_saved_data)
    db.session.commit()

    return jsonify({"message": "Data saved successfully", "saved_data": new_saved_data.to_dict()}), 201


@saved_data_bp.route("", methods=["GET"])
@jwt_required()
def get_saved_stock_data():
    stock_symbol_filter = request.args.get("stock_symbol")

    query = SavedStockData.query.filter_by(user_id=current_user.id)

    if stock_symbol_filter:
        stock = Stock.query.filter_by(symbol=stock_symbol_filter.upper()).first()
        if stock:
            query = query.filter_by(stock_id=stock.id)
        else:
            return jsonify([]), 200

    saved_data_items = query.all()
    return jsonify([item.to_dict() for item in saved_data_items]), 200


@saved_data_bp.route("/<int:saved_data_id>", methods=["DELETE"])
@jwt_required()
def delete_saved_stock_data(saved_data_id):
    # Scoping by user means other users' items look like they don't exist
    saved_item = SavedStockData.query.filter_by(id=saved_data_id, user_id=current_user.id).first()
    if not saved_item:
        return jsonify({"message": "Saved data point not found or you do not have permission to delete it"}), 404

    db.session.delete(saved_item)
    db.session.commit()

    return jsonify({"message": "Saved data deleted successfully"}), 200
