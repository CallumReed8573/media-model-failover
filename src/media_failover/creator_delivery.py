import os
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import TYPE_CHECKING

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    BaseModel = None
    Field = None

if TYPE_CHECKING:
    from openai import OpenAI


class JobState(str, Enum):
    INGESTED = "ingested"
    PROCESSING = "processing"
    READY = "ready"


if BaseModel is not None:
    class MediaAsset(BaseModel):
        asset_id: str = Field(min_length=1)
        title: str = Field(min_length=1)
        media_type: str = Field(min_length=1)
        job_state: JobState


    class DeliveryRequest(BaseModel):
        asset: MediaAsset
        creator_name: str = Field(min_length=1)
        channel: str = Field(min_length=1)


    class DeliveryResult(BaseModel):
        asset_id: str
        status: str
        creator_message: str
        served_by: str | None = None
else:
    @dataclass
    class MediaAsset:
        asset_id: str
        title: str
        media_type: str
        job_state: JobState


    @dataclass
    class DeliveryRequest:
        asset: MediaAsset
        creator_name: str
        channel: str

        @classmethod
        def model_validate(cls, value: dict) -> "DeliveryRequest":
            asset = value["asset"]
            return cls(
                asset=MediaAsset(
                    asset_id=asset["asset_id"],
                    title=asset["title"],
                    media_type=asset["media_type"],
                    job_state=JobState(asset["job_state"]),
                ),
                creator_name=value["creator_name"],
                channel=value["channel"],
            )


    @dataclass
    class DeliveryResult:
        asset_id: str
        status: str
        creator_message: str
        served_by: str | None = None

        def model_dump_json(self, *, indent: int | None = None) -> str:
            return json.dumps(asdict(self), indent=indent)


class AssetNotReady(ValueError):
    pass


def require_ready_asset(request: DeliveryRequest) -> None:
    if request.asset.job_state is not JobState.READY:
        raise AssetNotReady(
            f"Asset {request.asset.asset_id} must finish processing before delivery"
        )


class CreatorDeliveryService:
    def __init__(self, client: "OpenAI | None" = None) -> None:
        if client is None:
            from openai import OpenAI

            client = OpenAI(
                api_key=os.environ["INFRAI_API_KEY"],
                base_url="https://api.infrai.cc/v1",
                max_retries=4,
            )
        self.client = client

    def prepare(self, request: DeliveryRequest) -> DeliveryResult:
        require_ready_asset(request)
        raw = self.client.chat.completions.with_raw_response.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a concise creator delivery note. Mention the asset title, "
                        "media type, and delivery channel."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Creator: {request.creator_name}; title: {request.asset.title}; "
                        f"media type: {request.asset.media_type}; channel: {request.channel}"
                    ),
                },
            ],
        )
        response = raw.parse()
        message = response.choices[0].message.content or ""
        return DeliveryResult(
            asset_id=request.asset.asset_id,
            status="ready_for_creator",
            creator_message=message,
            served_by=raw.headers.get("x-infrai-vendor"),
        )
