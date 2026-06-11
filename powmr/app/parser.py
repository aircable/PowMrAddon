from __future__ import annotations

from typing import Any


QPIGS_FIELDS = (
    "grid_voltage",
    "grid_frequency",
    "ac_output_voltage",
    "ac_output_frequency",
    "ac_output_apparent_power",
    "ac_output_active_power",
    "load_percent",
    "bus_voltage",
    "battery_voltage",
    "battery_charge_current",
    "battery_capacity",
    "inverter_temperature",
    "pv_input_current_for_battery",
    "pv_input_voltage",
    "battery_voltage_scc",
    "battery_discharge_current",
    "device_status",
    "reserved_1",
    "reserved_2",
    "pv_input_power",
    "device_status_2",
)

QPIRI_FIELDS = (
    "ac_input_voltage",
    "ac_input_current",
    "ac_output_voltage_rating",
    "ac_output_frequency_rating",
    "ac_output_current_rating",
    "ac_output_apparent_power_rating",
    "ac_output_active_power_rating",
    "battery_voltage_rating",
    "battery_recharge_voltage",
    "battery_under_voltage",
    "battery_bulk_charge_voltage",
    "battery_float_charge_voltage",
    "battery_type",
    "max_ac_charging_current",
    "max_charging_current",
    "input_voltage_range",
    "output_source_priority",
    "charger_source_priority",
    "max_parallel_units",
    "machine_type",
    "topology",
    "output_mode",
    "battery_redischarge_voltage",
    "pv_ok_condition",
    "pv_power_balance",
)

LITHIUM_BATTERY_TYPES = {
    "pylontech",
    "shinheung",
    "weco",
    "soltaro",
    "bak",
    "lib",
    "lic",
}

LITHIUM_RESERVE_CURVE_48V = (
    (44.0, 0),
    (47.2, 5),
    (48.0, 20),
    (48.6, 30),
    (49.2, 40),
    (49.8, 50),
    (50.4, 60),
    (51.0, 70),
    (51.8, 82),
    (52.6, 92),
    (53.6, 97),
    (55.2, 100),
)

LEAD_ACID_RESERVE_CURVE_48V = (
    (42.0, 0),
    (46.8, 10),
    (47.6, 20),
    (48.4, 35),
    (49.2, 50),
    (50.0, 70),
    (50.8, 85),
    (51.6, 100),
)


def parse_qpigs(payload: str) -> dict[str, Any]:
    parts = payload.strip().split()
    if len(parts) < len(QPIGS_FIELDS):
        raise ValueError(f"Expected at least {len(QPIGS_FIELDS)} QPIGS fields, got {len(parts)}")

    raw = dict(zip(QPIGS_FIELDS, parts))
    parsed: dict[str, Any] = {
        "grid_voltage": _to_float(raw["grid_voltage"]),
        "grid_frequency": _to_float(raw["grid_frequency"]),
        "ac_output_voltage": _to_float(raw["ac_output_voltage"]),
        "ac_output_frequency": _to_float(raw["ac_output_frequency"]),
        "ac_output_apparent_power": _to_int(raw["ac_output_apparent_power"]),
        "ac_output_active_power": _to_int(raw["ac_output_active_power"]),
        "load_percent": _to_int(raw["load_percent"]),
        "bus_voltage": _to_int(raw["bus_voltage"]),
        "battery_voltage": _to_float(raw["battery_voltage"]),
        "battery_charge_current": _to_int(raw["battery_charge_current"]),
        "battery_capacity_raw": _to_int(raw["battery_capacity"]),
        "battery_capacity": _to_int(raw["battery_capacity"]),
        "inverter_temperature": _to_int(raw["inverter_temperature"]),
        "pv_input_current_for_battery": _to_float(raw["pv_input_current_for_battery"]),
        "pv_input_voltage": _to_float(raw["pv_input_voltage"]),
        "battery_voltage_scc": _to_float(raw["battery_voltage_scc"]),
        "battery_discharge_current": _to_int(raw["battery_discharge_current"]),
        "device_status": raw["device_status"],
        "reserved_1": _to_int(raw["reserved_1"]),
        "reserved_2": _to_int(raw["reserved_2"]),
        "pv_input_power": _to_int(raw["pv_input_power"]),
        "device_status_2": raw["device_status_2"],
    }
    parsed.update(_decode_device_status(parsed["device_status"]))
    parsed.update(_decode_device_status_2(parsed["device_status_2"]))
    charge_current = parsed["battery_charge_current"]
    discharge_current = parsed["battery_discharge_current"]
    net_battery_current = charge_current - discharge_current
    parsed["battery_net_current"] = net_battery_current
    parsed["battery_power"] = round(parsed["battery_voltage"] * net_battery_current, 1)
    parsed["house_consumption"] = parsed["ac_output_active_power"]
    parsed["solar_power"] = parsed["pv_input_power"]
    return parsed


