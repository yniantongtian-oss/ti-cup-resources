# ti-cup-resources

**电子设计竞赛可复用资源、模板与仓库质量工具**

[![Resource quality](https://github.com/yniantongtian-oss/ti-cup-resources/actions/workflows/ci.yml/badge.svg)](https://github.com/yniantongtian-oss/ti-cup-resources/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

本仓库提供可直接复制使用的项目管理模板、复盘模板，以及一个零第三方依赖的仓库审计工具。目标是让参赛资料具备可追溯、可复现、可协作和可公开的基础质量。

## 立即可用

### 仓库审计工具

检查 README、许可证、`.gitignore`、大文件、疑似密钥和 Markdown 本地链接：

```bash
python3 tools/project_audit.py /path/to/project
python3 tools/project_audit.py . --format json --output audit.json
python3 tools/project_audit.py . --strict
```

默认只在 `--strict` 且发现错误时返回非零状态，适合逐步接入已有项目。

### 项目模板

- [`templates/project-plan/`](templates/project-plan/)：BOM、测试记录、风险登记表
- [`experience/retrospective-template.md`](experience/retrospective-template.md)：结构化赛后复盘
- [`docs/LEARNING_PATH.md`](docs/LEARNING_PATH.md)：学习路径
- [`docs/COMMON_PITFALLS.md`](docs/COMMON_PITFALLS.md)：常见问题
- [`docs/SAFETY_NOTES.md`](docs/SAFETY_NOTES.md)：实验安全
- [`docs/REFERENCE_MATERIALS.md`](docs/REFERENCE_MATERIALS.md)：参考资料整理原则
- [`docs/ANSWER_DEFENSE_TIPS.md`](docs/ANSWER_DEFENSE_TIPS.md)：答辩建议
- [`docs/FAQ.md`](docs/FAQ.md)：常见问答

## 自动化质量检查

GitHub Actions 会运行审计工具的单元测试，并生成当前仓库的审计报告作为构建附件。测试仅使用 Python 标准库。

## 内容原则

- 明确区分实测结果、经验判断和待验证方案。
- 外部内容注明来源、许可证和访问日期。
- 公开前移除个人信息、内部链接、账号凭据和无授权材料。
- 涉及硬件实验时写明电压范围、限流、隔离、保护和测试条件。

贡献方式见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。本项目采用 [MIT License](LICENSE)。
