# ti-cup-resources

**电子设计竞赛可复用资源、通信工具、模板与仓库质量工具**

[![Resource quality](https://github.com/yniantongtian-oss/ti-cup-resources/actions/workflows/ci.yml/badge.svg)](https://github.com/yniantongtian-oss/ti-cup-resources/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

本仓库提供可直接复制使用的项目管理模板、复盘模板、RS485/Modbus RTU 调试工具，以及零第三方依赖的仓库审计工具。目标是让参赛资料具备可追溯、可复现、可协作和可公开的基础质量。

## 立即可用

### 仓库审计工具

检查 README、许可证、`.gitignore`、大文件、疑似密钥和 Markdown 本地链接：

```bash
python3 tools/project_audit.py /path/to/project
python3 tools/project_audit.py . --format json --output audit.json
python3 tools/project_audit.py . --strict
```

默认只在 `--strict` 且发现错误时返回非零状态，适合逐步接入已有项目。

### Modbus RTU 帧工具

生成标准请求、验证 CRC、解析 03/04 功能码响应，不依赖串口库：

```bash
python3 tools/modbus_rtu.py read 1 0 10
python3 tools/modbus_rtu.py read 1 0 8 --input
python3 tools/modbus_rtu.py write 1 1 1000
python3 tools/modbus_rtu.py parse "01 04 02 00 2A 39 9B"
```

该模块可直接导入 PySerial、WPF/Python 联调程序或自动化测试脚本。详细排错见 [`docs/MODBUS_DEBUGGING_GUIDE.md`](docs/MODBUS_DEBUGGING_GUIDE.md)。

### 项目与评审模板

- [`templates/project-plan/`](templates/project-plan/)：BOM、测试记录、风险登记表
- [`templates/design-review-checklist.md`](templates/design-review-checklist.md)：需求、硬件、固件、通信、测试和答辩全流程评审
- [`templates/competition-schedule.csv`](templates/competition-schedule.csv)：从需求拆解到现场彩排的执行计划
- [`experience/retrospective-template.md`](experience/retrospective-template.md)：结构化赛后复盘
- [`docs/LEARNING_PATH.md`](docs/LEARNING_PATH.md)：学习路径
- [`docs/COMMON_PITFALLS.md`](docs/COMMON_PITFALLS.md)：常见问题
- [`docs/SAFETY_NOTES.md`](docs/SAFETY_NOTES.md)：实验安全
- [`docs/REFERENCE_MATERIALS.md`](docs/REFERENCE_MATERIALS.md)：参考资料整理原则
- [`docs/ANSWER_DEFENSE_TIPS.md`](docs/ANSWER_DEFENSE_TIPS.md)：答辩建议
- [`docs/FAQ.md`](docs/FAQ.md)：常见问答

## 自动化质量检查

GitHub Actions 会运行全部 Python 标准库单元测试，并生成当前仓库的审计报告作为构建附件。工具不要求安装第三方依赖。

## 内容原则

- 明确区分实测结果、经验判断和待验证方案。
- 外部内容注明来源、许可证和访问日期。
- 公开前移除个人信息、内部链接、账号凭据和无授权材料。
- 涉及硬件实验时写明电压范围、限流、隔离、保护和测试条件。
- 通信工具只负责帧与数据正确性；启动、急停和硬件关断不能依赖远程通信。

贡献方式见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。本项目采用 [MIT License](LICENSE)。