def apply_derived_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    metrics["battery_capacity"] = _estimate_battery_reserve_percent(metrics)
    return metrics


def parse_qmod(payload: str) -> str:
    code = payload.strip()[:1]
    mapping = {
        "P": "power_on",
        "S": "standby",
        "L": "line",
        "B": "battery",
        "F": "fault",
        "H": "power_saving",
    }
    return mapping.get(code, code or "unknown")


def parse_qpiri(payload: str) -> dict[str, Any]:
    parts = payload.strip().split()
    if len(parts) < len(QPIRI_FIELDS):
        raise ValueError(f"Expected at least {len(QPIRI_FIELDS)} QPIRI fields, got {len(parts)}")

    raw = dict(zip(QPIRI_FIELDS, parts))
    return {
        "rating_ac_input_voltage": _to_float(raw["ac_input_voltage"]),
        "rating_ac_input_current": _to_float(raw["ac_input_current"]),
        "rating_ac_output_voltage": _to_float(raw["ac_output_voltage_rating"]),
        "rating_ac_output_frequency": _to_float(raw["ac_output_frequency_rating"]),
        "rating_ac_output_current": _to_float(raw["ac_output_current_rating"]),
        "rating_ac_output_apparent_power": _to_int(raw["ac_output_apparent_power_rating"]),
        "rating_ac_output_active_power": _to_int(raw["ac_output_active_power_rating"]),
        "rating_battery_voltage": _to_float(raw["battery_voltage_rating"]),
        "battery_recharge_voltage": _to_float(raw["battery_recharge_voltage"]),
        "battery_under_voltage": _to_float(raw["battery_under_voltage"]),
        "battery_bulk_charge_voltage": _to_float(raw["battery_bulk_charge_voltage"]),
        "battery_float_charge_voltage": _to_float(raw["battery_float_charge_voltage"]),
        "battery_type": _decode_battery_type(raw["battery_type"]),
        "max_ac_charging_current": _to_int(raw["max_ac_charging_current"]),
        "max_charging_current": _decode_max_charging_current(raw["max_charging_current"]),
        "input_voltage_range": _decode_input_voltage_range(raw["input_voltage_range"]),
        "output_source_priority": _decode_output_source_priority(raw["output_source_priority"]),
        "charger_source_priority": _decode_charger_source_priority(raw["charger_source_priority"]),
        "max_parallel_units": _to_int(raw["max_parallel_units"]),
        "machine_type": _decode_machine_type(raw["machine_type"]),
        "topology": _decode_topology(raw["topology"]),
        "output_mode": _decode_output_mode(raw["output_mode"]),
        "battery_redischarge_voltage": _to_float(raw["battery_redischarge_voltage"]),
        "pv_ok_condition": _decode_pv_ok_condition(raw["pv_ok_condition"]),
        "pv_power_balance": _decode_pv_power_balance(raw["pv_power_balance"]),
    }


def _decode_device_status(bits: str) -> dict[str, bool]:
    padded = bits.strip()
    if len(padded) < 8:
        padded = padded.ljust(8, "0")
    return {
        "load_on": padded[0] == "1",
        "scc_firmware_updated": padded[1] == "1",
        "charging_on": padded[2] == "1",
        "scc_charging_on": padded[3] == "1",
        "ac_charging_on": padded[4] == "1",
        "reserved_status_5": padded[5] == "1",
        "reserved_status_6": padded[6] == "1",
        "reserved_status_7": padded[7] == "1",
    }


