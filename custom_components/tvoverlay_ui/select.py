"""Select platform for TvOverlay."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, VALID_CORNERS, VALID_SHAPES
from .entity import TvOverlayEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TvOverlay select entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_name = data["name"]

    entities = [
        TvOverlayCornerSelect(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            device_name=device_name,
            entry_data=data,
            client=data["client"],
        ),
        TvOverlayShapeSelect(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            device_name=device_name,
            entry_data=data,
            client=data["client"],
        ),
    ]

    async_add_entities(entities)


class TvOverlayCornerSelect(TvOverlayEntity, SelectEntity):
    """Select entity for hot corner."""

    _attr_translation_key = "hot_corner"
    _attr_icon = "mdi:arrow-top-right"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator,
        entry_id: str,
        device_name: str,
        entry_data: dict,
        client,
    ) -> None:
        """Initialize the corner select entity."""
        super().__init__(coordinator, entry_id, device_name)
        self._entry_data = entry_data
        self._client = client
        self._attr_unique_id = f"{entry_id}_hot_corner"
        self._attr_options = VALID_CORNERS

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        if self.coordinator.data is None:
            return self._entry_data.get("hot_corner", "top_start")
        overlay = self.coordinator.data.get("overlay", {})
        corner = overlay.get("hotCorner", "top_start")
        return corner if corner in VALID_CORNERS else "top_start"

    async def async_select_option(self, option: str) -> None:
        """Change the selected corner."""
        success = await self._client.set_overlay({"hotCorner": option})
        if success:
            self._entry_data["hot_corner"] = option
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set hot corner to %s", option)


class TvOverlayShapeSelect(TvOverlayEntity, SelectEntity):
    """Select entity for default shape."""

    _attr_translation_key = "default_shape"
    _attr_icon = "mdi:shape-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator,
        entry_id: str,
        device_name: str,
        entry_data: dict,
        client,
    ) -> None:
        """Initialize the shape select entity."""
        super().__init__(coordinator, entry_id, device_name)
        self._entry_data = entry_data
        self._client = client
        self._attr_unique_id = f"{entry_id}_default_shape"
        self._attr_options = VALID_SHAPES

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        return self._entry_data.get("default_shape", "rounded")

    async def async_select_option(self, option: str) -> None:
        """Change the selected shape."""
        # This is a local setting used as default for fixed notifications
        self._entry_data["default_shape"] = option
        self.async_write_ha_state()
