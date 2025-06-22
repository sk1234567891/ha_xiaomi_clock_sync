# Xiaomi Clock Time Sync

This Home Assistant custom component allows you to synchronize the time on one or more Xiaomi LYWSD02 Bluetooth clocks directly from Home Assistant.

## Features

- Sync the time on multiple Xiaomi LYWSD02 clocks with a single service call.
- Uses Bluetooth (via the `bleak` library) to communicate with devices.
- Simple service for manual or automated time sync.

## Installation

1. **Copy the files**  
   Place the `xiaomi_clock_sync` folder in your Home Assistant `custom_components` directory.

2. **Enable in configuration.yaml file**
   add the following line to `configuration.yaml`:

   ```yaml
   xiaomi_clock_sync:
   ```

3. **Restart Home Assistant**  
   After copying the files, restart Home Assistant to load the new component.

> **Note:**  
> You do **not** need to install the `bleak` library manually. Home Assistant will automatically install all required dependencies as specified in `manifest.json`.

## Configuration

add the following line to `configuration.yaml`:

```yaml
xiaomi_clock_sync:
```

## Usage

### Service: `xiaomi_clock_sync.sync_time`

Sync the time on one or more Xiaomi LYWSD02 clocks.

#### Service Data

| Field | Type   | Required | Description                                 |
|-------|--------|----------|---------------------------------------------|
| macs  | list   | Yes      | List of MAC addresses of the clocks to sync |

**Example:**

```yaml
service: xiaomi_clock_sync.sync_time
data:
  macs:
    - "A4:C1:38:XX:XX:XX"
    - "3F:5B:7D:XX:XX:XX"
```

You can call this service from Developer Tools, automations, or scripts.

## Troubleshooting

- Ensure your Home Assistant host has a working Bluetooth adapter.
- The clocks must be powered on and within Bluetooth range.

## Credits

- Based on [h4/lywsd02](https://github.com/h4/lywsd02)
- Uses the [bleak](https://github.com/hbldh/bleak) Bluetooth library

## License

MIT License
