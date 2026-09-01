from fastapi import FastAPI, HTTPException
from openai import APIStatusError

from .creator_delivery import (
    AssetNotReady,
    CreatorDeliveryService,
    DeliveryRequest,
    DeliveryResult,
)

app = FastAPI(title="Media creator delivery")


@app.post("/creator-deliveries", response_model=DeliveryResult)
def create_creator_delivery(request: DeliveryRequest) -> DeliveryResult:
    try:
        return CreatorDeliveryService().prepare(request)
    except AssetNotReady as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except APIStatusError as exc:
        if 400 <= exc.status_code < 500:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        raise
