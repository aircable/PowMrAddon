# PowMr Inverter

This add-on polls a PowMr inverter over the validated TCP bridge path and
publishes Home Assistant MQTT discovery entities.

## Configuration

- `inverter_host`: hostname or IP of the AIRminiP5 bridge
- `inverter_port`: TCP port on the bridge, usually `3333`
- `poll_interval_seconds`: polling cadence
- `stale_link_seconds`: how long the inverter link may be stale before the add-on queues a safe fallback
- `mqtt_*`: broker settings; these are auto-filled from the MQTT service when available
- `mqtt_topic_prefix`: MQTT state/discovery prefix root for this add-on
- `device_name`: Home Assistant device name
- `device_id`: stable unique-id prefix for the device
- `safe_output_source_priority`: output source priority to restore when link health goes stale
- `debug_logging`: logs raw protocol details

## Expected sensors

The first release publishes:

- PV power
- battery voltage
- battery charge current
- battery discharge current
- battery capacity estimate
- raw inverter battery capacity
- AC output power
- AC output apparent power
- load percent
- AC input/output voltage and frequency
- inverter mode
- output source priority
- charger source priority
- input voltage range
- battery type
- max AC charging current
- max charging current
- inverter temperature
- battery power
- link health and stale telemetry state
- last successful poll timestamp
- last command target/value/result
- last collector error

## Notes

- Use a static IP for the bridge if `.local` name resolution is unreliable.
- The add-on publishes MQTT discovery payloads automatically at startup.
- The add-on now exposes writable Home Assistant `select` entities for output
  and charger source priority. If the inverter firmware rejects a change, the
  add-on logs the rejection and keeps the current reported state.
- When inverter polling stays stale longer than `stale_link_seconds`, the
  add-on marks telemetry stale and queues a safe output-source fallback for the
  next successful reconnection attempt.
- The published `battery_capacity` sensor is an estimated reserve percentage
  based on battery voltage plus charge/discharge current compensation. The raw
  inverter-reported percentage is also exposed as `battery_capacity_raw`.
