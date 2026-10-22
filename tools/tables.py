"""CSV loader for the contest spreadsheets."""

from __future__ import annotations

import csv
import io
from pathlib import Path


def read_csv(path: Path) -> tuple[list[str], list[tuple[int, dict[str, str]]]]:
    """Return the header and non-empty data rows.

    Each row is ``(line_number, cells)`` using 1-based file line numbers.
    Raises ``ValueError`` when the file is not a usable UTF-8 table.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeError as exc:
        raise ValueError(f"CSV must be UTF-8: {exc}") from exc
    try:
        parsed = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        raise ValueError(f"CSV parse error: {exc}") from exc
    if not parsed or not any(cell.strip() for cell in parsed[0]):
        raise ValueError("CSV is empty")
    header = [cell.strip() for cell in parsed[0]]
    if any(not name for name in header):
        raise ValueError("CSV has a blank column name")
    if len(header) != len(set(header)):
        raise ValueError("CSV has a duplicate column name")
    records: list[tuple[int, dict[str, str]]] = []
    width = len(header)
    for offset, cells in enumerate(parsed[1:], start=2):
        if not any(cell.strip() for cell in cells):
            continue
        if len(cells) > width:
            raise ValueError(f"row {offset} has too many columns")
        padded = cells + [""] * (width - len(cells))
        records.append((offset, {header[index]: padded[index].strip() for index in range(width)}))
    return header, records
