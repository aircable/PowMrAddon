from __future__ import annotations

import json
import logging
import time
from threading import Event
from collections.abc import Callable

import paho.mqtt.client as mqtt

from .discovery import build_discovery_messages
from .models import RuntimeConfig


LOG = logging.getLogger(__name__)


class MqttPublisher:
    def __init__(self, config: RuntimeConfig, command_handler: Callable[[str, str], None]) -> None:
        self._config = config
        self._command_handler = command_handler
        self._connected = Event()
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{config.device_id}_collector")
        if config.mqtt_username:
            self._client.username_pw_set(config.mqtt_username, config.mqtt_password or None)
        self._client.enable_logger(LOG)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

    def connect(self) -> None:
        while True:
            try:
                self._client.connect(self._config.mqtt_host, self._config.mqtt_port, keepalive=30)
                self._client.loop_start()
                if self._connected.wait(timeout=10):
                    self.publish_availability(True)
                    self.publish_discovery()
                    return
            except Exception as exc:
                LOG.warning("MQTT connect failed: %s", exc)
            time.sleep(5)

    def disconnect(self) -> None:
        try:
            self.publish_availability(False)
        finally:
            self._client.loop_stop()
            self._client.disconnect()

    def publish_discovery(self) -> None:
        for topic, payload in build_discovery_messages(self._config):
            self._publish(topic, payload, retain=True)

    def publish_state(self, payload: dict[str, object]) -> None:
        topic = f"{self._config.mqtt_topic_prefix}/state"
        self._publish(topic, payload, retain=False)

    def publish_availability(self, online: bool) -> None:
        topic = f"{self._config.mqtt_topic_prefix}/status"
        self._publish(topic, "online" if online else "offline", retain=True)

    def _publish(self, topic: str, payload: dict[str, object] | str, retain: bool) -> None:
        if isinstance(payload, dict):
            encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        else:
            encoded = payload
        info = self._client.publish(topic, encoded, qos=1, retain=retain)
        info.wait_for_publish()

    def _on_connect(self, client: mqtt.Client, userdata: object, flags: mqtt.ConnectFlags, reason_code: mqtt.ReasonCode, properties: mqtt.Properties | None) -> None:
        if reason_code.is_failure:
            LOG.error("MQTT connection failed: %s", reason_code)
            self._connected.clear()
            return
        LOG.info("Connected to MQTT broker at %s:%s", self._config.mqtt_host, self._config.mqtt_port)
        self._client.subscribe(f"{self._config.mqtt_topic_prefix}/set/+")
        self._connected.set()

    def _on_disconnect(self, client: mqtt.Client, userdata: object, disconnect_flags: mqtt.DisconnectFlags, reason_code: mqtt.ReasonCode, properties: mqtt.Properties | None) -> None:
        LOG.warning("Disconnected from MQTT broker: %s", reason_code)
        self._connected.clear()

    def _on_message(self, client: mqtt.Client, userdata: object, message: mqtt.MQTTMessage) -> None:
        topic = message.topic
        payload = message.payload.decode("utf-8").strip()
        LOG.info("Received command topic=%s payload=%s", topic, payload)
        object_id = topic.rsplit("/", 1)[-1]
        self._command_handler(object_id, payload)
