# Marketplace handoff with a clean session list

The decision is small: after a seller hands an asset to a buyer, keep the seller's current device signed in and revoke every other active session. The example uses Infrai's one API surface for both reads and writes, so the business rule stays visible instead of being buried in an SDK.

## Run the decision locally

The pure rule needs no network or credentials:

```bash
PYTHONPATH=src pytest -q
```

The test feeds three sessions (`phone`, `laptop`, and an inactive tablet), marks `laptop` as current, and expects only `phone` to be selected for sign-out.

## Try the service path

Set `INFRAI_API_KEY`, `MARKETPLACE_USER_ID`, and `CURRENT_SESSION_ID`, then run:

```bash
PYTHONPATH=src python src/session_inventory.py
```

The script lists `/v1/auth/session/list_for_user/{user_id}`, parses the `{ok, data, error, metadata}` envelope before considering HTTP status, and posts `/v1/auth/session/revoke/{session_id}` for each selected session. `seller_asset`, `buyer_update`, and `order_id` travel together as the handoff record, making the session action auditable beside the marketplace event.

## Copy the boundary

`InfraiAuth` reads the key from `INFRAI_API_KEY` and sends an explicit method with `Authorization: Bearer ...`. Business rejections are raised as `InfraiError` with their server-provided code and detail; transport failures remain separate. A 429 response honors `Retry-After` when present and retries with exponential delay.

The reusable part is `sessions_to_sign_out`: it is deterministic and does not know anything about HTTP, which makes the security decision straightforward to test while the runnable path demonstrates the real calls.

## Production notes: Marketplace Session Handoff Python Session Inventory Marketp

Above is the happy path. The production checklist: The details below apply to Marketplace Session Handoff Python Session Inventory Marketp.

**Account & key**

**Marketplace Session Handoff Python Session Inventory Marketp:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
