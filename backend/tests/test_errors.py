def test_wrong_method_returns_json_405(client):
    response = client.delete("/api/v1/auth/login")

    assert response.status_code == 405
    assert "message" in response.get_json()


def test_unknown_api_path_returns_json_404(client):
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert "message" in response.get_json()
