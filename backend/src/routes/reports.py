from datetime import UTC, date, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from src.services import alpha_vantage

reports_bp = Blueprint("reports_bp", __name__)

# time_period -> (days covered, bar interval). Daily data on the free tier only
# covers ~100 trading days, so longer periods use weekly bars.
PERIODS = {
    "1week": (7, "daily"),
    "1month": (30, "daily"),
    "3months": (91, "daily"),
    "6months": (182, "weekly"),
    "1year": (365, "weekly"),
    "5years": (1826, "weekly"),
}
FIELDS = ("price", "volume", "change")
# Each symbol costs one Alpha Vantage request (the free tier allows 25 a day)
MAX_SYMBOLS = 5


def summarize(bars, days, fields):
    """Reduce newest-first OHLCV bars to the requested metrics over the trailing `days`."""
    cutoff = (date.fromisoformat(bars[0]["date"]) - timedelta(days=days)).isoformat()
    window = [bar for bar in bars if bar["date"] >= cutoff]
    latest = window[0]
    summary = {"from": window[-1]["date"], "to": latest["date"]}

    if "price" in fields:
        summary["latest_close"] = latest["close"]
        summary["period_high"] = max(bar["high"] for bar in window)
        summary["period_low"] = min(bar["low"] for bar in window)
    if "volume" in fields:
        summary["average_volume"] = round(sum(bar["volume"] for bar in window) / len(window))
    if "change" in fields:
        # Measure from the last close before the window when we have it
        start_close = bars[len(window)]["close"] if len(bars) > len(window) else window[-1]["close"]
        change = latest["close"] - start_close
        summary["change"] = round(change, 4)
        summary["change_percent"] = round(change / start_close * 100, 2)
    return summary


@reports_bp.route("/build", methods=["POST"])
@jwt_required()
def build_report():
    data = request.get_json() or {}
    symbols = list(dict.fromkeys(s.strip().upper() for s in data.get("stock_symbols") or [] if s.strip()))
    fields = [f for f in FIELDS if f in (data.get("data_fields") or [])]
    time_period = data.get("time_period")

    if not symbols or not fields or time_period not in PERIODS:
        return jsonify(
            {
                "message": "Provide stock_symbols, data_fields "
                f"({', '.join(FIELDS)}) and a time_period ({', '.join(PERIODS)})"
            }
        ), 400
    if len(symbols) > MAX_SYMBOLS:
        return jsonify({"message": f"A report can include at most {MAX_SYMBOLS} stocks"}), 400

    days, interval = PERIODS[time_period]
    results = []
    for symbol in symbols:
        bars = alpha_vantage.get_time_series(symbol, interval)
        if bars:
            results.append({"symbol": symbol, **summarize(bars, days, fields)})
        else:
            results.append({"symbol": symbol, "error": "No data available"})

    return jsonify(
        {
            "time_period": time_period,
            "interval": interval,
            "data_fields": fields,
            "generated_at": datetime.now(UTC).isoformat(),
            "results": results,
        }
    ), 200
