"""Lock platform for Nest Protect."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityDescription
from homeassistant.helpers.entity import EntityCategory

from . import HomeAssistantNestProtectData
from .const import DOMAIN, LOGGER
from .entity import NestDescriptiveEntity


@dataclass
class NestProtectLockDescriptionMixin:
    """Define an entity description mixin for select entities."""

    # options: list[str]
    # select_option: Callable[[str, Callable[..., Awaitable[None]]], Awaitable[None]]


@dataclass
class NestProtectLockDescription(
    LockEntityDescription, NestProtectLockDescriptionMixin
):
    """Class to describe an Nest Protect Lock."""


# BRIGHTNESS_TO_PRESET: dict[str, str] = {1: "low", 2: "medium", 3: "high"}

# PRESET_TO_BRIGHTNESS = {v: k for k, v in BRIGHTNESS_TO_PRESET.items()}

LOCK_DESCRIPTIONS: list[LockEntityDescription] = [
    NestProtectLockDescription(
        name="Locked",
        key="locked",
        entity_category=EntityCategory.CONFIG,
        icon="mdi:lock",
    ),
    NestProtectLockDescription(
        key="unlocked",
        name="Unlocked",
        entity_category=EntityCategory.CONFIG,
        icon="mdi:lock-open",
    ),
]


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the Nest Protect Lock from a config entry."""

    data: HomeAssistantNestProtectData = hass.data[DOMAIN][entry.entry_id]
    entities: list[NestProtectLock] = []

    SUPPORTED_KEYS = {
        description.key: description for description in LOCK_DESCRIPTIONS
    }

    for device in data.devices.values():
        for key in device.value:
            if description := SUPPORTED_KEYS.get(key):
                entities.append(
                    NestProtectLock(device, description, data.areas, data.client)
                )

    async_add_devices(entities)


class NestProtectLock(NestDescriptiveEntity, LockEntity):
    """Representation of a Nest Protect Lock."""

    entity_description: NestProtectLockDescription

    @property
    def is_locked(self) -> bool | None:
        """Return True if entity is locked."""
        state = self.bucket.value.get(self.entity_description.key)

        return state

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the entity."""
        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": {
                    self.entity_description.key: True,
                },
            }
        ]

        if not self.client.nest_session or self.client.nest_session.is_expired():

            if not self.client.auth or self.client.auth.is_expired():
                await self.client.get_access_token()

            await self.client.authenticate(self.client.auth.access_token)

        result = await self.client.update_objects(
            self.client.nest_session.access_token,
            self.client.nest_session.userid,
            self.client.transport_url,
            objects,
        )

        LOGGER.debug(result)

    async def async_unlocked(self, **kwargs: Any) -> None:
        """Unlock the entity."""
        objects = [
            {
                "object_key": self.bucket.object_key,
                "op": "MERGE",
                "value": {
                    self.entity_description.key: False,
                },
            }
        ]

        if not self.client.nest_session or self.client.nest_session.is_expired():

            if not self.client.auth or self.client.auth.is_expired():
                await self.client.get_access_token()

            await self.client.authenticate(self.client.auth.access_token)

        result = await self.client.update_objects(
            self.client.nest_session.access_token,
            self.client.nest_session.userid,
            self.client.transport_url,
            objects,
        )

        LOGGER.debug(result)
