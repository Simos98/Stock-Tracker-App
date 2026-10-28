from src.routes.reports import summarize
from tests.conftest import bars


def build(client, headers, **overrides):
    payload = {"stock_symbols": ["BHP.AX"], "data_fields": ["price", "volume", "change"], "time_period": "1week"}
    payload.update(overrides)
    return client.post("/api/v1/reports/build", json=payload, headers=headers)


def test_summarize_covers_only_the_requested_window():
    # Ten daily bars, newest first: closes 20, 19, ... 11
    series = [
        {"date": f"2025-05-{30 - i:02d}", "open": 0, "high": 21 - i, "low": 19 - i, "close": 20 - i, "volume": 100}
        for i in range(10)
    ]

    summary = summarize(series, days=3, fields=["price", "volume", "change"])

    assert (summary["from"], summary["to"]) == ("2025-05-27", "2025-05-30")
    assert summary["latest_close"] == 20
    assert summary["period_high"] == 21
    assert summary["period_low"] == 16
    assert summary["average_volume"] == 100
    # Change is measured from the close just before the window (2025-05-26: 16)
    assert summary["change"] == 4
    assert summary["change_percent"] == 25.0


def test_build_report_returns_real_metrics(client, auth_headers, fake_av):
    fake_av.payloads["TIME_SERIES_DAILY"] = bars([110.0, 105.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0])

    response = build(client, auth_headers)

    assert response.status_code == 200
    result = response.get_json()["results"][0]
    assert result["symbol"] == "BHP.AX"
    assert result["latest_close"] == 110.0
    assert result["change_percent"] == 10.0


def test_long_periods_use_weekly_bars(client, auth_headers, fake_av):
    fake_av.payloads["TIME_SERIES_WEEKLY"] = bars([2.0, 1.0], key="Weekly Time Series", step_days=7)

    body = build(client, auth_headers, time_period="1year").get_json()

    assert body["interval"] == "weekly"
    assert fake_av.calls[0]["function"] == "TIME_SERIES_WEEKLY"


def test_symbols_without_data_are_reported_per_symbol(client, auth_headers, fake_av):
    body = build(client, auth_headers, stock_symbols=["NOPE.AX"]).get_json()

    assert body["results"] == [{"symbol": "NOPE.AX", "error": "No data available"}]


def test_build_report_validates_input(client, auth_headers, fake_av):
    assert build(client, auth_headers, time_period="forever").status_code == 400
    assert build(client, auth_headers, data_fields=[]).status_code == 400
    assert build(client, auth_headers, stock_symbols=[f"S{i}.AX" for i in range(6)]).status_code == 400
    assert fake_av.calls == []


def test_build_report_requires_login(client):
    assert client.post("/api/v1/reports/build", json={}).status_code == 401
