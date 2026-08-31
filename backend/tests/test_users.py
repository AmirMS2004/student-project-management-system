def test_list_professors_returns_only_professors(
    client, professor, student, register_user
):
    register_user(
        role="professor", email="another-prof@test.com", phone_number="09300000007"
    )
    r = client.get("/api/users/professors", headers=student["headers"])
    assert r.status_code == 200
    roles = {p["role"] for p in r.json()}
    assert roles == {"professor"}
    assert len(r.json()) == 2


def test_list_professors_requires_authentication(client):
    r = client.get("/api/users/professors")
    assert r.status_code == 401