def _decode_device_status_2(bits: str) -> dict[str, bool]:
    padded = bits.strip()
    if len(padded) < 3:
        padded = padded.ljust(3, "0")
    return {
        "charging_to_float": padded[0] == "1",
        "switched_on": padded[1] == "1",
        "reserved_status2_2": padded[2] == "1",
    }


def _decode_battery_type(value: str) -> str:
    mapping = {
        "0": "agm",
        "1": "flooded",
        "2": "user",
        "3": "pylontech",
        "4": "shinheung",
        "5": "weco",
        "6": "soltaro",
        "7": "bak",
        "8": "lib",
        "9": "lic",
    }
    return mapping.get(value, value)


def _decode_max_charging_current(value: str) -> int:
    numeric = "".join(ch for ch in value if ch.isdigit())
    return int(numeric) if numeric else 0


def _decode_input_voltage_range(value: str) -> str:
    return {"0": "appliance", "1": "ups"}.get(value, value)


def _decode_output_source_priority(value: str) -> str:
    return {
        "0": "utility_solar_battery",
        "1": "solar_utility_battery",
        "2": "solar_battery_utility",
    }.get(value, value)


def _decode_charger_source_priority(value: str) -> str:
    return {
        "0": "solar_first",
        "1": "solar_first",
        "2": "solar_and_utility",
        "3": "only_solar",
    }.get(value, value)


def _decode_machine_type(value: str) -> str:
    return {
        "00": "grid_tie",
        "01": "off_grid",
        "10": "hybrid",
    }.get(value, value)


def _decode_topology(value: str) -> str:
    return {"0": "transformerless", "1": "transformer"}.get(value, value)


def _decode_output_mode(value: str) -> str:
    return {
        "00": "single_machine_output",
        "01": "parallel_output",
        "02": "phase_1_of_3_phase_output",
        "03": "phase_2_of_3_phase_output",
        "04": "phase_3_of_3_phase_output",
        "05": "phase_1_of_2_phase_output",
        "06": "phase_2_of_2_phase_output_120",
        "07": "phase_2_of_2_phase_output_180",
    }.get(value, value)


def _decode_pv_ok_condition(value: str) -> str:
    return {
        "0": "any_unit_with_pv",
        "1": "all_units_require_pv",
    }.get(value, value)


def _decode_pv_power_balance(value: str) -> str:
    return {
        "0": "max_charge_current",
        "1": "max_charge_plus_load_power",
    }.get(value, value)


def _estimate_battery_reserve_percent(metrics: dict[str, Any]) -> int:
    battery_voltage = float(metrics.get("battery_voltage", 0.0))
    if battery_voltage <= 0:
        return int(metrics.get("battery_capacity_raw", metrics.get("battery_capacity", 0)) or 0)

    nominal_voltage = float(metrics.get("rating_battery_voltage", 48.0) or 48.0)
    scale = nominal_voltage / 48.0 if nominal_voltage > 0 else 1.0
    net_battery_current = float(metrics.get("battery_net_current", 0.0))
    compensated_voltage = battery_voltage - (net_battery_current * 0.03 * scale)

    battery_type = str(metrics.get("battery_type", "")).lower()
    curve = LITHIUM_RESERVE_CURVE_48V if battery_type in LITHIUM_BATTERY_TYPES else LEAD_ACID_RESERVE_CURVE_48V
    return _interpolate_curve(compensated_voltage, curve, scale)


def _interpolate_curve(voltage: float, curve: tuple[tuple[float, int], ...], scale: float) -> int:
    scaled_curve = [(point_voltage * scale, percent) for point_voltage, percent in curve]
    if voltage <= scaled_curve[0][0]:
        return scaled_curve[0][1]
    if voltage >= scaled_curve[-1][0]:
        return scaled_curve[-1][1]

    for (low_voltage, low_percent), (high_voltage, high_percent) in zip(scaled_curve, scaled_curve[1:]):
        if low_voltage <= voltage <= high_voltage:
            span = high_voltage - low_voltage
            if span <= 0:
                return low_percent
            fraction = (voltage - low_voltage) / span
            return round(low_percent + ((high_percent - low_percent) * fraction))

    return scaled_curve[-1][1]


def _to_float(value: str) -> float:
    return float(value)


def _to_int(value: str) -> int:
    return int(float(value))
