import pytest

from tests.conftest import bearer, login, signup


def change_password(client, headers, current, new):
    return client.put(
        "/api/v1/users/me",
        json={"current_password": current, "new_password": new},
        headers=headers,
    )


def test_password_change_takes_effect(client, auth_headers):
    response = change_password(client, auth_headers, "correct-horse", "battery-staple")

    assert response.status_code == 200
    assert login(client, password="correct-horse").status_code == 401
    assert login(client, password="battery-staple").status_code == 200


def test_password_change_requires_current_password(client, auth_headers):
    response = change_password(client, auth_headers, "wrong-guess", "battery-staple")

    assert response.status_code == 403
    assert login(client, password="correct-horse").status_code == 200


def test_password_change_enforces_minimum_length(client, auth_headers):
    assert change_password(client, auth_headers, "correct-horse", "short").status_code == 400


def test_signup_enforces_minimum_password_length(client):
    assert signup(client, password="short").status_code == 400


def test_update_profile_returns_updated_user(client, auth_headers):
    response = client.put("/api/v1/users/me", json={"username": "alice2"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()["user"]["username"] == "alice2"


@pytest.mark.parametrize(
    "method, path",
    [
        ("GET", "/api/v1/users/users_all"),
        ("GET", "/api/v1/users/users/1"),
        ("PUT", "/api/v1/users/users/1"),
        ("DELETE", "/api/v1/users/users/1"),
    ],
)
def test_user_admin_routes_are_not_exposed(client, method, path):
    """Any logged-in user could previously list, edit or delete every account."""
    signup(client)
    signup(client, username="mallory", email="mallory@example.com")
    mallory = login(client, email="mallory@example.com").get_json()

    response = client.open(path, method=method, json={}, headers=bearer(mallory["access_token"]))

    assert response.status_code in (404, 405)  # 405: only the GET-only SPA catch-all matches
