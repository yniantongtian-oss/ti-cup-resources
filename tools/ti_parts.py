"""Curated TI parts for electronics-contest BOMs.

Every entry was read from its ti.com product or tool page on 2026-10-22.
The page said Active for silicon and listed the development kits. This is
not a price, stock, or lifecycle guarantee: confirm the datasheet, package,
and orderable suffix before buying. Suffixes select package and feature
variants; lookup returns the catalog base device.
"""

from __future__ import annotations

CHECKED = "2026-10-22"
LOOKUP_NOTE = (
    "Catalog checked on ti.com on 2026-10-22. "
    "An orderable suffix is not a lifecycle or package guarantee."
)

_PUBLIC = ("part_number", "function", "status", "description", "url", "verified")

PARTS: tuple[dict, ...] = (
    {
        "part_number": "MSPM0G3507",
        "function": "mcu",
        "status": "active",
        "description": (
            "80 MHz Arm Cortex-M0+ MCU, 128 KB flash, 32 KB SRAM, "
            "two 12-bit 4 Msps ADCs, CAN-FD"
        ),
        "url": "https://www.ti.com/product/MSPM0G3507",
        "verified": CHECKED,
    },
    {
        "part_number": "LP-MSPM0G3507",
        "function": "dev-kit",
        "status": "listed",
        "description": "LaunchPad for the MSPM0G3507 with an on-board debug probe",
        "url": "https://www.ti.com/tool/LP-MSPM0G3507",
        "verified": CHECKED,
    },
    {
        "part_number": "TMS320F280039C",
        "function": "mcu",
        "status": "active",
        "description": (
            "C2000 real-time MCU, 120 MHz C28x with FPU, TMU, CLA, and CLB, 384 KB flash"
        ),
        "url": "https://www.ti.com/product/TMS320F280039C",
        "verified": CHECKED,
    },
    {
        "part_number": "LAUNCHXL-F280039C",
        "function": "dev-kit",
        "status": "listed",
        "description": "LaunchPad for the TMS320F280039C with an on-board XDS110 debug probe",
        "url": "https://www.ti.com/tool/LAUNCHXL-F280039C",
        "verified": CHECKED,
    },
    {
        "part_number": "THVD1450",
        "function": "interface",
        "status": "active",
        "description": (
            "3.3 V to 5 V half-duplex RS-485 transceiver with idle-bus failsafe "
            "and +/-18 kV IEC ESD"
        ),
        "url": "https://www.ti.com/product/THVD1450",
        "verified": CHECKED,
    },
    {
        "part_number": "TLV9062",
        "function": "amplifier",
        "status": "active",
        "description": "Dual 1.8 V to 5.5 V, 10 MHz rail-to-rail op amp",
        "url": "https://www.ti.com/product/TLV9062",
        "verified": CHECKED,
    },
    {
        "part_number": "INA181",
        "function": "amplifier",
        "status": "active",
        "description": (
            "26 V bidirectional current-sense amplifier, gains 20/50/100/200, "
            "bandwidth up to 350 kHz"
        ),
        "url": "https://www.ti.com/product/INA181",
        "verified": CHECKED,
    },
    {
        "part_number": "ADS1115",
        "function": "adc",
        "status": "active",
        "description": (
            "16-bit I2C delta-sigma ADC, up to 860 SPS, "
            "four single-ended or two differential inputs"
        ),
        "url": "https://www.ti.com/product/ADS1115",
        "verified": CHECKED,
    },
    {
        "part_number": "REF35",
        "function": "reference",
        "status": "active",
        "family_prefix": True,
        "description": (
            "650 nA series voltage reference, 12 ppm/C maximum drift "
            "(SOT-23, -40 C to 105 C), outputs from 1.024 V to 5 V"
        ),
        "url": "https://www.ti.com/product/REF35",
        "verified": CHECKED,
    },
    {
        "part_number": "TPS62933",
        "function": "power",
        "status": "active",
        "description": "3.8 V to 30 V input, 3 A synchronous buck, 0.8 V to 22 V output",
        "url": "https://www.ti.com/product/TPS62933",
        "verified": CHECKED,
    },
    {
        "part_number": "UCC27624",
        "function": "gate-driver",
        "status": "active",
        "description": "Dual 5 A low-side gate driver, 4.5 V to 26 V VDD, 30 V absolute maximum",
        "url": "https://www.ti.com/product/UCC27624",
        "verified": CHECKED,
    },
)


def _norm(value: str) -> str:
    return "".join(character for character in value.upper() if character not in " -_")


def _public(part: dict) -> dict:
    return {key: part[key] for key in _PUBLIC}


def _prefix_match(key: str, base: str, part: dict) -> bool:
    if not key.startswith(base) or len(key) == len(base):
        return False
    if part.get("family_prefix"):
        return True
    return key[len(base)].isalpha()


def lookup(part_number: str) -> dict | None:
    """Return the catalog entry for a generic number or an orderable suffix."""
    key = _norm(part_number)
    if not key:
        return None
    best: dict | None = None
    best_len = -1
    for part in PARTS:
        base = _norm(part["part_number"])
        if key == base:
            return _public(part)
        if _prefix_match(key, base, part) and len(base) > best_len:
            best = part
            best_len = len(base)
    return _public(best) if best is not None else None


def catalog(function: str | None = None) -> list[dict]:
    items = PARTS
    if function:
        wanted = function.casefold()
        items = tuple(part for part in items if part["function"].casefold() == wanted)
    return sorted(
        (_public(part) for part in items),
        key=lambda item: (item["function"], item["part_number"]),
    )
