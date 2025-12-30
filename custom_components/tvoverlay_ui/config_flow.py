"""Config flow for TvOverlay integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithConfigEntry,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TvOverlayApiClient, TvOverlayConnectionError
from .const import CONF_DEVICE_IDENTIFIER, DEFAULT_NAME, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Pattern for valid device identifier: lowercase letters, numbers, underscores only
VALID_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9_]+$")


def sanitize_identifier(name: str) -> str:
    """Convert a name to a valid device identifier.

    - Convert to lowercase
    - Replace spaces with underscores
    - Remove any characters that aren't lowercase letters, numbers, or underscores
    """
    # Convert to lowercase and replace spaces with underscores
    identifier = name.lower().replace(" ", "_")
    # Remove any invalid characters (keep only a-z, 0-9, _)
    identifier = re.sub(r"[^a-z0-9_]", "", identifier)
    # Remove consecutive underscores
    identifier = re.sub(r"_+", "_", identifier)
    # Remove leading/trailing underscores
    identifier = identifier.strip("_")
    return identifier or "device"


def validate_identifier(identifier: str) -> bool:
    """Check if identifier is valid (lowercase, numbers, underscores only)."""
    return bool(VALID_IDENTIFIER_PATTERN.match(identifier))


class TvOverlayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TvOverlay."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            name = user_input.get(CONF_NAME, DEFAULT_NAME)

            # Get device identifier - use provided or generate from name
            device_identifier = user_input.get(CONF_DEVICE_IDENTIFIER, "").strip()
            if not device_identifier:
                device_identifier = sanitize_identifier(name)

            # Validate device identifier
            if not validate_identifier(device_identifier):
                errors[CONF_DEVICE_IDENTIFIER] = "invalid_identifier"
            else:
                # Create unique ID from host and port
                unique_id = f"{host}:{port}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # Test connection
                session = async_get_clientsession(self.hass)
                client = TvOverlayApiClient(host, port, session)
                try:
                    if await client.test_connection():
                        return self.async_create_entry(
                            title=name,
                            data={
                                CONF_HOST: host,
                                CONF_PORT: port,
                                CONF_NAME: name,
                                CONF_DEVICE_IDENTIFIER: device_identifier,
                            },
                        )
                    else:
                        errors["base"] = "cannot_connect"
                except TvOverlayConnectionError:
                    errors["base"] = "cannot_connect"
                except Exception:  # noqa: BLE001
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Optional(CONF_DEVICE_IDENTIFIER, default=""): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithConfigEntry:
        """Get the options flow for this handler."""
        return TvOverlayOptionsFlow(config_entry)


class TvOverlayOptionsFlow(OptionsFlowWithConfigEntry):
    """Handle TvOverlay options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        # Get current values
        current_host = self.config_entry.data.get(CONF_HOST)
        current_port = self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)
        current_name = self.config_entry.data.get(CONF_NAME, DEFAULT_NAME)
        # Default identifier from device name if not set
        default_identifier = sanitize_identifier(current_name)
        current_identifier = self.config_entry.data.get(
            CONF_DEVICE_IDENTIFIER, default_identifier
        )

        if user_input is not None:
            host = user_input.get(CONF_HOST, current_host)
            port = user_input.get(CONF_PORT, current_port)
            device_identifier = user_input.get(
                CONF_DEVICE_IDENTIFIER, ""
            ).strip()

            # If device_identifier is empty, use sanitized name
            if not device_identifier:
                device_identifier = sanitize_identifier(current_name)

            # Validate device identifier
            if not validate_identifier(device_identifier):
                errors[CONF_DEVICE_IDENTIFIER] = "invalid_identifier"
            else:
                # Test connection with new settings
                session = async_get_clientsession(self.hass)
                client = TvOverlayApiClient(host, port, session)
                try:
                    if await client.test_connection():
                        # Update config entry data
                        self.hass.config_entries.async_update_entry(
                            self.config_entry,
                            data={
                                **self.config_entry.data,
                                CONF_HOST: host,
                                CONF_PORT: port,
                                CONF_DEVICE_IDENTIFIER: device_identifier,
                            },
                        )
                        return self.async_create_entry(title="", data={})
                    else:
                        errors["base"] = "cannot_connect"
                except TvOverlayConnectionError:
                    errors["base"] = "cannot_connect"
                except Exception:  # noqa: BLE001
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=current_host,
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        default=current_port,
                    ): int,
                    vol.Optional(
                        CONF_DEVICE_IDENTIFIER,
                        default=current_identifier,
                    ): str,
                }
            ),
            errors=errors,
        )
