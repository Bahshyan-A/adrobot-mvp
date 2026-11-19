"""Sample tracker data, isolated from real Keitaro accounts."""

from typing import Any

OFFERS = [
    {
        "id": 3749,
        "name": "Miaflow · Beauty RO · Основной лендинг",
        "country": ["RO"],
        "state": "active",
    },
    {
        "id": 3717,
        "name": "Miaflow · Beauty RO · Prize landing",
        "country": ["RO"],
        "state": "active",
    },
    {
        "id": 3812,
        "name": "Miaflow · Beauty RO · Spin landing",
        "country": ["RO"],
        "state": "active",
    },
    {"id": 3826, "name": "Nutra · Wellness AU · Main offer", "country": ["AU"], "state": "active"},
    {"id": 3901, "name": "Finance · Mexico · Lead form", "country": ["MX"], "state": "active"},
    {
        "id": 3940,
        "name": "Miaflow · Beauty RO · Summer edition",
        "country": ["RO"],
        "state": "active",
    },
]


def tracker_data() -> dict[str, Any]:
    return {
        "campaigns": [
            {
                "id": 128,
                "name": "Beauty · Romania",
                "alias": "beauty-ro",
                "domain_id": 1,
                "group_id": 1,
                "traffic_source_id": 1,
                "state": "active",
                "type": "position",
            }
        ],
        "streams": [
            {
                "id": 401,
                "campaign_id": 128,
                "name": "Геофильтр · Google",
                "type": "regular",
                "position": 1,
                "schema": "redirect",
                "state": "active",
                "action_type": "http",
                "action_payload": "https://google.com",
                "filters": [{"name": "country", "mode": "accept", "payload": ["AU"]}],
                "offers": [],
            },
            {
                "id": 402,
                "campaign_id": 128,
                "name": "Основной поток",
                "type": "default",
                "position": 2,
                "schema": "landings",
                "action_type": "http",
                "state": "active",
                "filters": [],
                "landings": [],
                "offers": [
                    {"offer_id": 3749, "share": 34, "state": "active"},
                    {"offer_id": 3717, "share": 33, "state": "active"},
                    {"offer_id": 3812, "share": 33, "state": "active"},
                ],
            },
        ],
        "offers": OFFERS,
        "domains": [
            {"id": 1, "name": "https://track.example.com", "state": "active"},
            {"id": 2, "name": "https://go.example.com", "state": "active"},
        ],
        "groups": [{"id": 1, "name": "FORTESTS"}, {"id": 2, "name": "Production"}],
        "traffic_sources": [
            {"id": 1, "name": "FORTESTS"},
            {"id": 2, "name": "Meta Ads"},
            {"id": 3, "name": "Google Ads"},
        ],
    }
