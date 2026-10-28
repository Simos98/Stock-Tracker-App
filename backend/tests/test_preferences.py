def test_defaults_are_created_on_first_read(client, auth_headers):
    body = client.get("/api/v1/preferences", headers=auth_headers).get_json()

    assert body["notification_frequency"] == "daily"
    assert body["notification_type_email"] is True


def test_update_persists_known_fields(client, auth_headers):
    response = client.put(
        "/api/v1/preferences",
        json={"notification_frequency": "realtime_critical", "notification_type_email": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    saved = client.get("/api/v1/preferences", headers=auth_headers).get_json()
    assert saved["notification_frequency"] == "realtime_critical"
    assert saved["notification_type_email"] is False


def test_update_rejects_invalid_values(client, auth_headers):
    bad_frequency = client.put("/api/v1/preferences", json={"notification_frequency": "realtime"}, headers=auth_headers)
    bad_flag = client.put("/api/v1/preferences", json={"notification_type_inapp": "yes"}, headers=auth_headers)

    assert bad_frequency.status_code == 400
    assert bad_flag.status_code == 400
