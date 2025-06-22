import logging
from homeassistant.core import HomeAssistant, ServiceCall
from .time_sync import sync_clock_time

_LOGGER = logging.getLogger(__name__)
DOMAIN = "xiaomi_clock_sync"

async def async_setup(hass: HomeAssistant, config: dict):
    async def handle_sync_time(call: ServiceCall):
        macs = call.data.get("macs")
        if not macs:
            _LOGGER.error("MAC addresses are required to sync time.")
            return
        if isinstance(macs, str):
            macs = [macs]
        for mac in macs:
            await sync_clock_time(mac)

    hass.services.async_register(DOMAIN, "sync_time", handle_sync_time)
    return True
