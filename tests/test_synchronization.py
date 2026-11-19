from backend.integrations.keitaro import KeitaroClient
from tests.test_drafts import edit


def test_external_removal_moves_offer_to_archive(client, stream, change_remote):
    def remove_offer(data):
        data["streams"][1]["offers"] = [
            {"offer_id": 3749, "share": 50, "state": "active"},
            {"offer_id": 3812, "share": 50, "state": "active"},
        ]

    change_remote(remove_offer)
    response = client.post("/api/campaigns/128/fetch", json={})
    assert response.status_code == 200
    result = response.json()
    archived = next(offer for offer in result["streams"][1]["offers"] if offer["offer_id"] == 3717)
    assert archived["removed"] and archived["share"] == 0
    assert archived["removed_reason"] == "source"
    assert result["sync_changes"]


def test_fetch_conflict_preserves_draft_and_requires_explicit_discard(
    client, stream, change_remote
):
    draft = edit(client, stream, "add", 3940).json()
    change_remote(lambda data: data["streams"][1]["offers"].pop())

    response = client.post("/api/campaigns/128/fetch", json={})
    assert response.status_code == 409
    conflict = response.json()["detail"]
    assert conflict["sync_conflict"] and conflict["changes"]
    assert client.get("/api/campaigns/128").json()["streams"][1] == draft

    confirmed = client.post(
        "/api/campaigns/128/fetch",
        json={
            "discard_drafts": True,
            "revisions": conflict["revisions"],
        },
    )
    assert confirmed.status_code == 200
    assert not confirmed.json()["streams"][1]["dirty"]


def test_push_rejects_external_changes_without_overwriting_them(client, stream, change_remote):
    draft = edit(client, stream, "add", 3940).json()
    change_remote(lambda data: data["streams"][1]["offers"].pop())
    response = client.post(
        f"/api/streams/{stream['id']}/push", json={"revision": draft["revision"]}
    )
    assert response.status_code == 409
    assert client.get("/api/campaigns/128").json()["streams"][1] == draft


def test_invalid_fetch_response_does_not_destroy_snapshot(client, stream, monkeypatch):
    monkeypatch.setattr(KeitaroClient, "get_streams", lambda *_: [{"id": "bad"}])
    response = client.post("/api/campaigns/128/fetch", json={})
    assert response.status_code == 502
    assert client.get("/api/campaigns/128").json()["streams"][1] == stream


def test_deleted_stream_keeps_local_history(client, campaign, change_remote):
    change_remote(lambda data: data["streams"].pop())
    result = client.post("/api/campaigns/128/fetch", json={}).json()
    archived_stream = result["streams"][1]
    assert archived_stream["source_missing"]
    assert all(offer["removed"] for offer in archived_stream["offers"])
