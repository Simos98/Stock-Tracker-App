from tests.conftest import bearer, login, signup


def test_signup_then_login_returns_tokens(client):
    assert signup(client).status_code == 201

    response = login(client)

    assert response.status_code == 200
    body = response.get_json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_signup_rejects_duplicate_email(client):
    signup(client)

    response = signup(client, username="someone-else")

    assert response.status_code == 409


def test_login_rejects_wrong_password(client):
    signup(client)

    assert login(client, password="wrong").status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/v1/users/me").status_code == 401


def test_me_returns_profile_without_password_hash(client, auth_headers):
    body = client.get("/api/v1/users/me", headers=auth_headers).get_json()

    assert body["email"] == "alice@example.com"
    assert "password_hash" not in body


def test_logout_revokes_access_token(client, tokens, auth_headers):
    assert client.post("/api/v1/auth/logout", headers=auth_headers).status_code == 200

    assert client.get("/api/v1/users/me", headers=auth_headers).status_code == 401


def test_logout_revokes_refresh_token(client, tokens):
    refresh_headers = bearer(tokens["refresh_token"])
    assert client.post("/api/v1/auth/logout", headers=refresh_headers).status_code == 200

    assert client.post("/api/v1/auth/refresh", headers=refresh_headers).status_code == 401


def test_refresh_issues_new_access_token(client, tokens):
    response = client.post("/api/v1/auth/refresh", headers=bearer(tokens["refresh_token"]))

    assert response.status_code == 200
    assert response.get_json()["access_token"]
