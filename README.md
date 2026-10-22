# Electronics Competition Resources

**Reusable project documents, protocol utilities, review checklists, and repository-quality tools for electronics engineering.**

[![Resource quality](https://github.com/yniantongtian-oss/ti-cup-resources/actions/workflows/ci.yml/badge.svg)](https://github.com/yniantongtian-oss/ti-cup-resources/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This repository includes reusable project and retrospective templates, RS485/Modbus RTU helpers, and a project audit utility with no required third-party Python dependencies. The goal is traceable, reproducible, collaborative engineering documentation.

## Repository audit

Check for a README, license, ignore rules, oversized files, possible embedded secrets, and broken local Markdown links:

```bash
python3 tools/project_audit.py /path/to/project
python3 tools/project_audit.py . --format json --output audit.json
python3 tools/project_audit.py . --strict
```

The default command reports findings without failing; strict mode exits nonzero on detected errors.

## Modbus RTU frame utility

Generate standard frames, verify CRC values, and parse function-code 03/04 responses without serial-port libraries:

```bash
python3 tools/modbus_rtu.py read 1 0 10
python3 tools/modbus_rtu.py read 1 0 8 --input
python3 tools/modbus_rtu.py write 1 1 1000
python3 tools/modbus_rtu.py parse "01 04 02 00 2A 39 9B"
```

The module can be imported into Python serial applications or test harnesses. See [Modbus troubleshooting](docs/MODBUS_DEBUGGING_GUIDE.md).

Negative register values are encoded as int16. Slave 0 is accepted for writes and rejected for reads. A starting address plus quantity past register 65535 is rejected.

## BOM check

`templates/project-plan/bom.csv` is the expected column layout. The checker prices rows with `Decimal`, leaves `do-not-use` rows out of the total, and compares TI manufacturer rows with a small catalog read from ti.com on 2026-10-22.

```bash
python3 tools/bom.py check templates/project-plan/bom.csv
python3 tools/bom.py lookup MSPM0G3507
python3 tools/bom.py catalog --function mcu
```

Orderable suffixes such as `MSPM0G3507SRHBR` resolve to the catalog base device. That match is not a package or lifecycle guarantee. See [references](docs/REFERENCE_MATERIALS.md).

## Contest prep

One command runs the repository audit, the BOM check, the design-review checklist, the schedule, and the risk-register score. A terminal gets a short text summary. A pipe, a redirect, or `--format json` prints schema version 1 for scripts and agents. `ok` is true when there are no errors. Warnings stay in `counts`.

```bash
python3 tools/contest_prep.py .
python3 tools/contest_prep.py . --format json --today 2026-10-22
python3 tools/contest_prep.py . --strict
```

Exit 1 means the report has errors, or warnings when `--strict` is set. Exit 2 means the command could not read an explicit path. Details are in [tools/README.md](tools/README.md).

## Project and review templates

| Resource | Intended use |
| --- | --- |
| [Project plans](templates/project-plan/) | BOM, test records and risk logs |
| [Design review checklist](templates/design-review-checklist.md) | Requirements, hardware, firmware, communication, test and presentation readiness |
| [Competition schedule](templates/competition-schedule.csv) | Milestones from requirements to final rehearsal |
| [Retrospective](experience/retrospective-template.md) | Evidence-driven review after a project |
| [Learning path](docs/LEARNING_PATH.md) | Structured learning sequence |
| [Common pitfalls](docs/COMMON_PITFALLS.md) | Frequent project failures |
| [Safety notes](docs/SAFETY_NOTES.md) | Hardware experiment precautions |
| [Reference materials](docs/REFERENCE_MATERIALS.md) | Attribution and citation standards |
| [Defense guidance](docs/ANSWER_DEFENSE_TIPS.md) | Explaining and defending engineering decisions |
| [FAQ](docs/FAQ.md) | Common operational questions |

## Validation

The core tools use the Python standard library only. pytest and ruff are declared in the `dev` extra:

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 -m ruff check tools tests .github/quality
```

GitHub Actions installs that extra, runs pytest on Python 3.8, 3.10, 3.12, and 3.13, runs ruff on 3.12, and uploads an audit report.

## Engineering safeguards

- Distinguish measured results, expert judgment, and untested proposals.
- Record sources, licenses, and access dates for externally sourced content.
- Remove credentials, confidential links, and private personal data before release.
- State voltage ranges, current limits, isolation, protection, and environmental conditions for hardware tests.
- Treat protocol utilities as data/transport checks only. Startup, emergency stop, and physical shutdown must have an independent safety path.

See [contribution guidance](CONTRIBUTING.md). Licensed under [MIT](LICENSE).
