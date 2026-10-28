"""Thin client for the Alpha Vantage market-data API.

Alpha Vantage reports most failures (rate limits, bad keys, unknown symbols) as
HTTP 200 with an explanatory field in the JSON body, so every call goes through
`_query`, which turns those into exceptions the app maps to clean API errors.

The free tier allows 25 requests a day and about one per second, so `_query`
also caches responses for a few minutes and spaces out calls that do go out.
"""

import threading
import time

import requests
from flask import current_app

API_URL = "https://www.alphavantage.co/query"
TIMEOUT_SECONDS = 10

# interval -> (API function, key holding the bars in the response)
TIME_SERIES = {
    "daily": ("TIME_SERIES_DAILY", "Time Series (Daily)"),
    "weekly": ("TIME_SERIES_WEEKLY", "Weekly Time Series"),
    "monthly": ("TIME_SERIES_MONTHLY", "Monthly Time Series"),
}


class AlphaVantageError(Exception):
    """The API could not be reached or returned an unusable response."""


class RateLimitError(AlphaVantageError):
    """The API key has used up its request quota."""


class _ClientState:
    """Per-app response cache and call spacing (kept on the app so tests stay isolated)."""

    def __init__(self):
        self.cache = {}  # (function, params) -> (expires_at, data)
        self.lock = threading.Lock()
        self.last_call = 0.0


def _state():
    return current_app.extensions.setdefault("alpha_vantage", _ClientState())


def _query(function, **params):
    api_key = current_app.config.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise AlphaVantageError("ALPHAVANTAGE_API_KEY is not configured")

    state = _state()
    cache_key = (function, tuple(sorted(params.items())))
    cached = state.cache.get(cache_key)
    if cached and cached[0] > time.monotonic():
        return cached[1]

    # One call at a time, at least min_interval apart, so concurrent requests
    # don't trip the per-second limit
    min_interval = current_app.config.get("ALPHAVANTAGE_MIN_INTERVAL", 1.1)
    with state.lock:
        time.sleep(max(0.0, state.last_call + min_interval - time.monotonic()))
        try:
            response = requests.get(
                API_URL,
                params={"function": function, "apikey": api_key, **params},
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            raise AlphaVantageError(f"{function} request failed: {e}") from e
        finally:
            state.last_call = time.monotonic()

    if "Note" in data or "Information" in data:
        raise RateLimitError(data.get("Note") or data.get("Information"))
    if "Error Message" in data:
        # Returned for unknown symbols; callers treat it as "no data"
        data = {}

    ttl = current_app.config.get("ALPHAVANTAGE_CACHE_SECONDS", 300)
    state.cache[cache_key] = (time.monotonic() + ttl, data)
    return data


def search_symbols(keywords):
    """Best matches for a company name or ticker."""
    data = _query("SYMBOL_SEARCH", keywords=keywords)
    return [
        {
            "symbol": match.get("1. symbol"),
            "name": match.get("2. name"),
            "region": match.get("4. region"),
            "currency": match.get("8. currency"),
        }
        for match in data.get("bestMatches", [])
    ]


def get_time_series(symbol, interval="daily", output_size="compact"):
    """OHLCV bars, newest first. Unknown intervals fall back to daily."""
    function, key = TIME_SERIES.get(interval, TIME_SERIES["daily"])
    data = _query(function, symbol=symbol, outputsize=output_size)
    bars = [
        {
            "date": day,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "volume": int(values["5. volume"]),
        }
        for day, values in data.get(key, {}).items()
    ]
    return sorted(bars, key=lambda bar: bar["date"], reverse=True)


def get_quote(symbol):
    """Latest quote, or None if the symbol has no data.

    GLOBAL_QUOTE is often empty for non-US listings on the free tier, so fall
    back to the two most recent daily bars and derive the change from them.
    """
    quote = _query("GLOBAL_QUOTE", symbol=symbol).get("Global Quote")
    if quote:
        return {
            "current_price": float(quote["05. price"]),
            "open_price": float(quote["02. open"]),
            "day_high": float(quote["03. high"]),
            "day_low": float(quote["04. low"]),
            "volume": int(quote["06. volume"]),
            "previous_close": float(quote["08. previous close"]),
            "change": float(quote["09. change"]),
            "change_percent": quote["10. change percent"],
            "last_updated": quote["07. latest trading day"],
        }

    bars = get_time_series(symbol, "daily")
    if not bars:
        return None
    latest = bars[0]
    previous_close = bars[1]["close"] if len(bars) > 1 else None
    change = latest["close"] - previous_close if previous_close else None
    return {
        "current_price": latest["close"],
        "open_price": latest["open"],
        "day_high": latest["high"],
        "day_low": latest["low"],
        "volume": latest["volume"],
        "previous_close": previous_close,
        "change": round(change, 4) if change is not None else None,
        "change_percent": f"{change / previous_close * 100:.4f}%" if change is not None else None,
        "last_updated": latest["date"],
    }
