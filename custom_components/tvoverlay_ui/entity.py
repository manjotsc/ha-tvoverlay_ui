"""Base entity for TvOverlay."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import TvOverlayCoordinator


class TvOverlayEntity(CoordinatorEntity["TvOverlayCoordinator"]):
    """Base class for TvOverlay entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TvOverlayCoordinator,
        entry_id: str,
        device_name: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._device_name = device_name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
            manufacturer="TvOverlay",
            model="Android TV Overlay",
            sw_version=self.coordinator.device_version,
        )
