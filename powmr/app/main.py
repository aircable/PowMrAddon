from __future__ import annotations

import logging
import os
import signal
import sys
import time
from datetime import UTC, datetime
from queue import Empty, Queue
from typing import Any

from .inverter_client import InverterClient, InverterError
from .models import RuntimeConfig
from .mqtt_publish import MqttPublisher
from .parser import apply_derived_metrics, parse_qmod, parse_qpigs, parse_qpiri


LOG = logging.getLogger(__name__)

OUTPUT_SOURCE_COMMANDS = {
    "utility_solar_battery": "POP00",
    "solar_utility_battery": "POP01",
    "solar_battery_utility": "POP02",
}

CHARGER_SOURCE_COMMANDS = {
    "solar_first": "PCP01",
    "solar_and_utility": "PCP02",
    "only_solar": "PCP03",
}


def main() -> int:
    config = load_config()
    configure_logging(config.debug_logging)
    LOG.info(
        "Starting PowMr collector inverter=%s:%s mqtt=%s:%s poll=%ss",
        config.inverter_host,
        config.inverter_port,
        config.mqtt_host,
        config.mqtt_port,
        config.poll_interval_seconds,
    )

    stop_requested = False

    def handle_stop(signum: int, frame: Any) -> None:
        nonlocal stop_requested
        stop_requested = True
        LOG.info("Received signal %s, stopping", signum)

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    command_queue: Queue[tuple[str, str]] = Queue()
    inverter = InverterClient(config.inverter_host, config.inverter_port)
    mqtt = MqttPublisher(config, lambda object_id, value: command_queue.put((object_id, value)))
    mqtt.connect()
    mqtt.publish_availability(True)
    health = initial_health_state()
    last_metrics: dict[str, object] = {}
    failover_last_attempt_monotonic = 0.0

    try:
        while not stop_requested:
            started = time.monotonic()
            try:
                process_pending_commands(command_queue, inverter, mqtt, health)
                metrics = collect_metrics(inverter)
                health["link_ok"] = True
                health["telemetry_stale"] = False
                health["last_successful_poll"] = now_iso()
                health["last_error"] = ""
                last_metrics = metrics

                if health["failover_pending"]:
                    if apply_pending_failover(inverter, metrics, health, config):
                        last_metrics = collect_metrics(inverter)
                        metrics = last_metrics
                        health["failover_pending"] = False
                        health["failover_applied"] = True
                    else:
                        failover_last_attempt_monotonic = time.monotonic()

                mqtt.publish_state(build_state_payload(last_metrics, health))
                LOG.debug("Published metrics: %s", build_state_payload(last_metrics, health))
            except InverterError as exc:
                LOG.warning("Inverter poll failed: %s", exc)
                mark_poll_failure(health, exc, config)
                if health["failover_pending"] and time.monotonic() - failover_last_attempt_monotonic >= 60:
                    try:
                        apply_failover_command(inverter, config.safe_output_source_priority, health, source="stale_link")
                        refreshed = collect_metrics(inverter)
                        health["last_successful_poll"] = now_iso()
                        health["link_ok"] = True
                        health["telemetry_stale"] = False
                        health["last_error"] = ""
                        health["failover_pending"] = False
                        health["failover_applied"] = True
                        last_metrics = refreshed
                    except InverterError as failover_exc:
                        health["last_error"] = str(failover_exc)
                        failover_last_attempt_monotonic = time.monotonic()
            except Exception:
                LOG.exception("Unexpected collector failure")
                mark_poll_failure(health, RuntimeError("unexpected collector failure"), config)
            finally:
                mqtt.publish_state(build_state_payload(last_metrics, health))

            elapsed = time.monotonic() - started
            sleep_seconds = max(0.0, config.poll_interval_seconds - elapsed)
            if sleep_seconds:
                time.sleep(sleep_seconds)
    finally:
        mqtt.disconnect()

    return 0


def collect_metrics(inverter: InverterClient) -> dict[str, object]:
    qpigs = parse_qpigs(inverter.query("QPIGS"))
    qpigs.update(parse_qpiri(inverter.query("QPIRI")))
    qpigs["mode"] = parse_qmod(inverter.query("QMOD"))
    return apply_derived_metrics(qpigs)


