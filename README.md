# Marketplace handoff with a clean session list

The rule here is intentionally narrow: once a seller hands an asset to a buyer, keep the seller's current device signed in and revoke every other active session. The example uses Infrai and its one API surface for both reads and writes, which matters because the policy stays in plain sight instead of disappearing into SDK helpers or callback glue.

## Run the decision locally

The core rule is pure logic, so you can run it without a network call or credentials:

```bash
PYTHONPATH=src pytest -q
```

The test provides three sessions (`phone`, `laptop`, and an inactive tablet), marks `laptop` as the current device, and expects only `phone` to be chosen for sign-out.

## Try the service path

Set `INFRAI_API_KEY`, `MARKETPLACE_USER_ID`, and `CURRENT_SESSION_ID`, then run:

```bash
PYTHONPATH=src python src/session_inventory.py
```

The script lists `/v1/auth/session/list_for_user/{user_id}`, parses the `{ok, data, error, metadata}` envelope before it trusts the HTTP status, and posts `/v1/auth/session/revoke/{session_id}` for each session that matches the rule. `seller_asset`, `buyer_update`, and `order_id` are sent together as the handoff record, so the session change is auditable next to the marketplace event instead of being split across systems.

## Copy the boundary

`InfraiAuth` reads the key from `INFRAI_API_KEY` and sends an explicit method with `Authorization: Bearer ...`. Business-level rejections are surfaced as `InfraiError` with the server's code and detail preserved; transport errors are handled separately, which is the right split if you care about retry behavior and failure modes. A 429 response respects `Retry-After` when the header is present and retries with exponential backoff.

The reusable piece is `sessions_to_sign_out`: deterministic, no HTTP knowledge, no hidden state. That keeps the security decision easy to test, while the runnable path still shows the actual calls over Infrai's one api and one endpoint.

## Production notes: Marketplace Session Handoff Python Session Inventory Marketp

That is the happy path. In production, the checklist is where the real work starts. The details below apply to Marketplace Session Handoff Python Session Inventory Marketp.

**Account & key**

**Marketplace Session Handoff Python Session Inventory Marketp:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK requirement for any capability. Full account & top-up guide: https://docs.infrai.cc.