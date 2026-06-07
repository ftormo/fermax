"""HTTP client for the Fermax API."""
from __future__ import annotations

import base64
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import aiohttp

from .const import API_BASE_URL, CLIENT_ID, CLIENT_SECRET, OAUTH_URL

_LOGGER = logging.getLogger(__name__)

_BASIC_AUTH = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

_COMMON_HEADERS: dict[str, str] = {
    "app-version": "4.3.1",
    "Accept": "*/*",
    "Accept-Language": "es-ES;q=1.0",
    "User-Agent": (
        "Blue/4.3.1 (com.fermax.bluefermax; build:3; iOS 26.1.0) Alamofire/5.10.2"
    ),
    "phone-os": "26.1",
    "phone-model": "iPhone 13",
    "app-build": "3",
}


class FermaxApiError(Exception):
    """Generic Fermax API error."""


class FermaxAuthError(FermaxApiError):
    """Authentication error in the Fermax API."""


class FermaxApi:
    """Client for the Fermax API."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
        token_update_callback: (
            Callable[[str, str], Coroutine[Any, Any, None]] | None
        ) = None,
    ) -> None:
        self._username = username
        self._password = password
        self._session = session
        self._token_update_callback = token_update_callback
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    @property
    def access_token(self) -> str | None:
        """Return the current access token."""
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        """Return the current refresh token."""
        return self._refresh_token

    def set_tokens(
        self,
        access_token: str | None,
        refresh_token: str | None = None,
    ) -> None:
        """Load previously stored tokens (for example, on HA restart)."""
        self._access_token = access_token
        self._refresh_token = refresh_token

    async def authenticate(self) -> None:
        """Get a new access and refresh token using username/password."""
        headers = {
            **_COMMON_HEADERS,
            "Authorization": f"Basic {_BASIC_AUTH}",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }
        data = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }

        async with self._session.post(OAUTH_URL, headers=headers, data=data) as resp:
            if resp.status == 401:
                raise FermaxAuthError("Invalid credentials")
            if resp.status >= 400:
                raise FermaxApiError(f"Failed to get token: HTTP {resp.status}")
            result: dict[str, Any] = await resp.json(content_type=None)

        self._access_token = result["access_token"]
        self._refresh_token = result["refresh_token"]
        _LOGGER.debug("Fermax token refreshed successfully")

        if self._token_update_callback:
            await self._token_update_callback(self._access_token, self._refresh_token)

    async def get_pairings(self) -> list[dict[str, Any]]:
        """Return the user's pairings list (GET /me)."""
        return await self._request(
            "GET", f"{API_BASE_URL}/pairing/api/v4/pairings/me"
        )

    async def open_door(
        self,
        device_id: str,
        pairing_type: str,
        unit_id: str,
        access_id: dict[str, int],
    ) -> Any:
        """Open a door (POST /directed-opendoor)."""
        url = (
            f"{API_BASE_URL}/deviceaction/api/v1/device"
            f"/{device_id}/directed-opendoor"
        )
        params = {"pairingType": pairing_type, "unitId": unit_id}
        return await self._request("POST", url, json=access_id, params=params)

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make an authenticated request and refresh token on 401."""
        if not self._access_token:
            await self.authenticate()

        headers = {
            **_COMMON_HEADERS,
            "Authorization": f"Bearer {self._access_token}",
        }

        async with self._session.request(
            method, url, headers=headers, **kwargs
        ) as resp:
            if resp.status == 401:
                _LOGGER.debug("Token expired, refreshing...")
                await self.authenticate()
                headers["Authorization"] = f"Bearer {self._access_token}"
                async with self._session.request(
                    method, url, headers=headers, **kwargs
                ) as retry:
                    if retry.status == 401:
                        raise FermaxAuthError("Authentication failed after token refresh")
                    if retry.status >= 400:
                        raise FermaxApiError(f"API error after token refresh: HTTP {retry.status}")
                    return await _parse_response(retry)

            if resp.status >= 400:
                raise FermaxApiError(f"API error: HTTP {resp.status}")

            return await _parse_response(resp)


async def _parse_response(response: aiohttp.ClientResponse) -> Any:
    """Parse JSON response and return None when body is empty."""
    if response.status == 204 or response.content_length == 0:
        return None
    try:
        return await response.json(content_type=None)
    except Exception:  # noqa: BLE001
        return None
