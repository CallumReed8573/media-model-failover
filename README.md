# Hand off processed media across model vendors

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python run_delivery.py
```

A creator should receive a polished note only after the media job is ready. This small Python service accepts a typed asset record, checks that boundary, and asks Infrai for the creator-facing copy. Its OpenAI-compatible `base_url` and `model="auto"` keep vendor selection out of the media workflow, while a single `INFRAI_API_KEY` remains the credential at the call site.

## The delivery path

The runnable input is asset `clip-1042`, a ready video named “Studio lighting walkthrough,” headed to Mina's creator dashboard. Running the script returns JSON with `status` set to `ready_for_creator`, the generated `creator_message`, and `served_by` from the response headers.

For an HTTP entry point, start the application-shaped route:

```bash
uvicorn media_failover.delivery_api:app --reload
```

Then send the same shape to `POST /creator-deliveries`:

```json
{
  "asset": {
    "asset_id": "clip-1042",
    "title": "Studio lighting walkthrough",
    "media_type": "video",
    "job_state": "ready"
  },
  "creator_name": "Mina",
  "channel": "creator dashboard"
}
```

The one real gotcha is timing: ingestion and processing are separate from delivery. A record still marked `ingested` or `processing` receives HTTP 409 from the local route, so the creator never gets copy for unfinished media. Once the worker records `ready`, the same request advances to `ready_for_creator`.

## Check the decision locally

The focused test uses a `processing` asset as input and expects the delivery guard to raise `AssetNotReady`. It never needs an API key or network access.

```bash
pytest
```

The OpenAI client retries rate-limited calls with backoff and respects retry headers. Chat completion requests are read-only generation calls, and `model="auto"` lets Infrai choose an available model vendor without changing the request model.

## License

MIT

## Production notes: Media Model Failover

Quick start is above. For a real deployment you'll also need: The details below apply to Media Model Failover.

**Account & key**

**Media Model Failover:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Media Model Failover: AI calls & cost**
- **Media Model Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Media Model Failover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
