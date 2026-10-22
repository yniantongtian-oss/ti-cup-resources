# 常见问题解答 | FAQ

**Q: 这个仓库和 ti-cup-energy-feedback-converter 有什么区别？**

A: 本仓库更偏向通用资源和经验分享，主仓库更偏向具体能量回馈变流器项目的代码和文档。

**Q: 我可以直接用这里的经验吗？**

A: 可以参考，但请结合自己的硬件和比赛要求进行调整。

**Q: 如何贡献内容？**

A: 欢迎通过 Pull Request 提交你的经验、工具推荐或模板。

**Q: 这个仓库会一直更新吗？**

A: 器件和软件版本会过期。`docs/REFERENCE_MATERIALS.md` 和 `tools/ti_parts.py` 写了核对日期。换届规则以全国大学生电子设计竞赛网站的当季通知为准。

**Q: 如何在本地跑测试？**

A: Python 3.8 到 3.13 都可以。`python -m pip install -e ".[dev]"` 安装 pytest 和 ruff，然后 `python -m pytest`。核心工具本身不依赖第三方包。CI 会再跑一遍 ruff。

**Q: BOM 和备赛检查怎么用？**

A: `python tools/bom.py check templates/project-plan/bom.csv` 检查清单，并对照 2026-10-22 从 ti.com 摘录的一小份目录。`python tools/contest_prep.py .` 在终端输出文字摘要；重定向或加上 `--format json` 时输出稳定 JSON。