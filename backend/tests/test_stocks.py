from src.services import alpha_vantage
from tests.conftest import bars

BHP_MATCH = {
    "bestMatches": [
        {"1. symbol": "BHP.AX", "2. name": "BHP Group Limited", "4. region": "Australia", "8. currency": "AUD"},
    ]
}


def test_search_falls_back_to_alpha_vantage_and_caches_results(client, fake_av):
    fake_av.payloads["SYMBOL_SEARCH"] = BHP_MATCH

    first = client.get("/api/v1/stocks?search_term=BHP").get_json()
    second = client.get("/api/v1/stocks?search_term=BHP").get_json()

    assert first["data"][0]["symbol"] == "BHP.AX"
    assert first["data"][0]["exchange"] == "ASX"
    assert second["data"][0]["symbol"] == "BHP.AX"
    assert len(fake_av.calls) == 1  # the second search was served from the database


def test_stock_details_use_global_quote(client, fake_av):
    fake_av.payloads["SYMBOL_SEARCH"] = BHP_MATCH
    fake_av.payloads["GLOBAL_QUOTE"] = {
        "Global Quote": {
            "02. open": "44.00",
            "03. high": "45.10",
            "04. low": "43.90",
            "05. price": "45.00",
            "06. volume": "123456",
            "07. latest trading day": "2025-05-30",
            "08. previous close": "44.50",
            "09. change": "0.50",
            "10. change percent": "1.1236%",
        }
    }

    body = client.get("/api/v1/stocks/bhp.ax").get_json()

    assert body["symbol"] == "BHP.AX"
    assert body["current_price"] == 45.0
    assert body["change_percent"] == "1.1236%"


def test_stock_details_fall_back_to_daily_bars_when_quote_is_empty(client, fake_av):
    fake_av.payloads["SYMBOL_SEARCH"] = BHP_MATCH
    fake_av.payloads["GLOBAL_QUOTE"] = {"Global Quote": {}}
    fake_av.payloads["TIME_SERIES_DAILY"] = bars([50.0, 40.0])

    body = client.get("/api/v1/stocks/BHP.AX").get_json()

    assert body["current_price"] == 50.0
    assert body["previous_close"] == 40.0
    assert body["change"] == 10.0
    assert body["change_percent"] == "25.0000%"


def test_unknown_symbol_returns_404(client, fake_av):
    fake_av.payloads["SYMBOL_SEARCH"] = {"bestMatches": []}

    assert client.get("/api/v1/stocks/NOPE.AX").status_code == 404


def test_weekly_history_reads_the_weekly_series(client, fake_av):
    """Weekly/monthly data lives under 'Weekly Time Series', not 'Time Series (Weekly)'."""
    fake_av.payloads["TIME_SERIES_WEEKLY"] = bars([3.0, 2.0, 1.0], key="Weekly Time Series", step_days=7)

    body = client.get("/api/v1/stocks/BHP.AX/historical?interval=weekly").get_json()

    assert [bar["close"] for bar in body] == [3.0, 2.0, 1.0]


def test_rate_limit_is_reported_as_503(client, fake_av):
    fake_av.payloads["SYMBOL_SEARCH"] = {"Information": "API rate limit reached"}

    response = client.get("/api/v1/stocks?search_term=BHP")

    assert response.status_code == 503
    assert "rate limit" in response.get_json()["message"]


def test_missing_api_key_is_reported_as_502(app, fake_av):
    app.config["ALPHAVANTAGE_API_KEY"] = None

    assert app.test_client().get("/api/v1/stocks/BHP.AX/historical").status_code == 502
    assert fake_av.calls == []


def test_seed_stocks_is_idempotent(app):
    runner = app.test_cli_runner()

    assert "Added 10 stocks" in runner.invoke(args=["seed-stocks"]).output
    assert "Added 0 stocks" in runner.invoke(args=["seed-stocks"]).output


def test_responses_are_cached(client, fake_av):
    fake_av.payloads["TIME_SERIES_DAILY"] = bars([2.0, 1.0])

    client.get("/api/v1/stocks/BHP.AX/historical")
    client.get("/api/v1/stocks/BHP.AX/historical")

    assert len(fake_av.calls) == 1


def test_calls_are_spaced_to_respect_the_per_second_limit(app, fake_av, monkeypatch):
    app.config["ALPHAVANTAGE_MIN_INTERVAL"] = 1.1
    sleeps = []
    monkeypatch.setattr(alpha_vantage.time, "sleep", sleeps.append)
    client = app.test_client()

    client.get("/api/v1/stocks/AAA/historical")
    client.get("/api/v1/stocks/BBB/historical")

    assert sleeps[0] == 0.0  # first call goes straight out
    assert sleeps[1] > 1.0  # second waits out the rest of the interval
