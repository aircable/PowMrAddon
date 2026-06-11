#!/usr/bin/with-contenv bashio
set -euo pipefail

if bashio::services.available "mqtt"; then
  MQTT_HOST="$(bashio::services "mqtt" "host")"
  MQTT_PORT="$(bashio::services "mqtt" "port")"
  MQTT_USERNAME="$(bashio::services "mqtt" "username")"
  MQTT_PASSWORD="$(bashio::services "mqtt" "password")"
else
  MQTT_HOST="$(bashio::config 'mqtt_host')"
  MQTT_PORT="$(bashio::config 'mqtt_port')"
  MQTT_USERNAME="$(bashio::config 'mqtt_username')"
  MQTT_PASSWORD="$(bashio::config 'mqtt_password')"
fi

export POWMR_INVERTER_HOST="$(bashio::config 'inverter_host')"
export POWMR_INVERTER_PORT="$(bashio::config 'inverter_port')"
export POWMR_POLL_INTERVAL_SECONDS="$(bashio::config 'poll_interval_seconds')"
export POWMR_STALE_LINK_SECONDS="$(bashio::config 'stale_link_seconds')"
export POWMR_MQTT_HOST="${MQTT_HOST}"
export POWMR_MQTT_PORT="${MQTT_PORT}"
export POWMR_MQTT_USERNAME="${MQTT_USERNAME}"
export POWMR_MQTT_PASSWORD="${MQTT_PASSWORD}"
export POWMR_MQTT_TOPIC_PREFIX="$(bashio::config 'mqtt_topic_prefix')"
export POWMR_DEVICE_NAME="$(bashio::config 'device_name')"
export POWMR_DEVICE_ID="$(bashio::config 'device_id')"
export POWMR_DEBUG_LOGGING="$(bashio::config 'debug_logging')"
export POWMR_SAFE_OUTPUT_SOURCE_PRIORITY="$(bashio::config 'safe_output_source_priority')"

cd /app
exec /opt/venv/bin/python -m app.main
