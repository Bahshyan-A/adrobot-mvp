from threading import RLock
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies import DatabaseSession, TrackerClient, authorize
from backend.errors import ApplicationError
from backend.schemas import CreateCampaign, EditOffer, FetchRequest, Revision
from backend.services import audit, campaigns, streams, synchronization
from backend.services.serialization import campaign_response

router = APIRouter(prefix="/api", dependencies=[Depends(authorize)])

# The application runs with one worker. Serialize mutations across local tabs;
# SQLAlchemy revisions additionally reject stale snapshots.
mutation_lock = RLock()


@router.get("/catalog")
def get_catalog(session: DatabaseSession, client: TrackerClient):
    result = {
        entity: client.list_entities(entity) for entity in ("domains", "groups", "traffic_sources")
    }
    session.commit()
    return result


@router.get("/offers")
def search_offers(
    session: DatabaseSession,
    client: TrackerClient,
    q: Annotated[str, Query(max_length=200)] = "",
):
    query = q.strip().casefold()
    matches = [
        offer
        for offer in client.list_entities("offers")
        if offer.get("state") == "active"
        and (not query or query in offer["name"].casefold() or query in str(offer["id"]))
    ]
    session.commit()
    return matches[:50]


@router.get("/campaigns")
def get_campaigns(session: DatabaseSession, client: TrackerClient, q: str = ""):
    return campaigns.list_campaigns(session, client, q)


@router.post("/campaigns", status_code=201)
def create_campaign(body: CreateCampaign, session: DatabaseSession, client: TrackerClient):
    with mutation_lock:
        return campaigns.create_campaign(session, client, body)


@router.get("/campaigns/{remote_id}")
def get_campaign(remote_id: int, session: DatabaseSession, client: TrackerClient):
    with mutation_lock:
        campaign = synchronization.find_campaign(session, remote_id)
        if campaign:
            return campaign_response(campaign)
        return synchronization.fetch_campaign(session, client, remote_id)


@router.post("/campaigns/{remote_id}/fetch")
def fetch_campaign(
    remote_id: int,
    body: FetchRequest,
    session: DatabaseSession,
    client: TrackerClient,
):
    with mutation_lock:
        return synchronization.fetch_campaign(
            session,
            client,
            remote_id,
            discard_drafts=body.discard_drafts,
            revisions=body.revisions,
        )


@router.get("/campaigns/{remote_id}/history")
def get_campaign_history(remote_id: int, session: DatabaseSession):
    return audit.get_history(session, remote_id)


@router.post("/streams/{stream_id}/offers")
def edit_offer(
    stream_id: int,
    body: EditOffer,
    session: DatabaseSession,
    client: TrackerClient,
):
    with mutation_lock:
        return streams.edit_offer(session, client, stream_id, body)


@router.post("/streams/{stream_id}/cancel")
def cancel_stream_draft(stream_id: int, body: Revision, session: DatabaseSession):
    with mutation_lock:
        return streams.cancel_draft(session, stream_id, body.revision)


@router.post("/streams/{stream_id}/push")
def publish_stream_draft(
    stream_id: int,
    body: Revision,
    session: DatabaseSession,
    client: TrackerClient,
):
    with mutation_lock:
        return streams.publish_draft(session, client, stream_id, body.revision)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
def api_not_found(path: str):
    raise ApplicationError(404, "API endpoint not found")