def process_pending_commands(command_queue: Queue[tuple[str, str]], inverter: InverterClient, mqtt: MqttPublisher, health: dict[str, object]) -> None:
    while True:
        try:
            object_id, value = command_queue.get_nowait()
        except Empty:
            return

        command = map_command(object_id, value)
        LOG.info("Applying inverter command %s for %s=%s", command, object_id, value)
        try:
            inverter.query(command)
        except InverterError as exc:
            LOG.warning("Inverter rejected command %s: %s", command, exc)
            update_command_health(health, object_id, value, f"error: {exc}")
            continue

        refreshed = collect_metrics(inverter)
        health["failover_applied"] = False
        update_command_health(health, object_id, value, "applied")
        mqtt.publish_state(build_state_payload(refreshed, health))
        LOG.info("Applied inverter command %s successfully", command)


def map_command(object_id: str, value: str) -> str:
    if object_id == "output_source_priority":
        if value not in OUTPUT_SOURCE_COMMANDS:
            raise InverterError(f"Unsupported output source priority: {value}")
        return OUTPUT_SOURCE_COMMANDS[value]
    if object_id == "charger_source_priority":
        if value not in CHARGER_SOURCE_COMMANDS:
            raise InverterError(f"Unsupported charger source priority: {value}")
        return CHARGER_SOURCE_COMMANDS[value]
    raise InverterError(f"Unsupported command target: {object_id}")


def configure_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def load_config() -> RuntimeConfig:
    return RuntimeConfig(
        inverter_host=require_env("POWMR_INVERTER_HOST"),
        inverter_port=int(require_env("POWMR_INVERTER_PORT")),
        poll_interval_seconds=int(require_env("POWMR_POLL_INTERVAL_SECONDS")),
        stale_link_seconds=int(require_env("POWMR_STALE_LINK_SECONDS")),
        mqtt_host=require_env("POWMR_MQTT_HOST"),
        mqtt_port=int(require_env("POWMR_MQTT_PORT")),
        mqtt_username=os.getenv("POWMR_MQTT_USERNAME", ""),
        mqtt_password=os.getenv("POWMR_MQTT_PASSWORD", ""),
        mqtt_topic_prefix=require_env("POWMR_MQTT_TOPIC_PREFIX"),
        device_name=require_env("POWMR_DEVICE_NAME"),
        device_id=require_env("POWMR_DEVICE_ID"),
        debug_logging=os.getenv("POWMR_DEBUG_LOGGING", "false").lower() in {"1", "true", "yes", "on"},
        safe_output_source_priority=require_env("POWMR_SAFE_OUTPUT_SOURCE_PRIORITY"),
    )


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is missing")
    return value


def initial_health_state() -> dict[str, object]:
    return {
        "link_ok": False,
        "telemetry_stale": False,
        "failover_pending": False,
        "failover_applied": False,
        "last_successful_poll": None,
        "last_command_at": None,
        "last_command_target": "",
        "last_command_value": "",
        "last_command_result": "",
        "last_error": "",
    }


def build_state_payload(metrics: dict[str, object], health: dict[str, object]) -> dict[str, object]:
    payload = dict(metrics)
    payload.update(health)
    return payload


def mark_poll_failure(health: dict[str, object], exc: Exception, config: RuntimeConfig) -> None:
    health["link_ok"] = False
    health["last_error"] = str(exc)
    last_success_iso = health.get("last_successful_poll")
    if not last_success_iso:
        return
    try:
        last_success = datetime.fromisoformat(str(last_success_iso).replace("Z", "+00:00"))
    except ValueError:
        return
    age_seconds = (datetime.now(UTC) - last_success).total_seconds()
    if age_seconds >= config.stale_link_seconds:
        health["telemetry_stale"] = True
        health["failover_pending"] = True


def update_command_health(health: dict[str, object], target: str, value: str, result: str) -> None:
    health["last_command_at"] = now_iso()
    health["last_command_target"] = target
    health["last_command_value"] = value
    health["last_command_result"] = result


def apply_pending_failover(inverter: InverterClient, metrics: dict[str, object], health: dict[str, object], config: RuntimeConfig) -> bool:
    desired = config.safe_output_source_priority
    current = str(metrics.get("output_source_priority", ""))
    if current == desired:
        update_command_health(health, "output_source_priority", desired, "already_safe")
        return True
    apply_failover_command(inverter, desired, health, source="stale_link_recovery")
    return True


def apply_failover_command(inverter: InverterClient, desired: str, health: dict[str, object], source: str) -> None:
    command = OUTPUT_SOURCE_COMMANDS[desired]
    LOG.warning("Applying safe failover command %s because %s", command, source)
    inverter.query(command)
    update_command_health(health, "output_source_priority", desired, f"failover_applied:{source}")


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    sys.exit(main())
