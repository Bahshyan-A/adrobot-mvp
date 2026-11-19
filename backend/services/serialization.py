from typing import Any

from backend.models import Campaign, Stream


def stream_response(stream: Stream) -> dict[str, Any]:
    active_offers = [offer for offer in stream.draft if not offer["removed"]]
    return {
        "id": stream.id,
        "remote_id": stream.remote_id,
        "name": stream.data["name"],
        "position": stream.data.get("position", 0),
        "schema": stream.data.get("schema"),
        "editable": stream.is_editable,
        "source_missing": stream.is_missing,
        "dirty": stream.is_dirty,
        "revision": stream.revision,
        "offers": stream.draft,
        "published_count": sum(not offer["removed"] for offer in stream.published),
        "active_count": len(active_offers),
        "total_share": sum(offer["share"] for offer in active_offers),
    }


def campaign_response(campaign: Campaign) -> dict[str, Any]:
    streams = sorted(campaign.streams, key=lambda stream: stream.data.get("position", 0))
    return {
        **campaign.data,
        "local_id": campaign.id,
        "synced_at": campaign.synced_at.isoformat(),
        "streams": [stream_response(stream) for stream in streams],
    }
