# Repository Guidelines

## Project Structure & Module Organization
This repository is a small Home Assistant add-on for polling a PowMr inverter and publishing MQTT discovery/state updates. Core Python code lives in `app/`: `main.py` runs the collector loop, `inverter_client.py` handles TCP protocol I/O, `parser.py` decodes inverter payloads, `discovery.py` builds Home Assistant entities, and `mqtt_publish.py` manages broker I/O. Add-on packaging files sit at the repo root: `config.yaml`, `Dockerfile`, `run.sh`, and `requirements.txt`. Reference docs and release notes are in `DOCS.md` and `CHANGELOG.md`; image assets are `icon.png` and `logo.png`.

## Build, Test, and Development Commands
Create a local environment with `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`. Run the collector directly with `python -m app.main` after exporting the `POWMR_*` variables that `run.sh` normally provides. Smoke-test syntax with `python -m compileall app`. Build the add-on image with `docker build --build-arg BUILD_FROM=<ha-base-image> -t powmr-addon .`.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, type hints on public functions, and `snake_case` for modules, functions, variables, and MQTT object IDs. Keep modules focused on one responsibility and prefer small helpers over deeply nested logic. Maintain the current standard-library-first import order and keep log messages operationally useful.

## Testing Guidelines
There is no committed automated test suite yet. For changes in parsing, protocol handling, or MQTT payloads, add focused tests under a future `tests/` package when practical; otherwise, at minimum run `python -m compileall app` and validate against a live inverter or recorded payloads. Name new tests after behavior, for example `test_parse_qpiri_decodes_output_source_priority`.

## Commit & Pull Request Guidelines
Git history is not available in this checkout, so follow the repository’s changelog style: concise, action-first summaries such as `Add stale-link recovery logging` or `Fix charger source priority mapping`. Keep commits scoped to one behavior change. Pull requests should include the user-visible effect, any config or MQTT topic changes, and a short validation note; include screenshots only when Home Assistant UI artifacts changed.

## Configuration & Release Notes
When changing runtime options, update both `config.yaml` defaults/schema and the corresponding environment handling in `run.sh` and `app/main.py`. Record shipped behavior changes in `CHANGELOG.md` before release.
