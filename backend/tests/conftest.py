from datetime import date, timedelta

import pytest

from src import create_app
from src.services import alpha_vantage

TEST_CONFIG = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite://",  # fresh in-memory database per app
    "SECRET_KEY": "test-secret-key-that-is-long-enough-123",
    "JWT_SECRET_KEY": "test-jwt-secret-key-that-is-long-enough",
    "ALPHAVANTAGE_API_KEY": "test-key",
    "ALPHAVANTAGE_MIN_INTERVAL": 0,
}


@pytest.fixture
def app():
    return create_app(TEST_CONFIG)


@pytest.fixture
def client(app):
    return app.test_client()


def signup(client, username="alice", email="alice@example.com", password="correct-horse"):
    return client.post(
        "/api/v1/auth/signup",
        json={"username": username, "email": email, "password": password},
    )


def login(client, email="alice@example.com", password="correct-horse"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tokens(client):
    """Sign up and log in a default user; returns the login response body."""
    signup(client)
    return login(client).get_json()


@pytest.fixture
def auth_headers(tokens):
    return bearer(tokens["access_token"])


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class FakeAlphaVantage:
    """Stands in for the HTTP API: payloads are keyed by the `function` parameter."""

    def __init__(self):
        self.payloads = {}
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append(params)
        return FakeResponse(self.payloads.get(params["function"], {}))


@pytest.fixture
def fake_av(monkeypatch):
    fake = FakeAlphaVantage()
    monkeypatch.setattr(alpha_vantage.requests, "get", fake.get)
    return fake


def bars(closes, key="Time Series (Daily)", start=date(2025, 5, 30), step_days=1):
    """Alpha Vantage time-series payload; closes are newest first."""
    series = {}
    for i, close in enumerate(closes):
        day = (start - timedelta(days=i * step_days)).isoformat()
        series[day] = {
            "1. open": str(close),
            "2. high": str(close + 1),
            "3. low": str(close - 1),
            "4. close": str(close),
            "5. volume": str(1000 * (i + 1)),
        }
    return {key: series}
