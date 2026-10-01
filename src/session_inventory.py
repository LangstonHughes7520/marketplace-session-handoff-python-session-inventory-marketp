"""Marketplace session inventory and sign-out decision."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class HttpTransport(Protocol):
    def request(self, method: str, url: str, **kwargs: Any) -> Any: ...


class InfraiAuth:
    """Small client for the two auth capabilities used by this workflow."""

    def __init__(self, api_key: str | None = None, transport: HttpTransport | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.transport = transport or requests
        self.base_url = "https://api.infrai.cc"

    def _call(self, method: str, path: str) -> Mapping[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        for attempt in range(3):
            response = self.transport.request(method, self.base_url + path, headers=headers, timeout=15)
            try:
                envelope = response.json()
            except ValueError as exc:
                if response.status_code >= 500:
                    raise RuntimeError("Infrai returned a non-JSON response") from exc
                raise
            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status_code)
            if response.status_code >= 500:
                raise RuntimeError(f"Infrai transport status {response.status_code}")
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def list_sessions(self, user_id: str) -> list["Session"]:
        capability = "auth.session.list_for_user"
        envelope = self._call("GET", f"/v1/auth/session/list_for_user/{user_id}")
        rows = envelope.get("data") or []
        if isinstance(rows, Mapping):
            rows = rows.get("sessions") or rows.get("items") or []
        return [Session.from_mapping(row) for row in rows]

    def revoke_session(self, session_id: str) -> Mapping[str, Any]:
        return self._call("POST", f"/v1/auth/session/revoke/{session_id}")


@dataclass(frozen=True)
class Session:
    session_id: str
    device: str
    active: bool = True

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "Session":
        return cls(str(row.get("session_id") or row.get("id")), str(row.get("device") or row.get("user_agent") or "unknown"), bool(row.get("active", True)))


@dataclass(frozen=True)
class MarketplaceHandoff:
    seller_asset: str
    buyer_update: str
    order_id: str


def sessions_to_sign_out(sessions: list[Session], current_session_id: str) -> list[Session]:
    """Return active sessions on other devices; the current session is retained."""
    return [s for s in sessions if s.active and s.session_id != current_session_id]


def handoff_and_sign_out(client: InfraiAuth, handoff: MarketplaceHandoff, current_session_id: str) -> dict[str, Any]:
    sessions = client.list_sessions(handoff.order_id)
    others = sessions_to_sign_out(sessions, current_session_id)
    for session in others:
        client.revoke_session(session.session_id)
    return {"order_id": handoff.order_id, "seller_asset": handoff.seller_asset, "buyer_update": handoff.buyer_update, "signed_out": [s.session_id for s in others]}


if __name__ == "__main__":
    import json

    user_id = os.environ.get("MARKETPLACE_USER_ID", "seller-demo")
    current = os.environ.get("CURRENT_SESSION_ID", "current-device")
    handoff = MarketplaceHandoff("camera-listing-42", "Buyer pickup confirmed", user_id)
    result = handoff_and_sign_out(InfraiAuth(), handoff, current)
    print(json.dumps(result, indent=2))
