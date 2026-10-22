#!/usr/bin/env python3
"""Small dependency-free Modbus RTU frame helper.

This module does not open a serial port. It builds requests, checks CRC, and
decodes function 03/04 responses so a serial program or a test harness can
reuse the same frames.

Register writes accept a uint16 or a negative int16. Negative values are
stored as two's complement. Slave 0 is the Modbus broadcast address and is
accepted only for writes.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass


class ModbusException(RuntimeError):
    """A well-formed exception response from a slave."""

    def __init__(self, code: int) -> None:
        self.code = code
        super().__init__(f"Modbus exception code {code}")


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF


def append_crc(payload: bytes) -> bytes:
    value = crc16(payload)
    return payload + bytes((value & 0xFF, value >> 8))


def validate_crc(frame: bytes) -> bool:
    return len(frame) >= 4 and crc16(frame[:-2]) == int.from_bytes(frame[-2:], "little")


def _as_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an int")
    return value


def _u16(value: int, name: str) -> int:
    value = _as_int(value, name)
    if not 0 <= value <= 0xFFFF:
        raise ValueError(f"{name} must fit in uint16")
    return value


def _slave(slave: int, *, allow_broadcast: bool = False) -> int:
    slave = _as_int(slave, "slave")
    lower = 0 if allow_broadcast else 1
    if not lower <= slave <= 247:
        span = "0..247" if allow_broadcast else "1..247"
        raise ValueError(f"slave must be in {span}")
    return slave


def _quantity(count: int, upper: int, address: int) -> int:
    count = _as_int(count, "count")
    if not 1 <= count <= upper:
        raise ValueError(f"count must be in 1..{upper}")
    if address + count > 0x10000:
        raise ValueError("address range exceeds 65536 registers")
    return count


def int16_to_u16(value: int) -> int:
    value = _as_int(value, "value")
    if not -32768 <= value <= 32767:
        raise ValueError("value must fit in int16")
    return value & 0xFFFF


def u16_to_int16(value: int) -> int:
    value = _u16(value, "value")
    return value - 0x10000 if value >= 0x8000 else value


def _register_value(value: int) -> int:
    value = _as_int(value, "value")
    if value < 0:
        return int16_to_u16(value)
    return _u16(value, "value")


def read_holding_registers(slave: int, address: int, count: int) -> bytes:
    _slave(slave)
    address = _u16(address, "address")
    count = _quantity(count, 125, address)
    return append_crc(bytes((slave, 0x03)) + address.to_bytes(2, "big") + count.to_bytes(2, "big"))


def read_input_registers(slave: int, address: int, count: int) -> bytes:
    _slave(slave)
    address = _u16(address, "address")
    count = _quantity(count, 125, address)
    return append_crc(bytes((slave, 0x04)) + address.to_bytes(2, "big") + count.to_bytes(2, "big"))


def write_single_register(slave: int, address: int, value: int) -> bytes:
    _slave(slave, allow_broadcast=True)
    address = _u16(address, "address")
    encoded = _register_value(value)
    return append_crc(bytes((slave, 0x06)) + address.to_bytes(2, "big") + encoded.to_bytes(2, "big"))


def write_multiple_registers(slave: int, address: int, values: list[int] | tuple[int, ...]) -> bytes:
    _slave(slave, allow_broadcast=True)
    address = _u16(address, "address")
    registers = [_register_value(value) for value in values]
    count = _quantity(len(registers), 123, address)
    body = b"".join(value.to_bytes(2, "big") for value in registers)
    payload = (
        bytes((slave, 0x10))
        + address.to_bytes(2, "big")
        + count.to_bytes(2, "big")
        + bytes((len(body),))
        + body
    )
    return append_crc(payload)


@dataclass(frozen=True)
class RegisterResponse:
    slave: int
    function: int
    registers: tuple[int, ...]


def parse_register_response(frame: bytes, expected_slave: int | None = None) -> RegisterResponse:
    if not validate_crc(frame):
        raise ValueError("invalid Modbus CRC")
    slave, function = frame[0], frame[1]
    if expected_slave is not None and slave != _slave(expected_slave):
        raise ValueError(f"unexpected slave {slave}")
    if function & 0x80:
        if len(frame) != 5:
            raise ValueError("invalid exception response length")
        raise ModbusException(frame[2])
    if function not in (0x03, 0x04):
        raise ValueError(f"unsupported response function 0x{function:02X}")
    byte_count = frame[2]
    if byte_count == 0 or byte_count % 2 or len(frame) != byte_count + 5:
        raise ValueError("invalid register byte count")
    registers = tuple(
        int.from_bytes(frame[index : index + 2], "big") for index in range(3, 3 + byte_count, 2)
    )
    return RegisterResponse(slave=slave, function=function, registers=registers)


def hex_bytes(data: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def _parse_int(value: str) -> int:
    return int(value, 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and inspect Modbus RTU frames")
    sub = parser.add_subparsers(dest="command", required=True)

    read = sub.add_parser("read", help="build function 03/04 request")
    read.add_argument("slave", type=_parse_int)
    read.add_argument("address", type=_parse_int)
    read.add_argument("count", type=_parse_int)
    read.add_argument("--input", action="store_true", help="use input registers (0x04)")

    write = sub.add_parser("write", help="build function 06 request")
    write.add_argument("slave", type=_parse_int)
    write.add_argument("address", type=_parse_int)
    write.add_argument("value", type=_parse_int)

    multi = sub.add_parser("write-multi", help="build function 16 request")
    multi.add_argument("slave", type=_parse_int)
    multi.add_argument("address", type=_parse_int)
    multi.add_argument("values", type=_parse_int, nargs="+")

    parse = sub.add_parser("parse", help="parse function 03/04 response")
    parse.add_argument("hex_frame", help='for example: "01 03 02 00 2A 39 9B"')
    parse.add_argument("--slave", type=_parse_int, help="require this slave address")

    args = parser.parse_args(argv)
    try:
        if args.command == "read":
            frame = (
                read_input_registers(args.slave, args.address, args.count)
                if args.input
                else read_holding_registers(args.slave, args.address, args.count)
            )
            print(hex_bytes(frame))
        elif args.command == "write":
            print(hex_bytes(write_single_register(args.slave, args.address, args.value)))
        elif args.command == "write-multi":
            print(hex_bytes(write_multiple_registers(args.slave, args.address, args.values)))
        else:
            frame = bytes.fromhex(args.hex_frame)
            response = parse_register_response(frame, expected_slave=args.slave)
            print(
                json.dumps(
                    {
                        "slave": response.slave,
                        "function": response.function,
                        "registers": list(response.registers),
                    }
                )
            )
    except ModbusException as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
