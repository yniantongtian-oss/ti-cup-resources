# 工具 | Tools

核心脚本只使用 Python 标准库，可以直接 `python tools/<name>.py` 运行。安装仓库后也可以用 `ti-cup-audit`、`ti-cup-modbus`、`ti-cup-bom` 和 `ti-cup-prep`。

开发依赖在 `pyproject.toml` 的 `dev` 里：pytest 和 ruff。

## `project_audit.py`

检查 README、LICENSE、`.gitignore`、超过阈值的大文件、疑似私钥或令牌、以及 Markdown 里缺失或越出仓库的本地链接。围栏代码、行内代码和 HTML 注释里的链接不计入。`.env` 这类点文件会参与密钥扫描。

```bash
python3 tools/project_audit.py .
python3 tools/project_audit.py . --format json --output audit.json
python3 tools/project_audit.py . --large-file-mb 20 --strict
```

默认只报告，不因发现而失败。`--strict` 在存在 error 时返回非零。它不能代替人工审查或专业密钥扫描。疑似凭据要先从 Git 历史里移除并轮换。

## `modbus_rtu.py`

构造和检查 Modbus RTU 帧，不打开串口。

```bash
python3 tools/modbus_rtu.py read 1 0 10
python3 tools/modbus_rtu.py read 1 0 8 --input
python3 tools/modbus_rtu.py write 1 1 1000
python3 tools/modbus_rtu.py write 1 1 -1
python3 tools/modbus_rtu.py write-multi 2 4 1 2 65535
python3 tools/modbus_rtu.py parse "01 04 02 00 2A 39 9B" --slave 1
```

- 读请求的从站地址是 1..247。写请求允许广播地址 0。
- 起始地址加数量不能超过 65536。功能码 03/04 最多 125 个寄存器，功能码 16 最多 123 个。
- 负数按 int16 补码写入。0..65535 按 uint16 写入。
- 解析到异常帧时返回 1，并在 stderr 打印异常码。畸形帧返回 2。

## `bom.py`

列与 `templates/project-plan/bom.csv` 一致。金额用 `Decimal`。`do-not-use` 不计入合计。

```bash
python3 tools/bom.py check path/bom.csv
python3 tools/bom.py check path/bom.csv --format json --strict
python3 tools/bom.py lookup MSPM0G3507SRHBR
python3 tools/bom.py catalog --function amplifier
```

错误包括缺列、空 `id`、重复 `id`、数量不是正整数、价格不是非负数字。警告包括空料号、空状态、无法识别的状态、重复器件、币种缺失或不是 3 个字母、TI 厂商与目录不一致。目录摘自 2026-10-22 的 ti.com 页面，见 `ti_parts.py`。查找会把可订购后缀归到基型号，这不是封装或生命周期保证。

`check` 在有错误时返回 1，只有警告时返回 0。`--strict` 把警告也变成失败。找不到文件时返回 2。`lookup` 找不到时返回 1。

## `contest_prep.py`

给人和代理用的一次备赛汇总。终端里输出文字；stdout 不是终端，或者显式 `--format json` 时输出 JSON。

```bash
python3 tools/contest_prep.py .
python3 tools/contest_prep.py . --format json --today 2026-10-22
python3 tools/contest_prep.py . --checklist path/to/list.md --bom path/to/bom.csv --strict
```

默认按这个顺序找文件：

| 内容 | 路径 |
| --- | --- |
| 评审清单 | `design-review-checklist.md`，`templates/design-review-checklist.md` |
| BOM | `bom.csv`，`project-plan/bom.csv`，`templates/project-plan/bom.csv` |
| 进度 | `competition-schedule.csv`，`templates/competition-schedule.csv` |
| 风险 | `risk-register.csv`，`project-plan/risk-register.csv`，`templates/project-plan/risk-register.csv` |

进度表认 `计划结束` 或 `end`，状态认 `状态` 或 `status`。完成状态包括 `完成`、`已完成`、`done`、`complete`、`completed`、`closed`。结束日早于 `--today` 且未完成记为逾期。缺日期汇总成一条警告，不给每行各发一条。风险表检查 `likelihood_1_5 * impact_1_5` 是否等于 `score`。

JSON 的 `schema_version` 是 1。`ok` 只表示没有 error。警告在 `counts.warnings`。有 error 时进程返回 1；`--strict` 时有警告也返回 1。显式路径不存在时返回 2。代理应读 `ok` 和 `code`，不要依赖某句话的措辞。仓库审计消息目前是中文，`code` 是稳定字段。
