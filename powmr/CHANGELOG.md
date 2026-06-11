# Changelog

## 0.1.16

- Fixed the add-on build metadata so Supervisor provides a valid Home Assistant base image during local builds.
- Added an amd64 Dockerfile fallback base image to prevent blank `BUILD_FROM` failures during rebuilds.

## 0.1.15

- Fixed MQTT discovery for `inverter_temperature` to publish `°C`, which Home Assistant accepts for `device_class: temperature`.
- Fixed the Hot Water Heater YAML dashboard structure so Home Assistant can render it as a proper sidebar dashboard.

## 0.1.14

- Switched the Home Assistant peak-window start and early-revert protection from battery percentage to battery voltage, using `42.5V` as the reserve threshold.
- Bumped the add-on version so Home Assistant detects the updated configuration bundle.

## 0.1.13

- Replaced the published `battery_capacity` value with a voltage/current-compensated reserve estimate and added `battery_capacity_raw` for the inverter's original percentage.
- Bumped the add-on version so Home Assistant detects the updated build.

## 0.1.12

- Added a printable `BatCheckSheet.md` battery-settings checklist for the PowMr system documentation.

## 0.1.11

- Tightened charger source priority handling to match the inverter manual with only `solar_first`, `solar_and_utility`, and `only_solar`.
- Updated the charger priority decoder to treat both inverter codes `0` and `1` as `solar_first` for model compatibility.

## 0.1.10

- Added PowMr health entities to the Solar Flow dashboard for live observability.
- Added a WhatsApp recovery message when the PowMr link returns and telemetry resumes.

## 0.1.9

- Added a Home Assistant `rest_command` for OpenClaw WhatsApp alerts through the local gateway.
- Wired the PowMr stale-link automation to send a WhatsApp alert to the configured self-chat target.

## 0.1.8

- Added Home Assistant stale-link alert and recovery automations tied to the new PowMr health entities.
- Added an immediate HA-side safe fallback request when telemetry is marked stale.

## 0.1.7

- Added PowMr health telemetry for link status, stale telemetry, last successful poll, last command details, and last error.
- Changed MQTT availability semantics so the collector stays available while reporting inverter link failures as explicit health entities.
- Added configurable stale-link failover that queues a safe output source priority when telemetry has been stale beyond the configured threshold.

## 0.1.6

- Corrected the Solar Flow dashboard card schema to use the signed battery power sensor directly.
- Removed misleading estimated grid flow from the main dashboard view because the inverter does not expose a direct grid power reading.
- Split solar balance into clamped `solar_surplus` and `solar_deficit` template sensors to avoid negative surplus values.

## 0.1.5

- Added Home Assistant peak-rate battery window automations for 4 PM to 9 PM operation.
- Added derived template sensors for dashboard use, including battery charge/discharge split and estimated grid import/export.
- Added a YAML Solar Flow dashboard wired to the PowMr MQTT entities and Power Flow Card Plus.

## 0.1.4

- Fixed MQTT command queue handling for writable priority controls.
- Prevented the control loop from crashing when Home Assistant sent `select` commands.

## 0.1.1

- Refined add-on metadata and description.
- Added direct TCP polling for live inverter telemetry.
- Added `QPIRI` polling for current inverter settings such as output and charger priorities.
- Added MQTT discovery entities for dashboard-critical sensors and current inverter configuration.
- Added add-on artwork (`icon.png`, `logo.png`).

## 0.1.0

- Initial local add-on scaffold for PowMr inverter telemetry.
