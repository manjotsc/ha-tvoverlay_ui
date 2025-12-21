"""API client for TvOverlay."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import (
    DEFAULT_TIMEOUT,
    ENDPOINT_GET,
    ENDPOINT_NOTIFY,
    ENDPOINT_NOTIFY_FIXED,
    ENDPOINT_SET_NOTIFICATIONS,
    ENDPOINT_SET_OVERLAY,
    ENDPOINT_SET_SETTINGS,
)

_LOGGER = logging.getLogger(__name__)


class TvOverlayApiError(Exception):
    """Exception for TvOverlay API errors."""


class TvOverlayConnectionError(TvOverlayApiError):
    """Exception for connection errors."""


class TvOverlayApiClient:
    """API client for TvOverlay devices."""

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._port = port
        self._session = session
        self._base_url = f"http://{host}:{port}"

    @property
    def host(self) -> str:
        """Return the host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port."""
        return self._port

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any] | None]:
        """Make an HTTP request to the TvOverlay API.

        Returns:
            Tuple of (success, response_data)
        """
        url = f"{self._base_url}{endpoint}"
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)

        try:
            # Use existing session or create a temporary one
            if self._session is None or self._session.closed:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    return await self._execute_request(session, method, url, data)
            else:
                return await self._execute_request(self._session, method, url, data)

        except asyncio.TimeoutError as err:
            raise TvOverlayConnectionError(
                f"Timeout connecting to TvOverlay at {self._host}:{self._port}"
            ) from err
        except aiohttp.ClientError as err:
            raise TvOverlayConnectionError(
                f"Error connecting to TvOverlay at {self._host}:{self._port}: {err}"
            ) from err

    async def _execute_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        data: dict[str, Any] | None,
    ) -> tuple[bool, dict[str, Any] | None]:
        """Execute the HTTP request."""
        if method == "GET":
            async with session.get(url) as response:
                return await self._handle_response(response)
        else:  # POST
            async with session.post(url, json=data or {}) as response:
                return await self._handle_response(response)

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
    ) -> tuple[bool, dict[str, Any] | None]:
        """Handle the API response."""
        if response.status == 200:
            try:
                json_data = await response.json()
                return True, json_data
            except Exception:
                return True, None

        _LOGGER.error(
            "TvOverlay API error: %s - %s",
            response.status,
            await response.text(),
        )
        return False, None

    async def test_connection(self) -> bool:
        """Test the connection to the TvOverlay device."""
        try:
            success, _ = await self._make_request("POST", ENDPOINT_NOTIFY, {})
            return success
        except TvOverlayConnectionError:
            return False

    async def send_notification(self, data: dict[str, Any]) -> bool:
        """Send a notification to the TvOverlay device."""
        success, _ = await self._make_request("POST", ENDPOINT_NOTIFY, data)
        return success

    async def send_fixed_notification(self, data: dict[str, Any]) -> bool:
        """Send a fixed notification to the TvOverlay device."""
        success, _ = await self._make_request("POST", ENDPOINT_NOTIFY_FIXED, data)
        return success

    async def clear_fixed_notification(self, notification_id: str) -> bool:
        """Clear a fixed notification by ID."""
        success, _ = await self._make_request(
            "POST",
            ENDPOINT_NOTIFY_FIXED,
            {"id": notification_id, "visible": False},
        )
        return success

    async def set_overlay(self, data: dict[str, Any]) -> bool:
        """Set overlay settings."""
        success, _ = await self._make_request("POST", ENDPOINT_SET_OVERLAY, data)
        return success

    async def set_notifications(self, data: dict[str, Any]) -> bool:
        """Set notification settings."""
        success, _ = await self._make_request("POST", ENDPOINT_SET_NOTIFICATIONS, data)
        return success

    async def set_settings(self, data: dict[str, Any]) -> bool:
        """Set general settings."""
        success, _ = await self._make_request("POST", ENDPOINT_SET_SETTINGS, data)
        return success

    async def get_config(self) -> dict[str, Any] | None:
        """Get device configuration."""
        try:
            success, data = await self._make_request("GET", ENDPOINT_GET)
            return data if success else None
        except TvOverlayConnectionError:
            _LOGGER.warning(
                "Failed to get config from TvOverlay at %s:%s",
                self._host,
                self._port,
            )
            return None

    async def get_overlay(self) -> dict[str, Any] | None:
        """Get overlay settings."""
        try:
            success, data = await self._make_request("GET", "/get/overlay")
            return data if success else None
        except TvOverlayConnectionError:
            return None
