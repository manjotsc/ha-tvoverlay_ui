"""Switch platform for TvOverlay."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import TvOverlayEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class TvOverlaySwitchEntityDescription(SwitchEntityDescription):
    """Describes TvOverlay switch entity."""

    api_key: str
    endpoint: str  # "notifications", "overlay", or "settings"
    data_key: str  # Key in coordinator data


SWITCH_DESCRIPTIONS: tuple[TvOverlaySwitchEntityDescription, ...] = (
    TvOverlaySwitchEntityDescription(
        key="display_clock",
        translation_key="display_clock",
        icon="mdi:clock-outline",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        api_key="clockOverlayVisibility",
        endpoint="overlay",
        data_key="overlay",
    ),
    TvOverlaySwitchEntityDescription(
        key="display_notifications",
        translation_key="display_notifications",
        icon="mdi:message-badge-outline",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        api_key="displayNotifications",
        endpoint="notifications",
        data_key="notifications",
    ),
    TvOverlaySwitchEntityDescription(
        key="display_fixed_notifications",
        translation_key="display_fixed_notifications",
        icon="mdi:pin-outline",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        api_key="displayFixedNotifications",
        endpoint="notifications",
        data_key="notifications",
    ),
    TvOverlaySwitchEntityDescription(
        key="pixel_shift",
        translation_key="pixel_shift",
        icon="mdi:television-shimmer",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        api_key="pixelShift",
        endpoint="settings",
        data_key="settings",
    ),
    TvOverlaySwitchEntityDescription(
        key="debug_mode",
        translation_key="debug_mode",
        icon="mdi:bug-outline",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.DIAGNOSTIC,
        api_key="displayDebug",
        endpoint="settings",
        data_key="settings",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TvOverlay switches."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_name = data["name"]

    entities = [
        TvOverlaySwitch(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            device_name=device_name,
            description=description,
            client=data["client"],
        )
        for description in SWITCH_DESCRIPTIONS
    ]

    async_add_entities(entities)


class TvOverlaySwitch(TvOverlayEntity, SwitchEntity):
    """Representation of a TvOverlay switch."""

    entity_description: TvOverlaySwitchEntityDescription

    def __init__(
        self,
        coordinator,
        entry_id: str,
        device_name: str,
        description: TvOverlaySwitchEntityDescription,
        client,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, entry_id, device_name)
        self.entity_description = description
        self._client = client
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self.coordinator.data is None:
            return None
        data_section = self.coordinator.data.get(self.entity_description.data_key, {})
        value = data_section.get(self.entity_description.api_key)
        if value is None:
            return None
        # Clock visibility uses 0-95 range instead of boolean
        if self.entity_description.key == "display_clock":
            return value > 0
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._set_state(False)

    async def _set_state(self, state: bool) -> None:
        """Set the switch state."""
        # Clock visibility uses 0-95 range instead of boolean
        if self.entity_description.key == "display_clock":
            value = 95 if state else 0
        else:
            value = state

        data = {self.entity_description.api_key: value}

        if self.entity_description.endpoint == "notifications":
            success = await self._client.set_notifications(data)
        elif self.entity_description.endpoint == "overlay":
            success = await self._client.set_overlay(data)
        else:  # settings
            success = await self._client.set_settings(data)

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(
                "Failed to set %s to %s",
                self.entity_description.key,
                state,
            )
