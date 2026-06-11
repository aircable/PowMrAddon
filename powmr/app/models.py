from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    inverter_host: str
    inverter_port: int
    poll_interval_seconds: int
    stale_link_seconds: int
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    mqtt_topic_prefix: str
    device_name: str
    device_id: str
    debug_logging: bool
    safe_output_source_priority: str
