from copy import deepcopy

from backend.errors import ApplicationError
from backend.integrations.keitaro import KeitaroClient


def edit(client, stream, action, offer_id, **fields):
    return client.post(
        f"/api/streams/{stream['id']}/offers",
        json={
            "revision": stream["revision"],
            "action": action,
            "offer_id": offer_id,
            **fields,
        },
    )


def test_add_is_local_until_push_and_cancel_removes_new_binding(client, stream, tracker_stub):
    added = edit(client, stream, "add", 3940).json()
    assert added["dirty"]
    assert [offer["share"] for offer in added["offers"]] == [25, 25, 25, 25]
    reloaded = client.get("/api/campaigns/128").json()["streams"][1]
    assert reloaded == added

    remote = tracker_stub.data["streams"][1]
    assert len(remote["offers"]) == 3

    cancelled = client.post(
        f"/api/streams/{stream['id']}/cancel", json={"revision": added["revision"]}
    )
    assert cancelled.status_code == 200
    assert not cancelled.json()["dirty"]
    assert len(cancelled.json()["offers"]) == 3


def test_remove_push_restore_preserves_archive_and_pin(client, stream, tracker_stub):
    pinned = edit(client, stream, "pin", 3749, share=25).json()
    removed = edit(client, pinned, "remove", 3717).json()
    assert [offer["share"] for offer in removed["offers"]] == [25, 0, 75]
    pushed = client.post(
        f"/api/streams/{stream['id']}/push", json={"revision": removed["revision"]}
    )
    assert pushed.status_code == 200, pushed.text
    published = pushed.json()
    assert not published["dirty"]
    assert len(published["offers"]) == 3
    assert published["offers"][1]["removed"]

    remote = tracker_stub.data["streams"][1]
    assert [offer["offer_id"] for offer in remote["offers"]] == [3749, 3812]

    restored = edit(client, published, "restore", 3717).json()
    assert [offer["share"] for offer in restored["offers"]] == [25, 38, 37]
    assert restored["offers"][0]["pinned"]
    assert len({offer["offer_id"] for offer in restored["offers"]}) == 3


def test_duplicate_add_and_stale_revision_are_rejected(client, stream):
    assert edit(client, stream, "add", 3749).status_code == 409
    assert edit(client, stream, "add", 3940).status_code == 200
    assert edit(client, stream, "remove", 3717).status_code == 409


def test_invalid_pinned_weight_keeps_previous_draft(client, stream):
    pinned = edit(client, stream, "pin", 3749, share=80).json()
    invalid = edit(client, pinned, "pin", 3717, share=30)
    assert invalid.status_code == 422
    actual = client.get("/api/campaigns/128").json()["streams"][1]
    assert actual == pinned
    assert edit(client, pinned, "pin", 3717, share=12.5).status_code == 422


def test_all_offers_can_be_removed_and_published_with_archive_preserved(
    client, stream, tracker_stub
):
    current = stream
    for offer_id in [3749, 3717, 3812]:
        current = edit(client, current, "remove", offer_id).json()
    response = client.post(
        f"/api/streams/{stream['id']}/push", json={"revision": current["revision"]}
    )
    assert response.status_code == 200, response.text
    assert current["total_share"] == 0
    published = response.json()
    assert not published["dirty"]
    assert published["active_count"] == 0
    assert len(published["offers"]) == 3
    assert all(offer["removed"] and offer["share"] == 0 for offer in published["offers"])
    assert tracker_stub.data["streams"][1]["offers"] == []

    restored = edit(client, published, "restore", 3749).json()
    assert restored["total_share"] == 100
    assert restored["active_count"] == 1
    assert len(restored["offers"]) == 3
    response = client.post(
        f"/api/streams/{stream['id']}/push", json={"revision": restored["revision"]}
    )
    assert response.status_code == 200, response.text
    assert tracker_stub.data["streams"][1]["offers"] == [
        {"offer_id": 3749, "share": 100, "state": "active"}
    ]


def test_failed_publication_preserves_draft(client, stream, monkeypatch):
    draft = edit(client, stream, "add", 3940).json()

    def fail_update(*_args, **_kwargs):
        raise ApplicationError(504, "Test timeout")

    monkeypatch.setattr(KeitaroClient, "update_stream_offers", fail_update)
    response = client.post(
        f"/api/streams/{stream['id']}/push", json={"revision": draft["revision"]}
    )
    assert response.status_code == 504
    assert client.get("/api/campaigns/128").json()["streams"][1] == draft


def test_retry_after_ambiguous_success_confirms_without_duplicate_update(
    client, stream, change_remote, monkeypatch
):
    draft = edit(client, stream, "add", 3940).json()
    desired = [
        {"offer_id": offer["offer_id"], "share": offer["share"], "state": "active"}
        for offer in draft["offers"]
    ]
    change_remote(lambda data: data["streams"][1].update(offers=desired))

    def unexpected_update(*_args, **_kwargs):
        raise AssertionError("An already applied configuration must not be sent twice")

    monkeypatch.setattr(KeitaroClient, "update_stream_offers", unexpected_update)
    response = client.post(
        f"/api/streams/{stream['id']}/push", json={"revision": draft["revision"]}
    )
    assert response.status_code == 200, response.text
    assert not response.json()["dirty"]


def test_push_preserves_filters_landings_and_other_stream_settings(
    client, stream, change_remote, tracker_stub
):
    metadata = {
        "filters": [{"name": "device_type", "payload": ["mobile"], "mode": "accept"}],
        "landings": [{"landing_id": 42, "share": 100}],
        "comments": "Keep me",
    }
    change_remote(lambda data: data["streams"][1].update(deepcopy(metadata)))
    draft = edit(client, stream, "add", 3940).json()
    response = client.post(
        f"/api/streams/{stream['id']}/push", json={"revision": draft["revision"]}
    )
    assert response.status_code == 200
    remote = tracker_stub.data["streams"][1]
    assert all(remote[key] == value for key, value in metadata.items())


def test_technical_stream_cannot_be_edited(client, campaign):
    technical = campaign["streams"][0]
    assert not technical["editable"]
    assert edit(client, technical, "add", 3940).status_code == 422


def test_audit_history_records_draft_and_publication(client, stream):
    draft = edit(client, stream, "add", 3940).json()
    client.post(f"/api/streams/{stream['id']}/push", json={"revision": draft["revision"]})
    events = client.get("/api/campaigns/128/history").json()
    assert [event["action"] for event in events][:3] == ["push", "add", "fetch"]
