#!/usr/bin/env python3
"""Check a contest BOM and look up a small curated TI catalog.

The CSV columns match ``templates/project-plan/bom.csv``. Empty part numbers
on a ``planned`` row are warnings. Prices use ``Decimal`` and ``do-not-use``
rows are left out of the cost rollup. The catalog is a reading aid, not a
purchasing approval.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.tables import read_csv
from tools.ti_parts import CHECKED, LOOKUP_NOTE, catalog, lookup

COLUMNS = (
    "id",
    "category",
    "manufacturer",
    "part_number",
    "description",
    "quantity",
    "unit_price",
    "currency",
    "supplier",
    "alternative_part",
    "status",
    "notes",
)
STATUSES = {"planned", "ordered", "received", "fitted", "do-not-use", "substitute"}
TI_NAMES = {"ti", "texas instruments", "texas instruments inc", "texas instruments inc."}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class BomReport:
    path: str
    rows: int
    findings: tuple[Finding, ...]
    cost: dict[str, str]

    @property
    def errors(self) -> int:
        return sum(item.severity == "error" for item in self.findings)

    @property
    def warnings(self) -> int:
        return sum(item.severity == "warning" for item in self.findings)

    @property
    def ok(self) -> bool:
        return self.errors == 0


def _is_ti(manufacturer: str) -> bool:
    return manufacturer.casefold() in TI_NAMES


def _finding(severity: str, code: str, path: str, message: str) -> Finding:
    return Finding(severity, code, path, message)


def check_bom(path: Path) -> BomReport:
    location = str(path)
    try:
        header, records = read_csv(path)
    except (OSError, ValueError) as exc:
        finding = _finding("error", "bom-unreadable", location, str(exc))
        return BomReport(location, 0, (finding,), {})

    missing = [name for name in COLUMNS if name not in header]
    if missing:
        message = "missing columns: " + ", ".join(missing)
        return BomReport(location, len(records), (_finding("error", "missing-column", location, message),), {})

    findings: list[Finding] = []
    seen_ids: dict[str, int] = {}
    seen_parts: dict[tuple[str, str], int] = {}
    amounts: dict[str, Decimal] = {}
    for line, row in records:
        where = f"{location}:{line}"
        part_id = row["id"]
        if not part_id:
            findings.append(_finding("error", "empty-id", where, "id is empty"))
        elif part_id in seen_ids:
            findings.append(_finding("error", "duplicate-id", where, f"duplicate id {part_id}"))
        else:
            seen_ids[part_id] = line

        status = row["status"].casefold()
        if not status:
            findings.append(_finding("warning", "missing-status", where, "status is empty"))
        elif status not in STATUSES:
            findings.append(
                _finding("warning", "unknown-status", where, f"status {row['status']!r} is not recognized")
            )

        part_number = row["part_number"]
        manufacturer = row["manufacturer"]
        if not part_number:
            findings.append(_finding("warning", "incomplete-part", where, "part_number is empty"))
        else:
            part_key = (manufacturer.casefold(), part_number.casefold())
            if part_key in seen_parts:
                findings.append(
                    _finding(
                        "warning",
                        "duplicate-part",
                        where,
                        f"duplicate part {manufacturer} {part_number}",
                    )
                )
            else:
                seen_parts[part_key] = line
            known = lookup(part_number)
            if known and manufacturer and not _is_ti(manufacturer):
                findings.append(
                    _finding(
                        "warning",
                        "catalog-manufacturer-mismatch",
                        where,
                        f"{part_number} is in the TI catalog but manufacturer is {manufacturer}",
                    )
                )
            elif not manufacturer:
                if known:
                    message = f"{part_number} matches TI catalog entry {known['part_number']}"
                else:
                    message = "manufacturer is empty"
                findings.append(_finding("warning", "manufacturer-unset", where, message))
            elif _is_ti(manufacturer) and known is None:
                findings.append(
                    _finding(
                        "warning",
                        "ti-part-unlisted",
                        where,
                        f"TI part {part_number} is not in the catalog checked on {CHECKED}",
                    )
                )

        quantity = _positive_int(row["quantity"])
        if quantity is None:
            findings.append(_finding("error", "bad-quantity", where, "quantity must be a positive integer"))

        price_text = row["unit_price"]
        price: Decimal | None = None
        if price_text:
            try:
                price = Decimal(price_text)
            except InvalidOperation:
                price = None
            if price is None or price < 0:
                findings.append(
                    _finding("error", "bad-price", where, "unit_price must be a non-negative number")
                )
                price = None

        currency = row["currency"].upper()
        if price is not None and not currency:
            findings.append(
                _finding("warning", "missing-currency", where, "unit_price is set but currency is empty")
            )
        elif currency and (len(currency) != 3 or not currency.isalpha()):
            findings.append(
                _finding("warning", "odd-currency", where, f"currency {row['currency']!r} is not 3 letters")
            )

        if price is not None and currency and quantity is not None and status != "do-not-use":
            amounts[currency] = amounts.get(currency, Decimal(0)) + price * quantity

    cost = {key: format(amounts[key], "f") for key in sorted(amounts)}
    ordered = tuple(sorted(findings, key=lambda item: (item.severity != "error", item.path, item.code)))
    return BomReport(location, len(records), ordered, cost)


def _positive_int(value: str) -> int | None:
    if not value.isdigit():
        return None
    number = int(value)
    if number < 1:
        return None
    return number


def _payload(report: BomReport) -> dict:
    return {
        "tool": "bom",
        "schema_version": 1,
        "path": report.path,
        "ok": report.ok,
        "rows": report.rows,
        "errors": report.errors,
        "warnings": report.warnings,
        "cost": report.cost,
        "findings": [asdict(item) for item in report.findings],
    }


def _format_name(explicit: str | None) -> str:
    if explicit:
        return explicit
    return "text" if sys.stdout.isatty() else "json"


def _print_check(report: BomReport, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(_payload(report), ensure_ascii=False, indent=2))
        return
    state = "ok" if report.ok else "failed"
    print(f"bom: {state}  rows={report.rows}  errors={report.errors}  warnings={report.warnings}")
    if report.cost:
        print("cost: " + ", ".join(f"{key} {value}" for key, value in report.cost.items()))
    for item in report.findings:
        print(f"{item.severity}\t{item.code}\t{item.path}\t{item.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="validate a BOM CSV")
    check.add_argument("path", type=Path)
    check.add_argument("--format", choices=("json", "text"))
    check.add_argument("--strict", action="store_true", help="fail when any warning is present")

    find = sub.add_parser("lookup", help="look up one part in the curated catalog")
    find.add_argument("part_number")
    find.add_argument("--format", choices=("json", "text"))

    listed = sub.add_parser("catalog", help="list the curated catalog")
    listed.add_argument("--function")
    listed.add_argument("--format", choices=("json", "text"))

    args = parser.parse_args(argv)
    fmt = _format_name(args.format)
    if args.command == "lookup":
        found = lookup(args.part_number)
        payload = {
            "found": found is not None,
            "query": args.part_number,
            "part": found,
            "checked": CHECKED,
            "note": LOOKUP_NOTE,
        }
        if fmt == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif found is None:
            print(f"{args.part_number}: not in the catalog checked on {CHECKED}")
        else:
            print(f"{found['part_number']}  {found['function']}  {found['status']}")
            print(found["description"])
            print(found["url"])
            print(LOOKUP_NOTE)
        return 0 if found is not None else 1

    if args.command == "catalog":
        items = catalog(args.function)
        if fmt == "json":
            print(json.dumps({"checked": CHECKED, "parts": items}, ensure_ascii=False, indent=2))
        else:
            for item in items:
                print(f"{item['part_number']}\t{item['function']}\t{item['status']}\t{item['url']}")
        return 0

    if not args.path.is_file():
        print(f"bom check failed: {args.path} is not a file", file=sys.stderr)
        return 2
    report = check_bom(args.path)
    _print_check(report, fmt)
    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
