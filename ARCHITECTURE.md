# PowMr Add-on Architecture

## Scope

`powmr` is a Home Assistant local add-on that:

1. Connects to PowMr inverter through AIRcable MiniP5 TCP bridge.
2. Polls inverter telemetry and settings at fixed interval.
3. Publishes Home Assistant MQTT discovery entities.
4. Accepts writable MQTT control updates for inverter priorities.
5. Exposes link-health/stale telemetry diagnostics for automations.

## Runtime Model

- Entrypoint: `run.sh` (bashio + with-contenv)
- App module: `app.main`
- Transport: TCP to bridge (`inverter_host:inverter_port`)
- Broker: MQTT service discovery from Supervisor (fallback to manual config)

## Key Components

- `app/inverter_client.py`: TCP command/response I/O
- `app/parser.py`: PowMr frame parsing and value extraction
- `app/discovery.py`: MQTT discovery payload generation
- `app/mqtt_publish.py`: MQTT publish/command handling
- `app/models.py`: typed configuration/state structs
- `app/main.py`: poll loop, stale detection, orchestration

## Configuration Surface

From `powmr/config.yaml`:

- Inverter endpoint (`inverter_host`, `inverter_port`)
- Poll/stale timings (`poll_interval_seconds`, `stale_link_seconds`)
- MQTT endpoint/credentials/topic prefix
- Device metadata (`device_name`, `device_id`)
- Safe fallback output priority (`safe_output_source_priority`)
- Debug logging

## Entity & Automation Intent

Designed to support:

- Solar/power dashboards (`solar_flow.yaml`)
- Peak-rate window automations
- Link-stale failover to safe inverter output-source priority
- Last command/result diagnostics

## Publish Model

This repository is a Home Assistant **Add-on Repository** (not HACS integration). Required files:

- `repository.yaml` at repository root
- Add-on directory `powmr/` with `config.yaml`, `Dockerfile`, `run.sh`, code, assets

