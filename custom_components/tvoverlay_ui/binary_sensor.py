"""Binary sensor platform for TvOverlay."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import TvOverlayEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TvOverlay binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_name = data["name"]

    async_add_entities([
        TvOverlayConnectivitySensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            device_name=device_name,
        )
    ])


class TvOverlayConnectivitySensor(TvOverlayEntity, BinarySensorEntity):
    """Binary sensor for TvOverlay connectivity status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "connectivity"

    def __init__(
        self,
        coordinator,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the connectivity sensor."""
        super().__init__(coordinator, entry_id, device_name)
        self._attr_unique_id = f"{entry_id}_connectivity"

    @property
    def is_on(self) -> bool:
        """Return true if the device is connected."""
        return self.coordinator.available
