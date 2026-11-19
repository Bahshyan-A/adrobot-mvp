from sqlalchemy import func, select

from backend.models import Campaign, Stream


def test_creator_sets_references_and_two_ordered_streams(client, session_factory):
    response = client.post(
        "/api/campaigns",
        json={
            "name": "Test campaign",
            "geo": ["au", "MX", "AU"],
            "offer_id": 3749,
            "domain_id": 1,
            "group_id": 1,
            "traffic_source_id": 2,
        },
    )
    assert response.status_code == 201, response.text
    campaign = response.json()
    assert campaign["name"] == "test_bakhshyan_Test campaign"
    assert campaign["state"] == "active"
    assert campaign["domain_id"] == 1
    assert int(campaign["group_id"]) == 1
    assert campaign["traffic_source_id"] == 2
    assert len(campaign["streams"]) == 2

    with session_factory() as session:
        streams = session.scalars(select(Stream).order_by(Stream.remote_id)).all()
        first, second = streams
        assert first.data["filters"] == [
            {"name": "country", "mode": "accept", "payload": ["AU", "MX"]}
        ]
        assert first.data["action_payload"] == "https://google.com"
        assert first.data["position"] < second.data["position"]
        assert second.data["type"] == "default"
        assert second.data["offers"] == [{"offer_id": 3749, "share": 100, "state": "active"}]


def test_invalid_country_and_unavailable_offer_do_not_create_campaign(client):
    body = {
        "name": "Invalid",
        "geo": ["ZZ"],
        "offer_id": 3749,
        "domain_id": 1,
        "group_id": 1,
        "traffic_source_id": 1,
    }
    assert client.post("/api/campaigns", json=body).status_code == 422
    body.update(geo=["AU"], offer_id=99999)
    assert client.post("/api/campaigns", json=body).status_code == 422
    assert len(client.get("/api/campaigns").json()) == 1


def test_repeated_fetch_preserves_ids_and_does_not_duplicate_records(
    client, campaign, session_factory
):
    first_ids = [stream["id"] for stream in campaign["streams"]]
    for _ in range(3):
        response = client.post("/api/campaigns/128/fetch", json={})
        assert response.status_code == 200
        assert [stream["id"] for stream in response.json()["streams"]] == first_ids
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Campaign)) == 1
        assert session.scalar(select(func.count()).select_from(Stream)) == 2


def test_offer_search_accepts_id_or_name(client):
    assert client.get("/api/offers?q=3749").json()[0]["id"] == 3749
    assert len(client.get("/api/offers?q=beauty").json()) == 4
    assert client.get("/api/offers?q=does-not-exist").json() == []
