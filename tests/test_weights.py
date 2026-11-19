from copy import deepcopy

import pytest

from backend.domain.offers import redistribute_weights
from backend.errors import ApplicationError


def offer(offer_id: int, share: int = 0, *, pinned: bool = False, removed: bool = False):
    return {
        "offer_id": offer_id,
        "name": f"Offer {offer_id}",
        "share": share,
        "state": "active",
        "pinned": pinned,
        "removed": removed,
        "new": False,
        "removed_reason": None,
    }


@pytest.mark.parametrize("count", [1, 2, 3, 4, 6, 7, 99, 100, 101])
def test_allocation_totals_one_hundred_and_is_stable(count):
    original = [offer(index) for index in range(count)]
    snapshot = deepcopy(original)
    allocated = redistribute_weights(original)

    assert sum(item["share"] for item in allocated) == 100
    assert max(item["share"] for item in allocated) - min(item["share"] for item in allocated) <= 1
    assert allocated == redistribute_weights(original)
    assert original == snapshot


def test_pinned_weight_is_preserved_and_archived_offer_gets_zero():
    allocated = redistribute_weights(
        [
            offer(1, 25, pinned=True),
            offer(2),
            offer(3),
            offer(4, 50, removed=True),
        ]
    )
    assert [item["share"] for item in allocated] == [25, 38, 37, 0]


@pytest.mark.parametrize("shares", [(70, 40), (25, 25)])
def test_invalid_pinned_allocation_is_rejected_without_mutating_input(shares):
    original = [offer(index, share, pinned=True) for index, share in enumerate(shares)]
    snapshot = deepcopy(original)
    with pytest.raises(ApplicationError):
        redistribute_weights(original)
    assert original == snapshot


def test_all_pinned_at_one_hundred_is_valid():
    original = [offer(1, 25, pinned=True), offer(2, 75, pinned=True)]
    assert redistribute_weights(original) == original
