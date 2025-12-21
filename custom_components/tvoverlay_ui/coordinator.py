"""DataUpdateCoordinator for TvOverlay."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TvOverlayApiClient, TvOverlayConnectionError

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class TvOverlayCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching TvOverlay data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TvOverlayApiClient,
        device_name: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"TvOverlay {device_name}",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self._device_name = device_name
        self._device_version: str | None = None
        self._available = True

    @property
    def device_version(self) -> str | None:
        """Return device software version."""
        return self._device_version

    @property
    def available(self) -> bool:
        """Return if device is available."""
        return self._available

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from TvOverlay device."""
        try:
            config = await self.client.get_config()
            if config is None:
                self._available = False
                raise UpdateFailed("Failed to fetch config from device")

            self._available = True

            # Parse the response
            result = config.get("result", config)

            # Extract device version
            status = result.get("status", {})
            if "version" in status:
                self._device_version = str(status["version"])

            # Extract all relevant data
            data: dict[str, Any] = {
                "overlay": result.get("overlay", {}),
                "settings": result.get("settings", {}),
                "notifications": result.get("notifications", {}),
                "status": status,
            }

            _LOGGER.debug("Coordinator data updated: %s", data)
            return data

        except TvOverlayConnectionError as err:
            self._available = False
            raise UpdateFailed(f"Connection error: {err}") from err
        except Exception as err:
            self._available = False
            raise UpdateFailed(f"Error fetching data: {err}") from err
