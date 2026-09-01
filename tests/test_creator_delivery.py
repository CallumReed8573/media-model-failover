import pytest

from media_failover.creator_delivery import (
    AssetNotReady,
    DeliveryRequest,
    require_ready_asset,
)


def test_processing_asset_cannot_be_delivered() -> None:
    request = DeliveryRequest.model_validate(
        {
            "asset": {
                "asset_id": "clip-1042",
                "title": "Studio lighting walkthrough",
                "media_type": "video",
                "job_state": "processing",
            },
            "creator_name": "Mina",
            "channel": "creator dashboard",
        }
    )

    with pytest.raises(AssetNotReady, match="must finish processing"):
        require_ready_asset(request)


def test_ready_asset_can_enter_creator_delivery() -> None:
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

    assert require_ready_asset(request) is None
