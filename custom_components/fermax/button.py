"""Button entities for visible Fermax doors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import FermaxApi
from .const import DOMAIN
from .coordinator import FermaxCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create door buttons from visible pairings."""
    coordinator: FermaxCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[FermaxDoorButton] = []
    for pairing in coordinator.data or []:
        device_id: str = pairing.get("deviceId", "")
        pairing_type: str = pairing.get("type", "WIFI")
        unit_id: str = pairing.get("deviceId", "")
        pairing_id: str = pairing.get("id", device_id)
        tag: str = pairing.get("tag") or "Fermax"

        for door_key, door in pairing.get("accessDoorMap", {}).items():
            if not door.get("visible"):
                continue

            title: str = door.get("title") or door_key.capitalize()
            access_id: dict[str, int] = door["accessId"]

            entities.append(
                FermaxDoorButton(
                    api=coordinator.api,
                    pairing_id=pairing_id,
                    device_id=device_id,
                    pairing_type=pairing_type,
                    unit_id=unit_id,
                    tag=tag,
                    door_key=door_key,
                    title=title,
                    access_id=access_id,
                )
            )

    async_add_entities(entities)


class FermaxDoorButton(ButtonEntity):
    """Button that opens a Fermax door when pressed."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:door-open"

    def __init__(
        self,
        api: FermaxApi,
        pairing_id: str,
        device_id: str,
        pairing_type: str,
        unit_id: str,
        tag: str,
        door_key: str,
        title: str,
        access_id: dict[str, int],
    ) -> None:
        self._api = api
        self._device_id = device_id
        self._pairing_type = pairing_type
        self._unit_id = unit_id
        self._access_id = access_id

        self._attr_name = title
        self._attr_unique_id = f"{pairing_id}_{door_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, pairing_id)},
            name=tag,
            manufacturer="Fermax",
            model="Duox Me",
        )

    async def async_press(self) -> None:
        """Open the door when pressing the button."""
        _LOGGER.debug(
            "Opening door '%s' (block=%s, subblock=%s, number=%s)",
            self._attr_name,
            self._access_id.get("block"),
            self._access_id.get("subblock"),
            self._access_id.get("number"),
        )
        await self._api.open_door(
            device_id=self._device_id,
            pairing_type=self._pairing_type,
            unit_id=self._unit_id,
            access_id=self._access_id,
        )
