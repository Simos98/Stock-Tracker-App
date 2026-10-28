from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, jwt_required

from src.models import Stock, UserWatchlist, db

watchlist_bp = Blueprint("watchlist_bp", __name__)


@watchlist_bp.route("", methods=["GET"])
@jwt_required()
def get_watchlist():
    watchlist_items = UserWatchlist.query.filter_by(user_id=current_user.id).all()
    return jsonify([item.to_dict() for item in watchlist_items]), 200


@watchlist_bp.route("", methods=["POST"])
@jwt_required()
def add_to_watchlist():
    data = request.get_json() or {}
    stock_symbol = data.get("stock_symbol")
    if not stock_symbol:
        return jsonify({"message": "Stock symbol is required"}), 400

    stock = Stock.query.filter_by(symbol=stock_symbol.upper()).first()
    if not stock:
        return jsonify({"message": f"Stock with symbol {stock_symbol.upper()} not found"}), 404
    existing_item = UserWatchlist.query.filter_by(user_id=current_user.id, stock_id=stock.id).first()
    if existing_item:
        return jsonify({"message": "Stock already in watchlist"}), 409

    new_watchlist_item = UserWatchlist(user_id=current_user.id, stock_id=stock.id)
    db.session.add(new_watchlist_item)
    db.session.commit()

    return jsonify({"message": "Stock added to watchlist", "watchlist_item": new_watchlist_item.to_dict()}), 201


@watchlist_bp.route("/<string:stock_symbol>", methods=["DELETE"])
@jwt_required()
def remove_from_watchlist(stock_symbol):
    stock = Stock.query.filter_by(symbol=stock_symbol.upper()).first()

    if not stock:
        return jsonify({"message": f"Stock with symbol {stock_symbol.upper()} not found"}), 404

    watchlist_item = UserWatchlist.query.filter_by(user_id=current_user.id, stock_id=stock.id).first()
    if not watchlist_item:
        return jsonify({"message": "Stock not found in watchlist"}), 404

    db.session.delete(watchlist_item)
    db.session.commit()

    return jsonify({"message": "Stock removed from watchlist"}), 200
