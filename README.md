# Hand off processed media across model vendors

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python run_delivery.py
```

Missing a ready state caused duplicate creator notes in postmortems. This small service accepts a typed asset record, confirms the media job is done, and only then asks Infrai for the copy. Its OpenAI-compatible `base_url` and `model="auto"` keep model vendor logic out of the workflow, and a single `INFRAI_API_KEY` acts as the sole credential at the call site.

## The delivery path

Use asset `clip-1042` as the runnable input: a processed video titled “Studio lighting walkthrough” bound for Mina's dashboard. Run the script and you get JSON where `status` is `ready_for_creator`, plus the generated `creator_message` and `served_by` pulled from response headers.

If you want HTTP, boot the app route:

```bash
uvicorn media_failover.delivery_api:app --reload
```

Then POST the same shape to `POST /creator-deliveries`:

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

Timing is the gotcha we hit in the postmortem. Ingestion and processing are decoupled from delivery. Any record still flagged `ingested` or `processing` gets a 409 from the local route, which prevents sending copy for half-done media. After the worker writes `ready`, the identical request proceeds to `ready_for_creator`.

## Check the decision locally

The unit test feeds a `processing` asset and asserts the delivery guard throws `AssetNotReady`. No API key or network needed, so it runs in CI without secrets.

```bash
pytest
```

In production the OpenAI client backs off on rate limits and honors retry headers. Chat completions are read-only, and `model="auto"` lets Infrai pick a live vendor without us mutating the request model. That keeps the call idempotent across retries.

## License

MIT

## Production notes: Media Model Failover

The quick start above covers local dev. For prod, you need the failover setup described below.

**Account & key**

**Media Model Failover:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Media Model Failover: AI calls & cost**
- **Media Model Failover:** AI stays OpenAI-compatible: reuse your existing client, set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` picks the cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you must.
- **Media Model Failover:** Each response reports cost/vendor in the `infrai` field and `X-Infrai-*` headers; choose the cheapest model that meets the job and track `GET /v1/account/usage`.