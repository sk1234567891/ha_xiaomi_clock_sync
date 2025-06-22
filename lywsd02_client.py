import asyncio
import collections
import contextlib
import logging
import struct
import time
from datetime import datetime

from bleak import BleakClient

_LOGGER = logging.getLogger(__name__)

UUID_UNITS = 'EBE0CCBE-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_HISTORY = 'EBE0CCBC-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_TIME = 'EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_DATA = 'EBE0CCC1-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_BATTERY = 'EBE0CCC4-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_NUM_RECORDS = 'EBE0CCB9-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_RECORD_IDX = 'EBE0CCBA-7A0A-4B0C-8A1A-6FF2997DA3A6'


class SensorData(collections.namedtuple('SensorDataBase', ['temperature', 'humidity'])):
    __slots__ = ()


class Lywsd02Client:
    UNITS = {
        b'\x01': 'F',
        b'\xff': 'C',
    }
    UNITS_CODES = {
        'C': b'\xff',
        'F': b'\x01',
    }

    def __init__(self, mac, notification_timeout=5.0):
        self._mac = mac
        self._client = BleakClient(mac)
        self._notification_timeout = notification_timeout
        self._tz_offset = None
        self._data = SensorData(None, None)
        self._history_data = collections.OrderedDict()
        self._notification_event = asyncio.Event()

    @contextlib.asynccontextmanager
    async def connect(self):
        if not self._client.is_connected:
            _LOGGER.debug('Connecting to %s', self._mac)
            await self._client.connect()
        try:
            yield self
        finally:
            _LOGGER.debug('Disconnecting from %s', self._mac)
            await self._client.disconnect()

    @property
    def tz_offset(self):
        if self._tz_offset is not None:
            return self._tz_offset
        elif time.daylight:
            return -time.altzone // 3600
        else:
            return -time.timezone // 3600

    @tz_offset.setter
    def tz_offset(self, tz_offset: int):
        self._tz_offset = tz_offset

    async def get_units(self):
        async with self.connect():
            value = await self._client.read_gatt_char(UUID_UNITS)
        return self.UNITS[value]

    async def set_units(self, value):
        if value.upper() not in self.UNITS_CODES:
            raise ValueError(f"Units must be one of {list(self.UNITS_CODES)}")
        async with self.connect():
            await self._client.write_gatt_char(UUID_UNITS, self.UNITS_CODES[value.upper()], response=True)

    async def get_battery(self):
        async with self.connect():
            value = await self._client.read_gatt_char(UUID_BATTERY)
        return value[0]

    async def get_time(self):
        async with self.connect():
            value = await self._client.read_gatt_char(UUID_TIME)
        if len(value) == 5:
            ts, tz_offset = struct.unpack('Ib', value)
        else:
            ts = struct.unpack('I', value[:4])[0]
            tz_offset = 0
        return datetime.fromtimestamp(ts), tz_offset

    async def set_time(self, dt: datetime):
        data = struct.pack('Ib', int(dt.timestamp()), self.tz_offset)
        async with self.connect():
            await self._client.write_gatt_char(UUID_TIME, data, response=True)

    async def get_history_index(self):
        async with self.connect():
            value = await self._client.read_gatt_char(UUID_RECORD_IDX)
        return struct.unpack_from('I', value)[0] if value else 0

    async def set_history_index(self, idx):
        data = struct.pack('I', idx)
        async with self.connect():
            await self._client.write_gatt_char(UUID_RECORD_IDX, data, response=True)

    async def get_num_stored_entries(self):
        async with self.connect():
            value = await self._client.read_gatt_char(UUID_NUM_RECORDS)
        return struct.unpack_from('II', value)

    async def get_sensor_data(self):
        async with self.connect():
            self._notification_event.clear()
            await self._client.start_notify(UUID_DATA, self._sensor_callback)
            try:
                await asyncio.wait_for(self._notification_event.wait(), timeout=self._notification_timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"No data from device for {self._notification_timeout} seconds")
            finally:
                await self._client.stop_notify(UUID_DATA)
        return self._data

    async def get_history_data(self):
        async with self.connect():
            self._notification_event.clear()
            await self._client.start_notify(UUID_HISTORY, self._history_callback)
            try:
                while True:
                    try:
                        await asyncio.wait_for(self._notification_event.wait(), timeout=self._notification_timeout)
                        self._notification_event.clear()
                    except asyncio.TimeoutError:
                        break
            finally:
                await self._client.stop_notify(UUID_HISTORY)
        return self._history_data

    def _sensor_callback(self, sender, data):
        temperature, humidity = struct.unpack_from('hB', data)
        self._data = SensorData(temperature=temperature / 100, humidity=humidity)
        self._notification_event.set()

    def _history_callback(self, sender, data):
        idx, ts, max_temp, max_hum, min_temp, min_hum = struct.unpack_from('<IIhBhB', data)
        self._history_data[idx] = [
            datetime.fromtimestamp(ts),
            min_temp / 100,
            min_hum,
            max_temp / 100,
            max_hum,
        ]
        self._notification_event.set()
