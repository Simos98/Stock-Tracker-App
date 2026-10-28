from flask import Blueprint, jsonify, request

from src.models import Stock, db
from src.services import alpha_vantage

stock_bp = Blueprint("stock_bp", __name__)


def _exchange_for(symbol, region):
    return "ASX" if symbol.endswith(".AX") else region


def _remember(match):
    """Cache a symbol-search match in the stocks table so later searches stay local."""
    stock = Stock.query.filter_by(symbol=match["symbol"]).first()
    if not stock:
        stock = Stock(
            symbol=match["symbol"],
            name=match["name"],
            exchange=_exchange_for(match["symbol"], match["region"]),
        )
        db.session.add(stock)
    return stock


@stock_bp.route("", methods=["GET"])
def list_or_search_stocks():
    search_term = request.args.get("search_term")
    exchange = request.args.get("exchange")
    limit = request.args.get("limit", default=20, type=int)
    offset = request.args.get("offset", default=0, type=int)

    query = Stock.query
    if search_term:
        query = query.filter(Stock.name.ilike(f"%{search_term}%") | Stock.symbol.ilike(f"%{search_term}%"))
    if exchange:
        query = query.filter(Stock.exchange.ilike(f"%{exchange}%"))
    stocks_page = query.offset(offset).limit(limit).all()

    if stocks_page or not search_term:
        return jsonify(
            {
                "total": query.count(),
                "limit": limit,
                "offset": offset,
                "data": [stock.to_dict() for stock in stocks_page],
            }
        ), 200

    # Nothing cached locally: ask Alpha Vantage and remember what it finds
    matches = alpha_vantage.search_symbols(search_term)
    if exchange and exchange.upper() in ("ASX", "AU"):
        matches = [m for m in matches if m["region"] == "Australia" or m["symbol"].endswith(".AX")]
    for match in matches:
        _remember(match)
    db.session.commit()

    return jsonify(
        {
            "total": len(matches),
            "limit": limit,
            "offset": 0,
            "data": [
                {
                    "symbol": m["symbol"],
                    "name": m["name"],
                    "exchange": _exchange_for(m["symbol"], m["region"]),
                    "currency": m["currency"],
                }
                for m in matches[:limit]
            ],
        }
    ), 200


@stock_bp.route("/<string:stock_symbol>", methods=["GET"])
def get_stock_details(stock_symbol):
    symbol = stock_symbol.upper()
    stock = Stock.query.filter_by(symbol=symbol).first()

    if not stock:
        match = next((m for m in alpha_vantage.search_symbols(symbol) if m["symbol"].upper() == symbol), None)
        if not match:
            return jsonify({"message": "Stock symbol not found"}), 404
        stock = _remember(match)
        db.session.commit()

    quote = alpha_vantage.get_quote(stock.symbol)
    if quote is None:
        return jsonify({"message": f"No data available for {symbol}"}), 404

    return jsonify({**stock.to_dict(), **quote}), 200


@stock_bp.route("/<string:stock_symbol>/historical", methods=["GET"])
def get_stock_historical_data(stock_symbol):
    interval = request.args.get("interval", default="daily")  # daily, weekly, monthly
    output_size = request.args.get("output_size", default="compact")  # compact (~100 points) or full

    bars = alpha_vantage.get_time_series(stock_symbol.upper(), interval, output_size)
    if not bars:
        return jsonify({"message": f"No historical data available for {stock_symbol}"}), 404

    return jsonify(bars), 200
