from __future__ import annotations

from typing import Any

from .models import RuntimeConfig


def build_discovery_messages(config: RuntimeConfig) -> list[tuple[str, dict[str, Any]]]:
    state_topic = f"{config.mqtt_topic_prefix}/state"
    availability_topic = f"{config.mqtt_topic_prefix}/status"
    device = {
        "identifiers": [config.device_id],
        "manufacturer": "PowMr",
        "model": "POS-HVM6.2M-48V-N",
        "name": config.device_name,
    }

    def sensor_payload(
        object_id: str,
        name: str,
        value_key: str,
        unit: str | None = None,
        device_class: str | None = None,
        state_class: str | None = None,
        icon: str | None = None,
        component: str = "sensor",
        extra: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        payload: dict[str, Any] = {
            "name": name,
            "unique_id": f"{config.device_id}_{object_id}",
            "state_topic": state_topic,
            "availability_topic": availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",
            "value_template": f"{{{{ value_json.{value_key} }}}}",
            "device": device,
        }
        if unit:
            payload["unit_of_measurement"] = unit
        if device_class:
            payload["device_class"] = device_class
        if state_class:
            payload["state_class"] = state_class
        if icon:
            payload["icon"] = icon
        if extra:
            payload.update(extra)
        topic = f"homeassistant/{component}/{config.device_id}/{object_id}/config"
        return topic, payload

    def binary_sensor_payload(object_id: str, name: str, value_key: str) -> tuple[str, dict[str, Any]]:
        return sensor_payload(
            object_id=object_id,
            name=name,
            value_key=value_key,
            component="binary_sensor",
            extra={
                "value_template": f"{{{{ 'ON' if value_json.{value_key} else 'OFF' }}}}",
                "payload_on": "ON",
                "payload_off": "OFF",
            },
        )

    def select_payload(object_id: str, name: str, value_key: str, options: list[str], icon: str | None = None) -> tuple[str, dict[str, Any]]:
        payload: dict[str, Any] = {
            "name": name,
            "unique_id": f"{config.device_id}_{object_id}",
            "state_topic": state_topic,
            "command_topic": f"{config.mqtt_topic_prefix}/set/{object_id}",
            "availability_topic": availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",
            "value_template": f"{{{{ value_json.{value_key} }}}}",
            "options": options,
            "device": device,
        }
        if icon:
            payload["icon"] = icon
        topic = f"homeassistant/select/{config.device_id}/{object_id}/config"
        return topic, payload

    messages = [
        sensor_payload("pv_power", "PowMr PV Power", "pv_input_power", "W", "power", "measurement"),
        sensor_payload("solar_power", "PowMr Solar Power", "solar_power", "W", "power", "measurement"),
        sensor_payload("last_successful_poll", "PowMr Last Successful Poll", "last_successful_poll", device_class="timestamp"),
        sensor_payload("last_command_at", "PowMr Last Command At", "last_command_at", device_class="timestamp"),
        sensor_payload("last_command_result", "PowMr Last Command Result", "last_command_result", icon="mdi:clipboard-check-outline"),
        sensor_payload("last_command_target", "PowMr Last Command Target", "last_command_target", icon="mdi:cursor-pointer"),
        sensor_payload("last_command_value", "PowMr Last Command Value", "last_command_value", icon="mdi:tune"),
        sensor_payload("last_error", "PowMr Last Error", "last_error", icon="mdi:alert-circle-outline"),
        sensor_payload("battery_voltage", "PowMr Battery Voltage", "battery_voltage", "V", "voltage", "measurement"),
        sensor_payload("battery_charge_current", "PowMr Battery Charge Current", "battery_charge_current", "A", "current", "measurement"),
        sensor_payload("battery_discharge_current", "PowMr Battery Discharge Current", "battery_discharge_current", "A", "current", "measurement"),
        sensor_payload("battery_power", "PowMr Battery Power", "battery_power", "W", "power", "measurement"),
        sensor_payload("battery_capacity", "PowMr Battery Capacity", "battery_capacity", "%", "battery", "measurement"),
        sensor_payload("battery_capacity_raw", "PowMr Battery Capacity Raw", "battery_capacity_raw", "%", "battery", "measurement", "mdi:battery-unknown"),
        sensor_payload("ac_output_power", "PowMr AC Output Power", "ac_output_active_power", "W", "power", "measurement"),
        sensor_payload("house_consumption", "PowMr House Consumption", "house_consumption", "W", "power", "measurement"),
        sensor_payload("load_percent", "PowMr Load Percent", "load_percent", "%", None, "measurement", "mdi:gauge"),
        sensor_payload("grid_voltage", "PowMr Grid Voltage", "grid_voltage", "V", "voltage", "measurement"),
        sensor_payload("grid_frequency", "PowMr Grid Frequency", "grid_frequency", "Hz", "frequency", "measurement"),
        sensor_payload("ac_output_voltage", "PowMr AC Output Voltage", "ac_output_voltage", "V", "voltage", "measurement"),
        sensor_payload("ac_output_frequency", "PowMr AC Output Frequency", "ac_output_frequency", "Hz", "frequency", "measurement"),
        sensor_payload("inverter_temperature", "PowMr Inverter Temperature", "inverter_temperature", "°C", "temperature", "measurement"),
        sensor_payload("pv_input_voltage", "PowMr PV Input Voltage", "pv_input_voltage", "V", "voltage", "measurement"),
        sensor_payload("pv_input_current", "PowMr PV Input Current", "pv_input_current_for_battery", "A", "current", "measurement"),
        sensor_payload("mode", "PowMr Mode", "mode", icon="mdi:state-machine"),
        select_payload(
            "output_source_priority",
            "PowMr Output Source Priority",
            "output_source_priority",
            ["utility_solar_battery", "solar_utility_battery", "solar_battery_utility"],
            "mdi:transmission-tower-export",
        ),
        select_payload(
            "charger_source_priority",
            "PowMr Charger Source Priority",
            "charger_source_priority",
            ["solar_first", "solar_and_utility", "only_solar"],
            "mdi:battery-charging",
        ),
        sensor_payload("input_voltage_range", "PowMr Input Voltage Range", "input_voltage_range", icon="mdi:sine-wave"),
        sensor_payload("battery_type", "PowMr Battery Type", "battery_type", icon="mdi:car-battery"),
        sensor_payload("machine_type", "PowMr Machine Type", "machine_type", icon="mdi:chip"),
        sensor_payload("output_mode", "PowMr Output Mode", "output_mode", icon="mdi:power-plug"),
        sensor_payload("max_ac_charging_current", "PowMr Max AC Charging Current", "max_ac_charging_current", "A", "current", "measurement"),
        sensor_payload("max_charging_current", "PowMr Max Charging Current", "max_charging_current", "A", "current", "measurement"),
        sensor_payload("battery_recharge_voltage", "PowMr Battery Recharge Voltage", "battery_recharge_voltage", "V", "voltage", "measurement"),
        sensor_payload("battery_redischarge_voltage", "PowMr Battery Redischarge Voltage", "battery_redischarge_voltage", "V", "voltage", "measurement"),
        sensor_payload("battery_under_voltage", "PowMr Battery Under Voltage", "battery_under_voltage", "V", "voltage", "measurement"),
        sensor_payload("battery_bulk_charge_voltage", "PowMr Battery Bulk Charge Voltage", "battery_bulk_charge_voltage", "V", "voltage", "measurement"),
        sensor_payload("battery_float_charge_voltage", "PowMr Battery Float Charge Voltage", "battery_float_charge_voltage", "V", "voltage", "measurement"),
        sensor_payload("status_raw", "PowMr Device Status", "device_status", icon="mdi:information-outline"),
        sensor_payload("status2_raw", "PowMr Device Status 2", "device_status_2", icon="mdi:information-outline"),
        binary_sensor_payload("link_ok", "PowMr Link OK", "link_ok"),
        binary_sensor_payload("telemetry_stale", "PowMr Telemetry Stale", "telemetry_stale"),
        binary_sensor_payload("failover_pending", "PowMr Failover Pending", "failover_pending"),
        binary_sensor_payload("failover_applied", "PowMr Failover Applied", "failover_applied"),
        binary_sensor_payload("load_on", "PowMr Load Enabled", "load_on"),
        binary_sensor_payload("charging_on", "PowMr Charging Enabled", "charging_on"),
        binary_sensor_payload("scc_charging_on", "PowMr SCC Charging", "scc_charging_on"),
        binary_sensor_payload("ac_charging_on", "PowMr AC Charging", "ac_charging_on"),
        binary_sensor_payload("charging_to_float", "PowMr Charging To Float", "charging_to_float"),
        binary_sensor_payload("switched_on", "PowMr Switched On", "switched_on"),
    ]
    return messages
