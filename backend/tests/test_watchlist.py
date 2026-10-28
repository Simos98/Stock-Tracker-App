import pytest

from src.extensions import db
from src.models import Stock


@pytest.fixture
def bhp(app):
    with app.app_context():
        db.session.add(Stock(symbol="BHP.AX", name="BHP Group Limited", exchange="ASX"))
        db.session.commit()


@pytest.mark.parametrize("path", ["/api/v1/watchlist", "/api/v1/preferences", "/api/v1/saved-data"])
def test_collection_routes_answer_without_trailing_slash(client, auth_headers, path):
    assert client.get(path, headers=auth_headers).status_code == 200


def test_cors_preflight_is_not_redirected(client):
    response = client.options(
        "/api/v1/watchlist",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"


def test_add_list_and_remove_watchlist_item(client, auth_headers, bhp):
    added = client.post("/api/v1/watchlist", json={"stock_symbol": "bhp.ax"}, headers=auth_headers)
    assert added.status_code == 201

    items = client.get("/api/v1/watchlist", headers=auth_headers).get_json()
    assert [(item["symbol"], item["name"]) for item in items] == [("BHP.AX", "BHP Group Limited")]

    assert client.delete("/api/v1/watchlist/BHP.AX", headers=auth_headers).status_code == 200
    assert client.get("/api/v1/watchlist", headers=auth_headers).get_json() == []


def test_watchlist_rejects_duplicates_and_unknown_stocks(client, auth_headers, bhp):
    client.post("/api/v1/watchlist", json={"stock_symbol": "BHP.AX"}, headers=auth_headers)

    duplicate = client.post("/api/v1/watchlist", json={"stock_symbol": "BHP.AX"}, headers=auth_headers)
    unknown = client.post("/api/v1/watchlist", json={"stock_symbol": "NOPE.AX"}, headers=auth_headers)

    assert duplicate.status_code == 409
    assert unknown.status_code == 404
