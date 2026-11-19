import pytest
from pydantic import ValidationError

from backend.schemas import CreateCampaign


def campaign_request(name: str) -> CreateCampaign:
    return CreateCampaign(
        name=name,
        geo=["AU"],
        offer_id=3749,
        domain_id=1,
        group_id=1,
        traffic_source_id=1,
    )


@pytest.mark.parametrize(
    ("input_name", "expected"),
    [
        ("campaign1", "test_bakhshyan_campaign1"),
        ("  campaign1  ", "test_bakhshyan_campaign1"),
        ("test_bakhshyan_campaign1", "test_bakhshyan_campaign1"),
    ],
)
def test_campaign_prefix_is_added_exactly_once(input_name, expected):
    assert campaign_request(input_name).name == expected


@pytest.mark.parametrize("name", ["", "   ", "test_bakhshyan_", "test_bakhshyan_   "])
def test_empty_campaign_suffix_is_rejected(name):
    with pytest.raises(ValidationError):
        campaign_request(name)


def test_length_limit_includes_automatically_added_prefix():
    prefix = "test_bakhshyan_"
    assert len(campaign_request("a" * (255 - len(prefix))).name) == 255
    with pytest.raises(ValidationError):
        campaign_request("a" * (256 - len(prefix)))
