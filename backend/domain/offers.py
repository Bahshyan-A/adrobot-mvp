"""Local snapshots and deterministic traffic allocation for integer API shares."""

from copy import deepcopy
from typing import Literal, TypedDict

from backend.errors import ApplicationError


class OfferSnapshot(TypedDict):
    offer_id: int
    name: str
    share: int
    state: str
    pinned: bool
    removed: bool
    new: bool
    removed_reason: Literal["local", "source"] | None


class OfferBinding(TypedDict):
    offer_id: int
    share: int
    state: str


def active_bindings(offers: list[OfferSnapshot]) -> list[OfferBinding]:
    return [
        {
            "offer_id": offer["offer_id"],
            "share": offer["share"],
            "state": offer.get("state", "active"),
        }
        for offer in offers
        if not offer["removed"]
    ]


def normalized_bindings(offers: list[OfferBinding]) -> list[tuple[int, int, str]]:
    """Ignore API ordering and extra fields when comparing offer configurations."""
    return sorted(
        (offer["offer_id"], offer["share"], offer.get("state", "active")) for offer in offers
    )


def redistribute_weights(offers: list[OfferSnapshot]) -> list[OfferSnapshot]:
    """Return a new snapshot, preserving pinned shares and assigning the remainder in order."""
    result = deepcopy(offers)
    active_offers = [offer for offer in result if not offer["removed"]]

    for offer in result:
        if offer["removed"]:
            offer["share"] = 0
            offer["pinned"] = False

    if not active_offers:
        return result

    pinned_offers = [offer for offer in active_offers if offer["pinned"]]
    unpinned_offers = [offer for offer in active_offers if not offer["pinned"]]
    remaining_share = 100 - sum(offer["share"] for offer in pinned_offers)

    if remaining_share < 0:
        raise ApplicationError(422, "Закреплённые доли превышают 100%. Уменьшите одну из них.")

    if not unpinned_offers and remaining_share != 0:
        raise ApplicationError(
            422,
            "Все доли закреплены, но их сумма не равна 100%. Открепите одну долю.",
        )

    if unpinned_offers:
        base_share, remainder = divmod(remaining_share, len(unpinned_offers))
        for index, offer in enumerate(unpinned_offers):
            offer["share"] = base_share + int(index < remainder)

    return result
