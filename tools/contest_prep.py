#!/usr/bin/env python3
"""Summarize contest readiness for a person or an agent.

Stdout is text in a terminal and JSON otherwise. ``--format`` overrides that.
JSON schema version is 1. ``ok`` is true when there are no errors; warnings
stay visible in ``counts``. The process exits 1 when ``ok`` is false, and
``--strict`` also exits 1 when any warning is present. Usage and IO failures
exit 2.

Default files, first match under the project root:

- ``design-review-checklist.md``, ``templates/design-review-checklist.md``
- ``bom.csv``, ``project-plan/bom.csv``, ``templates/project-plan/bom.csv``
- ``competition-schedule.csv``, ``templates/competition-schedule.csv``
- ``risk-register.csv``, ``project-plan/risk-register.csv``,
  ``templates/project-plan/risk-register.csv``
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools import __version__
from tools.bom import check_bom
from tools.project_audit import audit, visible_markdown
from tools.tables import read_csv

CHECKLIST_CANDIDATES = ("design-review-checklist.md", "templates/design-review-checklist.md")
BOM_CANDIDATES = ("bom.csv", "project-plan/bom.csv", "templates/project-plan/bom.csv")
SCHEDULE_CANDIDATES = ("competition-schedule.csv", "templates/competition-schedule.csv")
RISK_CANDIDATES = (
    "risk-register.csv",
    "project-plan/risk-register.csv",
    "templates/project-plan/risk-register.csv",
)
DONE = {"完成", "已完成", "done", "complete", "completed", "closed"}
_BOXES = re.compile(r"(?m)^[ \t]*[-*]\s+\[([ xX])\]")


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


def _discover(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def _require(path: Path | None) -> None:
    if path is not None and not path.is_file():
        raise FileNotFoundError(path)


def _done(status: str) -> bool:
    return status in {"完成", "已完成"} or status.casefold() in DONE


def _pick(row: dict[str, str], names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in row:
            return row[name]
    return None


def _parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(value)


def _checklist(path: Path | None) -> dict:
    if path is None:
        finding = Finding("warning", "missing-checklist", "design-review-checklist.md", "checklist was not found")
        return {"path": None, "checked": 0, "unchecked": 0, "complete": False, "findings": [finding]}
    try:
        text = visible_markdown(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        finding = Finding("error", "checklist-unreadable", str(path), str(exc))
        return {"path": str(path), "checked": 0, "unchecked": 0, "complete": False, "findings": [finding]}
    marks = _BOXES.findall(text)
    checked = sum(mark in "xX" for mark in marks)
    unchecked = sum(mark == " " for mark in marks)
    findings: list[Finding] = []
    if not marks:
        findings.append(Finding("warning", "checklist-empty", str(path), "checklist has no task boxes"))
    return {
        "path": str(path),
        "checked": checked,
        "unchecked": unchecked,
        "complete": bool(marks) and unchecked == 0,
        "findings": findings,
    }


def _schedule(path: Path | None, today: date) -> dict:
    empty = {"path": None if path is None else str(path), "tasks": 0, "overdue": 0, "undated": 0, "findings": []}
    if path is None:
        empty["findings"] = [
            Finding("warning", "missing-schedule", "competition-schedule.csv", "schedule was not found")
        ]
        return empty
    try:
        header, records = read_csv(path)
    except (OSError, ValueError) as exc:
        empty["findings"] = [Finding("error", "schedule-unreadable", str(path), str(exc))]
        return empty
    has_end = any(name in header for name in ("计划结束", "planned_end", "end"))
    has_status = any(name in header for name in ("状态", "status"))
    if not has_end or not has_status:
        empty["findings"] = [
            Finding("error", "schedule-columns", str(path), "schedule needs an end date and a status column")
        ]
        return empty
    findings: list[Finding] = []
    overdue = 0
    undated = 0
    for line, row in records:
        status = _pick(row, ("状态", "status")) or ""
        end = _pick(row, ("计划结束", "planned_end", "end")) or ""
        task_id = _pick(row, ("ID", "id")) or str(line)
        where = f"{path}:{line}"
        if not end:
            undated += 1
            continue
        try:
            end_date = _parse_date(end)
        except ValueError:
            findings.append(Finding("error", "schedule-bad-date", where, f"task {task_id} has an invalid end date"))
            continue
        if end_date < today and not _done(status):
            overdue += 1
            findings.append(
                Finding("warning", "schedule-overdue", where, f"task {task_id} ended on {end_date.isoformat()}")
            )
    if undated:
        findings.append(
            Finding("warning", "schedule-undated", str(path), f"{undated} tasks have no end date")
        )
    findings.sort(key=lambda item: (item.severity != "error", item.path, item.code))
    return {
        "path": str(path),
        "tasks": len(records),
        "overdue": overdue,
        "undated": undated,
        "findings": findings,
    }


def _risks(path: Path | None) -> dict:
    if path is None:
        finding = Finding("warning", "missing-risk-register", "risk-register.csv", "risk register was not found")
        return {"path": None, "rows": 0, "findings": [finding]}
    try:
        header, records = read_csv(path)
    except (OSError, ValueError) as exc:
        return {"path": str(path), "rows": 0, "findings": [Finding("error", "risk-unreadable", str(path), str(exc))]}
    required = ("likelihood_1_5", "impact_1_5", "score")
    missing = [name for name in required if name not in header]
    if missing:
        message = "missing columns: " + ", ".join(missing)
        finding = Finding("error", "risk-columns", str(path), message)
        return {"path": str(path), "rows": len(records), "findings": [finding]}
    findings: list[Finding] = []
    if not records:
        findings.append(Finding("warning", "risk-empty", str(path), "risk register has no rows"))
    for line, row in records:
        where = f"{path}:{line}"
        try:
            likelihood = _factor(row["likelihood_1_5"])
            impact = _factor(row["impact_1_5"])
            score = _factor(row["score"], upper=25)
        except ValueError as exc:
            findings.append(Finding("error", "risk-factor-range", where, str(exc)))
            continue
        if likelihood is None or impact is None:
            if score is not None:
                findings.append(Finding("warning", "risk-score-incomplete", where, "score is set without both factors"))
            else:
                findings.append(Finding("warning", "risk-unscored", where, "likelihood or impact is empty"))
            continue
        if score is None:
            findings.append(Finding("warning", "risk-score-missing", where, "score is empty"))
        elif score != likelihood * impact:
            findings.append(
                Finding(
                    "error",
                    "risk-score-mismatch",
                    where,
                    f"score {score} does not equal {likelihood} x {impact}",
                )
            )
    findings.sort(key=lambda item: (item.severity != "error", item.path, item.code))
    return {"path": str(path), "rows": len(records), "findings": findings}


def _factor(value: str, upper: int = 5) -> int | None:
    if not value:
        return None
    if not value.isdigit():
        raise ValueError(f"expected an integer 1..{upper}")
    number = int(value)
    if not 1 <= number <= upper:
        raise ValueError(f"expected an integer 1..{upper}")
    return number


def _bom(path: Path | None) -> dict:
    if path is None:
        finding = Finding("warning", "missing-bom", "bom.csv", "BOM was not found")
        return {"path": None, "rows": 0, "cost": {}, "findings": [finding]}
    report = check_bom(path)
    return {
        "path": report.path,
        "rows": report.rows,
        "cost": report.cost,
        "findings": [
            Finding(item.severity, item.code, item.path, item.message) for item in report.findings
        ],
    }


def _audit(root: Path) -> dict:
    findings = [
        Finding(item.severity, item.code, item.path, item.message) for item in audit(root)
    ]
    return {"findings": findings}


def _count(sections: list[dict]) -> dict[str, int]:
    errors = 0
    warnings = 0
    for section in sections:
        for item in section["findings"]:
            if item.severity == "error":
                errors += 1
            elif item.severity == "warning":
                warnings += 1
    return {"errors": errors, "warnings": warnings}


def prepare(
    root: Path,
    *,
    today: date | None = None,
    checklist: Path | None = None,
    bom: Path | None = None,
    schedule: Path | None = None,
    risks: Path | None = None,
) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    for explicit in (checklist, bom, schedule, risks):
        _require(explicit)
    current = today or date.today()
    checklist_path = checklist or _discover(root, CHECKLIST_CANDIDATES)
    bom_path = bom or _discover(root, BOM_CANDIDATES)
    schedule_path = schedule or _discover(root, SCHEDULE_CANDIDATES)
    risk_path = risks or _discover(root, RISK_CANDIDATES)
    report = {
        "tool": "contest_prep",
        "schema_version": 1,
        "package_version": __version__,
        "root": str(root),
        "today": current.isoformat(),
        "audit": _audit(root),
        "bom": _bom(bom_path),
        "checklist": _checklist(checklist_path),
        "schedule": _schedule(schedule_path, current),
        "risks": _risks(risk_path),
    }
    counts = _count([report["audit"], report["bom"], report["checklist"], report["schedule"], report["risks"]])
    report["ok"] = counts["errors"] == 0
    report["counts"] = counts
    return report


def _public(report: dict) -> dict:
    copied = dict(report)
    for key in ("audit", "bom", "checklist", "schedule", "risks"):
        section = dict(copied[key])
        section["findings"] = [asdict(item) for item in section["findings"]]
        copied[key] = section
    return copied


def render(report: dict, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(_public(report), ensure_ascii=False, indent=2) + "\n"
    checklist = report["checklist"]
    schedule = report["schedule"]
    lines = [
        f"contest prep: {'ok' if report['ok'] else 'failed'}",
        f"errors: {report['counts']['errors']}",
        f"warnings: {report['counts']['warnings']}",
        f"checklist: {checklist['checked']} checked, {checklist['unchecked']} open",
        f"schedule: {schedule['overdue']} overdue, {schedule['undated']} undated",
    ]
    cost = report["bom"]["cost"]
    if cost:
        lines.append("bom cost: " + ", ".join(f"{key} {value}" for key, value in cost.items()))
    for name in ("audit", "bom", "checklist", "schedule", "risks"):
        for item in report[name]["findings"]:
            lines.append(f"{item.severity}\t{name}\t{item.code}\t{item.path}\t{item.message}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--format", choices=("json", "text"))
    parser.add_argument("--strict", action="store_true", help="fail when any warning is present")
    parser.add_argument("--today", type=date.fromisoformat, help="ISO date used for overdue checks")
    parser.add_argument("--checklist", type=Path)
    parser.add_argument("--bom", type=Path)
    parser.add_argument("--schedule", type=Path)
    parser.add_argument("--risks", type=Path)
    args = parser.parse_args(argv)
    fmt = args.format or ("text" if sys.stdout.isatty() else "json")
    try:
        report = prepare(
            args.root,
            today=args.today,
            checklist=args.checklist,
            bom=args.bom,
            schedule=args.schedule,
            risks=args.risks,
        )
    except (OSError, ValueError) as exc:
        print(f"contest prep failed: {exc}", file=sys.stderr)
        return 2
    print(render(report, fmt), end="")
    if report["counts"]["errors"] or (args.strict and report["counts"]["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
