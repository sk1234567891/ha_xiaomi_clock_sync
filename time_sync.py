import datetime
import logging
from .lywsd02_client import Lywsd02Client

_LOGGER = logging.getLogger(__name__)

async def sync_clock_time(mac: str) -> None:
    now = datetime.datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        client = Lywsd02Client(mac, "lywsd02_client")  # type: ignore
        async with client.connect():
            _LOGGER.debug("Connected to device")
            await client.set_time(now)  # Set the system time to the device
            _LOGGER.info(f"Time set on device {mac} to {time_str}")
        _LOGGER.info(f"Time synced for {mac} at {time_str}")
    except Exception as e:
        _LOGGER.error(f"Failed to sync time for {mac}: {e}")
