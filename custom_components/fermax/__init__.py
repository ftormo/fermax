"""Fermax integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FermaxApi
from .const import CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, DOMAIN, PLATFORMS
from .coordinator import FermaxCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Fermax integration from a config entry."""
    session = async_get_clientsession(hass)

    async def _save_tokens(access_token: str, refresh_token: str) -> None:
        """Persist refreshed tokens in the config entry."""
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_ACCESS_TOKEN: access_token,
                CONF_REFRESH_TOKEN: refresh_token,
            },
        )

    api = FermaxApi(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=session,
        token_update_callback=_save_tokens,
    )

    # Restore cached tokens to avoid an unnecessary login on HA restart.
    if access_token := entry.data.get(CONF_ACCESS_TOKEN):
        api.set_tokens(
            access_token=access_token,
            refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
        )

    coordinator = FermaxCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the Fermax integration."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
