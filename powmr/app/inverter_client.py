from __future__ import annotations

import binascii
import logging
import socket


LOG = logging.getLogger(__name__)


class InverterError(RuntimeError):
    pass


class InverterClient:
    def __init__(self, host: str, port: int, timeout_seconds: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._timeout_seconds = timeout_seconds

    def query(self, command: str) -> str:
        payload = self._build_command(command)
        LOG.debug("Sending inverter command %s to %s:%s", command, self._host, self._port)
        with socket.create_connection((self._host, self._port), timeout=self._timeout_seconds) as conn:
            conn.settimeout(self._timeout_seconds)
            conn.sendall(payload)
            raw = self._read_frame(conn)
        LOG.debug("Received raw frame for %s: %r", command, raw)
        frame = self._validate_frame(raw)
        if frame == "NAK":
            raise InverterError(f"{command} returned NAK")
        LOG.debug("Decoded inverter frame for %s: %s", command, frame)
        return frame

    def _build_command(self, command: str) -> bytes:
        body = command.encode("ascii")
        crc = self._crc16_xmodem(body)
        escaped_crc = bytes(self._escape_crc_byte(byte) for byte in crc)
        return body + escaped_crc + b"\r"

    def _read_frame(self, conn: socket.socket) -> bytes:
        chunks = bytearray()
        while True:
            chunk = conn.recv(1)
            if not chunk:
                raise InverterError("Connection closed before frame terminator")
            chunks.extend(chunk)
            if chunk == b"\r":
                return bytes(chunks)

    def _validate_frame(self, raw: bytes) -> str:
        if len(raw) < 4 or raw[-1:] != b"\r":
            raise InverterError("Malformed inverter frame")

        body = raw[:-3]
        crc = raw[-3:-1]
        expected_crc = bytes(self._escape_crc_byte(byte) for byte in self._crc16_xmodem(body))
        if crc != expected_crc:
            raise InverterError("CRC mismatch in inverter response")

        try:
            decoded = body.decode("ascii")
        except UnicodeDecodeError as exc:
            raise InverterError("Non-ASCII inverter response") from exc

        if not decoded.startswith("("):
            raise InverterError(f"Unexpected inverter payload: {decoded!r}")
        return decoded[1:]

    @staticmethod
    def _crc16_xmodem(data: bytes) -> bytes:
        crc = binascii.crc_hqx(data, 0)
        return crc.to_bytes(2, "big")

    @staticmethod
    def _escape_crc_byte(value: int) -> int:
        if value in (0x28, 0x0D, 0x0A):
            return (value + 1) & 0xFF
        return value
