import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from tools.modbus_rtu import (
    ModbusException,
    append_crc,
    crc16,
    hex_bytes,
    int16_to_u16,
    main,
    parse_register_response,
    read_holding_registers,
    read_input_registers,
    u16_to_int16,
    validate_crc,
    write_multiple_registers,
    write_single_register,
)


class ModbusRtuTests(unittest.TestCase):
    def test_known_crc_vector(self):
        payload = bytes.fromhex("01 03 00 00 00 0A")
        self.assertEqual(crc16(payload), 0xCDC5)
        self.assertEqual(append_crc(payload), bytes.fromhex("01 03 00 00 00 0A C5 CD"))

    def test_read_holding_request(self):
        frame = read_holding_registers(1, 0, 10)
        self.assertEqual(frame, bytes.fromhex("01 03 00 00 00 0A C5 CD"))
        self.assertTrue(validate_crc(frame))

    def test_write_single_register(self):
        frame = write_single_register(1, 1, 1000)
        self.assertTrue(validate_crc(frame))
        self.assertEqual(frame[:6], bytes.fromhex("01 06 00 01 03 E8"))

    def test_write_multiple_registers(self):
        frame = write_multiple_registers(2, 4, [1, 2, 0xFFFF])
        self.assertTrue(validate_crc(frame))
        self.assertEqual(frame[0:7], bytes.fromhex("02 10 00 04 00 03 06"))
        self.assertEqual(frame[7:-2], bytes.fromhex("00 01 00 02 FF FF"))

    def test_parse_register_response(self):
        payload = bytes.fromhex("01 04 06 00 2A FF 9C 04 D2")
        response = parse_register_response(append_crc(payload), expected_slave=1)
        self.assertEqual(response.slave, 1)
        self.assertEqual(response.function, 4)
        self.assertEqual(response.registers, (42, 0xFF9C, 1234))

    def test_reject_bad_crc(self):
        with self.assertRaises(ValueError):
            parse_register_response(bytes.fromhex("01 03 02 00 2A 00 00"))

    def test_reject_invalid_limits(self):
        with self.assertRaises(ValueError):
            read_holding_registers(0, 0, 1)
        with self.assertRaises(ValueError):
            read_holding_registers(1, 0, 126)
        with self.assertRaises(ValueError):
            write_multiple_registers(1, 0, [])

    def test_address_window_and_types(self):
        self.assertTrue(validate_crc(read_holding_registers(1, 0xFFFF, 1)))
        with self.assertRaises(ValueError):
            read_holding_registers(1, 0xFFFF, 2)
        with self.assertRaises(ValueError):
            read_holding_registers(1.5, 0, 1)
        with self.assertRaises(ValueError):
            read_holding_registers(1, 0, True)
        with self.assertRaises(ValueError):
            write_multiple_registers(1, 0xFFF0, [1] * 123)

    def test_input_registers_and_broadcast_write(self):
        frame = read_input_registers(1, 0, 1)
        self.assertEqual(frame[1], 0x04)
        self.assertTrue(validate_crc(frame))
        broadcast = write_single_register(0, 1, 3)
        self.assertEqual(broadcast[0], 0)
        self.assertTrue(validate_crc(broadcast))
        with self.assertRaises(ValueError):
            read_input_registers(0, 0, 1)

    def test_signed_register_values(self):
        self.assertEqual(int16_to_u16(-1), 0xFFFF)
        self.assertEqual(u16_to_int16(0x8000), -32768)
        frame = write_single_register(1, 1, -1)
        self.assertEqual(frame[4:6], b"\xff\xff")
        self.assertTrue(validate_crc(frame))
        frame = write_multiple_registers(1, 0, [-2, 2])
        self.assertEqual(frame[7:11], bytes.fromhex("FF FE 00 02"))

    def test_exception_and_response_errors(self):
        frame = append_crc(bytes((1, 0x83, 0x02)))
        with self.assertRaises(ModbusException) as caught:
            parse_register_response(frame)
        self.assertEqual(caught.exception.code, 2)
        with self.assertRaises(ValueError):
            parse_register_response(frame, expected_slave=2)
        with self.assertRaises(ValueError):
            parse_register_response(append_crc(bytes((1, 0x83, 0x02, 0x00))))
        with self.assertRaises(ValueError):
            parse_register_response(append_crc(bytes((1, 0x03, 0x00))))

    def test_cli_frames(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main(["read", "1", "0", "10"]), 0)
        self.assertEqual(stdout.getvalue().strip(), "01 03 00 00 00 0A C5 CD")

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main(["write-multi", "2", "4", "1", "2", "65535"]), 0)
        frame = bytes.fromhex(stdout.getvalue())
        self.assertEqual(frame[1], 0x10)
        self.assertTrue(validate_crc(frame))

        payload = bytes.fromhex("01 04 06 00 2A FF 9C 04 D2")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main(["parse", hex_bytes(append_crc(payload)), "--slave", "1"]), 0)
        self.assertEqual(json.loads(stdout.getvalue())["registers"], [42, 0xFF9C, 1234])

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(main(["parse", "01 0"]), 2)
        self.assertTrue(stderr.getvalue().strip())

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(main(["parse", hex_bytes(append_crc(bytes((1, 0x83, 0x02))))]), 1)
        self.assertIn("exception code 2", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
