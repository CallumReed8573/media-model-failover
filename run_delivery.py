import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from media_failover.creator_delivery import CreatorDeliveryService, DeliveryRequest


request = DeliveryRequest.model_validate(
    {
        "asset": {
            "asset_id": "clip-1042",
            "title": "Studio lighting walkthrough",
            "media_type": "video",
            "job_state": "ready",
        },
        "creator_name": "Mina",
        "channel": "creator dashboard",
    }
)

print(CreatorDeliveryService().prepare(request).model_dump_json(indent=2))
