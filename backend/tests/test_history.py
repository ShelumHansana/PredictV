def make(client, **body):
    r = client.post("/api/diagnoses", json=body)
    assert r.status_code == 201
    return r.json()


def test_check_is_saved_and_listed(client):
    d = make(client, bike={"name": "  CT 100 ", "mileage_km": 42000}, symptoms=["weak_starter"])
    assert d["bike_name"] == "CT 100"
    rows = client.get("/api/diagnoses").json()
    assert rows[0]["id"] == d["id"] and rows[0]["top_fault"] == "battery" and rows[0]["has_feedback"] is False
    assert client.get(f"/api/diagnoses/{d['id']}").json()["answers"]["bike"]["mileage_km"] == 42000


def test_another_browser_cannot_see_change_or_delete_it(client, other_client):
    d = make(client, symptoms=["tapping"])
    url = f"/api/diagnoses/{d['id']}"
    assert other_client.get(url).status_code == 404
    assert other_client.delete(url).status_code == 404
    assert other_client.put(url + "/feedback", json={"confirmed_fault": "old_oil"}).status_code == 404
    assert other_client.get("/api/diagnoses").json() == []
    assert client.get(url).status_code == 200


def test_feedback_can_be_saved_and_changed(client):
    d = make(client, symptoms=["tapping"])
    url = f"/api/diagnoses/{d['id']}/feedback"
    assert client.put(url, json={"confirmed_fault": "valve_clearance", "note": " set to spec "}).json()["feedback"]["note"] == "set to spec"
    assert client.put(url, json={"confirmed_fault": "none"}).json()["feedback"] == {
        "confirmed_fault": "none", "note": None, "created_at": client.get(f"/api/diagnoses/{d['id']}").json()["feedback"]["created_at"]}
    assert client.put(url, json={"confirmed_fault": "made_up"}).status_code == 422
    assert client.get("/api/diagnoses").json()[0]["has_feedback"] is True


def test_delete(client):
    d = make(client, symptoms=["tapping"])
    client.put(f"/api/diagnoses/{d['id']}/feedback", json={"confirmed_fault": "old_oil"})
    assert client.delete(f"/api/diagnoses/{d['id']}").status_code == 204
    assert client.get(f"/api/diagnoses/{d['id']}").status_code == 404


def test_unknown_id_is_404(client):
    assert client.get("/api/diagnoses/not-a-real-id").status_code == 404
