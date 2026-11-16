def check(client, **body):
    r = client.post("/api/diagnoses", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    h = client.get("/health").json()
    assert h["status"] == "healthy" and h["mixture_model"] is True


def test_meta_has_everything_the_frontend_needs(client):
    m = client.get("/api/meta").json()
    assert m["symptom_groups"] and m["service_items"] and m["faults"] and m["ml"]["ready"]
    assert m["limits"] == {"co_percent": 4.0, "hc_ppm": 6000.0}


def test_nothing_entered_means_ok(client):
    r = check(client)["result"]
    assert r["overall"] == "ok" and r["faults"] == [] and r["emission"] is None


def test_black_smoke_points_to_rich_side(client):
    r = check(client, symptoms=["black_smoke", "high_fuel", "fuel_smell"])["result"]
    assert {f["id"] for f in r["faults"][:2]} == {"rich_mixture", "air_filter"}


def test_blue_smoke_is_oil_burning_and_urgent(client):
    d = check(client, symptoms=["blue_smoke"])
    assert d["result"]["faults"][0]["id"] == "oil_burning" and d["overall"] == "fix_now"


def test_weak_starter_is_battery(client):
    assert check(client, symptoms=["weak_starter"])["result"]["faults"][0]["id"] == "battery"


def test_overdue_oil_is_flagged_without_symptoms(client):
    r = check(client, service={"oil": 5000})["result"]
    assert r["service"]["oil"] == "overdue" and r["faults"][0]["id"] == "old_oil"


def test_same_input_gives_same_result(client):
    body = dict(symptoms=["misfire", "hard_start"], emission={"co_percent": 1.2, "hc_ppm": 160})
    assert check(client, **body)["result"] == check(client, **body)["result"]


def test_emission_over_limit_fails(client):
    d = check(client, emission={"co_percent": 5.5, "hc_ppm": 300})
    assert d["result"]["emission"]["co"]["pass"] is False and d["overall"] == "fix_now"


def test_ml_refuses_out_of_range_reading(client):
    ml = check(client, emission={"co_percent": 2.0, "hc_ppm": 3000})["result"]["emission"]["ml"]
    assert ml["status"] == "out_of_range" and ml["outside"] == ["HC"]


def test_ml_alone_never_raises_a_fault(client):
    r = check(client, emission={"co_percent": 1.1, "hc_ppm": 170})["result"]
    assert r["emission"]["pass"] and r["faults"] == [] and r["overall"] == "ok"


def test_limit_check_wins_over_ml(client):
    d = check(client, emission={"co_percent": 4.6, "hc_ppm": 420})
    assert d["result"]["emission"]["ml"]["status"] == "conflict" and d["overall"] == "fix_now"


def test_bad_input_is_rejected(client):
    assert client.post("/api/diagnoses", json={"symptoms": ["nope"]}).status_code == 422
    assert client.post("/api/diagnoses", json={"emission": {"co_percent": 2}}).status_code == 422
    assert client.post("/api/diagnoses", json={"bike": {"mileage_km": -5}}).status_code == 422
