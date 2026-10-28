import pytest

from src.extensions import db
from src.models import Stock
from tests.conftest import bearer, login, signup


@pytest.fixture(autouse=True)
def bhp(app):
    with app.app_context():
        db.session.add(Stock(symbol="BHP.AX", name="BHP Group Limited", exchange="ASX"))
        db.session.commit()


def save_note(client, headers, value="Watch the iron ore price"):
    return client.post(
        "/api/v1/saved-data",
        json={"stock_symbol": "BHP.AX", "data_point_name": "note", "data_value": value},
        headers=headers,
    )


def test_save_and_filter_by_symbol(client, auth_headers):
    assert save_note(client, auth_headers).status_code == 201

    items = client.get("/api/v1/saved-data?stock_symbol=bhp.ax", headers=auth_headers).get_json()

    assert [item["data_value"] for item in items] == ["Watch the iron ore price"]


def test_falsy_values_can_be_saved(client, auth_headers):
    assert save_note(client, auth_headers, value=0).status_code == 201


def test_users_cannot_see_or_delete_each_others_data(client, auth_headers):
    item_id = save_note(client, auth_headers).get_json()["saved_data"]["id"]
    signup(client, username="mallory", email="mallory@example.com")
    mallory = bearer(login(client, email="mallory@example.com").get_json()["access_token"])

    assert client.get("/api/v1/saved-data", headers=mallory).get_json() == []
    assert client.delete(f"/api/v1/saved-data/{item_id}", headers=mallory).status_code == 404
    assert client.delete(f"/api/v1/saved-data/{item_id}", headers=auth_headers).status_code == 200
