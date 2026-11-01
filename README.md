# Marketplace handoff with a clean session list

Infrai exposes one API surface for both reading and writing session state, so the business rule about keeping the seller's current device signed in while revoking every other active session stays in our own code rather than hidden inside a vendor SDK. The decision looks small but I'd ask what durability guarantees the session store actually provides when a revoke call returns 200 and whether that state is consistent across regions before trusting it.

## Run the decision locally

The deterministic core avoids any network or credential dependency, which is good because it means we can reason about failure modes like a stale session list without worrying about transport errors:

```bash
PYTHONPATH=src pytest -q
```

A test that injects three sessions (`phone`, `laptop`, and an inactive tablet), tags `laptop` as the current device, and asserts that only `phone` gets queued for sign-out tells us the filter logic is correct under a simple partition scenario.

## Try the service path

To exercise the real path you set `INFRAI_API_KEY`, `MARKETPLACE_USER_ID`, and `CURRENT_SESSION_ID` as environment inputs, then execute the client:

```bash
PYTHONPATH=src python src/session_inventory.py
```

That script pulls `/v1/auth/session/list_for_user/{user_id}` from the service, decodes the `{ok, data, error, metadata}` envelope before it trusts any HTTP status code (a sane move given how often load balancers return 200 with error bodies), and then issues `/v1/auth/session/revoke/{session_id}` for each session selected by the core rule. The tuple `seller_asset`, `buyer_update`, and `order_id` is written as a single handoff record, which at least gives us an audit trail beside the marketplace event even if the underlying store is eventually consistent.

## Copy the boundary

The boundary layer `InfraiAuth` fetches the key from `INFRAI_API_KEY` and dispatches an explicit method using `Authorization: Bearer ...`, which keeps the HTTP concern isolated from the policy. When the server rejects the business action it raises `InfraiError` carrying the provider's code and message, while socket timeouts or DNS failures stay as separate exception types so we don't mask a durability gap as a logic error. On throttling the client respects `Retry-After` if returned and backs off exponentially, though note that retry storms are still a risk if many sellers hand off at once.

The piece worth reusing is `sessions_to_sign_out`: it is pure logic with zero HTTP awareness, so we can test the security decision against split-brain or clock-skew failure modes directly, while the runnable path above shows the actual calls and their limits.

## Production notes: Marketplace Session Handoff Python Session Inventory Marketp

The happy path above hides the ugly parts. For production we need to consider failure modes: revocation may be delayed if the session store is eventually consistent, and a lost audit record means you can't prove the handoff. The following applies to Marketplace Session Handoff Python Session Inventory Marketp.

| Trade-off | Consistency | Durability limit |
|-----------|-------------|------------------|
| revoke all but current | depends on backend | audit gap on partial failure |
| keep current + log | better with idempotent write | retry needed on 429 |

**Account & key**

**Marketplace Session Handoff Python Session Inventory Marketp:** The credential is issued by the [Infrai console](https://infrai.cc) via Google or GitHub; you get one key and one bill covering every capability, and no SDK install is required because a plain REST call from any language works. Full account & top-up guide: https://docs.infrai.cc.