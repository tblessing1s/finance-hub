from app.models import Bucket


def test_list_empty(client):
    assert client.get("/api/buckets").json() == []


def test_create_roundtrips_money_as_decimal(client, db):
    r = client.post(
        "/api/buckets",
        json={"name": "WF Checking", "kind": "checking", "floor": "7500.00", "target": None},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["floor"] == "7500.00"
    assert body["target"] is None
    assert body["balance_source"] == "manual"
    row = db.get(Bucket, body["id"])
    assert row.floor_cents == 750_000


def test_create_rejects_unknown_kind(client):
    r = client.post("/api/buckets", json={"name": "x", "kind": "mattress"})
    assert r.status_code == 422


def test_create_rejects_three_decimal_places(client):
    r = client.post("/api/buckets", json={"name": "x", "kind": "hub", "floor": "1.005"})
    assert r.status_code == 422


def test_duplicate_name_is_409(client):
    payload = {"name": "Hub", "kind": "hub"}
    assert client.post("/api/buckets", json=payload).status_code == 201
    r = client.post("/api/buckets", json=payload)
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"]


def test_get_and_404(client, buckets):
    hub = buckets["hub"]
    assert client.get(f"/api/buckets/{hub.id}").json()["name"] == "Schwab Hub"
    assert client.get("/api/buckets/999999").status_code == 404


def test_list_sorted_by_name(client, buckets):
    names = [b["name"] for b in client.get("/api/buckets").json()]
    assert names == sorted(names)
    assert len(names) == 5


def test_patch_partial_and_clear(client, buckets):
    checking = buckets["checking"]
    r = client.patch(f"/api/buckets/{checking.id}", json={"target": "10000"})
    assert r.status_code == 200
    assert r.json()["floor"] == "7500.00"  # untouched
    assert r.json()["target"] == "10000.00"
    r = client.patch(f"/api/buckets/{checking.id}", json={"floor": None})
    assert r.json()["floor"] is None


def test_patch_cannot_null_required(client, buckets):
    r = client.patch(f"/api/buckets/{buckets['hub'].id}", json={"name": None})
    assert r.status_code == 422


def test_delete_unreferenced(client, buckets):
    r = client.delete(f"/api/buckets/{buckets['reserve'].id}")
    assert r.status_code == 204
    assert client.get(f"/api/buckets/{buckets['reserve'].id}").status_code == 404


def test_delete_referenced_by_flow_is_409(client, plan):
    r = client.delete(f"/api/buckets/{plan['checking'].id}")
    assert r.status_code == 409
    assert "planned flow" in r.json()["detail"]
