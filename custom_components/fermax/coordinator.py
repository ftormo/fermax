"""Data coordinator for Fermax."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FermaxApi, FermaxApiError

_LOGGER = logging.getLogger(__name__)

# Doors do not change frequently; refresh once per hour.
SCAN_INTERVAL = timedelta(hours=1)


class FermaxCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator that fetches the pairing list from the Fermax API."""

    def __init__(self, hass: HomeAssistant, api: FermaxApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Fermax",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            return await self.api.get_pairings()
        except FermaxApiError as err:
            raise UpdateFailed(f"Error fetching Fermax data: {err}") from err
