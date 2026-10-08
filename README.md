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

GitHub Actions runs the standard-library Python tests and uploads an audit report. No mandatory external Python dependencies are required for the core tools.

## Engineering safeguards

- Distinguish measured results, expert judgment, and untested proposals.
- Record sources, licenses, and access dates for externally sourced content.
- Remove credentials, confidential links, and private personal data before release.
- State voltage ranges, current limits, isolation, protection, and environmental conditions for hardware tests.
- Treat protocol utilities as data/transport checks only. Startup, emergency stop, and physical shutdown must have an independent safety path.

See [contribution guidance](CONTRIBUTING.md). Licensed under [MIT](LICENSE).
