from collections import Counter

import pytest


def test_list_empty(client):
    assert client.get("/api/planned-flows").json() == []


def test_list_includes_bucket_names_and_groups_by_cadence(client, plan):
    rows = client.get("/api/planned-flows").json()
    assert len(rows) == 3
    by_name = {r["name"]: r for r in rows}
    assert by_name["Paycheck"]["from_bucket_name"] is None
    assert by_name["Paycheck"]["to_bucket_name"] == "WF Checking"
    assert by_name["Paycheck"]["amount"] == "3200.00"
    assert by_name["Sweep to hub"]["amount"] is None
    assert by_name["Sweep to hub"]["amount_rule"] == "sweep_above_floor"
    assert by_name["Runway contribution"]["stop_rule"] == "bucket_reaches_target"
    assert by_name["Runway contribution"]["redirect_to_bucket_name"] == "Engine"
    assert Counter(r["cadence"] for r in rows) == {"per_paycheck": 2, "monthly_on_day": 1}


def test_filter_active(client, plan):
    client.patch(f"/api/planned-flows/{plan['sweep'].id}", json={"active": False})
    assert len(client.get("/api/planned-flows", params={"active": "true"}).json()) == 2
    assert len(client.get("/api/planned-flows", params={"active": "false"}).json()) == 1


def test_create_fixed_amount(client, buckets):
    r = client.post(
        "/api/planned-flows",
        json={
            "name": "Ameritas premium",
            "from_bucket_id": buckets["checking"].id,
            "amount": "1250.50",
            "cadence": "monthly_on_day",
            "anchor_date": "2026-10-15",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["amount"] == "1250.50"
    assert body["to_bucket_id"] is None
    assert body["active"] is True
    assert body["from_bucket_name"] == "WF Checking"


def test_create_rule_based(client, buckets):
    r = client.post(
        "/api/planned-flows",
        json={
            "name": "Remainder to engine",
            "from_bucket_id": buckets["hub"].id,
            "to_bucket_id": buckets["engine"].id,
            "amount_rule": "remainder",
            "cadence": "monthly_on_day",
            "anchor_date": "2026-10-30",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["amount"] is None


def test_create_with_date_stop_rule(client, buckets):
    r = client.post(
        "/api/planned-flows",
        json={
            "name": "Roth",
            "from_bucket_id": buckets["hub"].id,
            "amount": "583.33",
            "cadence": "monthly_on_day",
            "anchor_date": "2026-10-01",
            "stop_rule": "date",
            "stop_date": "2027-04-15",
        },
    )
    assert r.status_code == 201, r.text


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"amount": None, "amount_rule": None}, "exactly one of amount"),
        ({"amount": "10", "amount_rule": "remainder"}, "exactly one of amount"),
        ({"amount": "0"}, "positive"),
        ({"from_bucket_id": None, "to_bucket_id": None}, "needs a from_bucket or a to_bucket"),
        ({"stop_rule": "date"}, "needs a stop_date"),
        ({"stop_date": "2027-01-01"}, "only applies when stop_rule"),
        ({"stop_rule": "bucket_reaches_target", "to_bucket_id": None}, "needs a to_bucket"),
        (
            {"amount": None, "amount_rule": "sweep_above_floor", "from_bucket_id": None},
            "needs a from_bucket",
        ),
    ],
)
def test_create_invariants(client, buckets, overrides, message):
    base = {
        "name": "x",
        "from_bucket_id": buckets["checking"].id,
        "to_bucket_id": buckets["hub"].id,
        "amount": "100",
        "cadence": "weekly",
        "anchor_date": "2026-10-05",
    }
    r = client.post("/api/planned-flows", json={**base, **overrides})
    assert r.status_code == 422, r.text
    assert message in r.text


def test_same_bucket_both_ends_rejected(client, buckets):
    r = client.post(
        "/api/planned-flows",
        json={
            "name": "x",
            "from_bucket_id": buckets["hub"].id,
            "to_bucket_id": buckets["hub"].id,
            "amount": "1",
            "cadence": "weekly",
            "anchor_date": "2026-10-05",
        },
    )
    assert r.status_code == 422
    assert "must differ" in r.text


def test_redirect_requires_stop_rule(client, buckets):
    r = client.post(
        "/api/planned-flows",
        json={
            "name": "x",
            "from_bucket_id": buckets["checking"].id,
            "to_bucket_id": buckets["runway"].id,
            "amount": "1",
            "cadence": "weekly",
            "anchor_date": "2026-10-05",
            "redirect_to_bucket_id": buckets["engine"].id,
        },
    )
    assert r.status_code == 422
    assert "stop_rule fires" in r.text


def test_unknown_bucket_is_422(client, buckets):
    r = client.post(
        "/api/planned-flows",
        json={
            "name": "x",
            "from_bucket_id": 424242,
            "amount": "1",
            "cadence": "weekly",
            "anchor_date": "2026-10-05",
        },
    )
    assert r.status_code == 422
    assert "424242" in r.text


def test_get_and_404(client, plan):
    assert client.get(f"/api/planned-flows/{plan['sweep'].id}").json()["name"] == "Sweep to hub"
    assert client.get("/api/planned-flows/999999").status_code == 404


def test_patch_swap_amount_for_rule(client, plan):
    flow_id = plan["paycheck"].id
    # Sending only amount_rule would violate xor against the stored amount.
    r = client.patch(f"/api/planned-flows/{flow_id}", json={"amount_rule": "remainder"})
    assert r.status_code == 422
    r = client.patch(
        f"/api/planned-flows/{flow_id}",
        json={"amount": None, "amount_rule": "remainder", "from_bucket_id": plan["hub"].id},
    )
    assert r.status_code == 200, r.text
    assert r.json()["amount"] is None
    assert r.json()["amount_rule"] == "remainder"
    assert r.json()["from_bucket_name"] == "Schwab Hub"


def test_patch_amount_only(client, plan):
    r = client.patch(f"/api/planned-flows/{plan['paycheck'].id}", json={"amount": "3300"})
    assert r.status_code == 200
    assert r.json()["amount"] == "3300.00"
    assert r.json()["cadence"] == "per_paycheck"


def test_patch_cannot_null_required(client, plan):
    r = client.patch(f"/api/planned-flows/{plan['paycheck'].id}", json={"cadence": None})
    assert r.status_code == 422


def test_patch_rejects_unknown_redirect_bucket(client, plan):
    r = client.patch(
        f"/api/planned-flows/{plan['runway_flow'].id}", json={"redirect_to_bucket_id": 777777}
    )
    assert r.status_code == 422


def test_delete(client, plan):
    r = client.delete(f"/api/planned-flows/{plan['sweep'].id}")
    assert r.status_code == 204
    assert client.get(f"/api/planned-flows/{plan['sweep'].id}").status_code == 404
    assert client.delete("/api/planned-flows/999999").status_code == 404
