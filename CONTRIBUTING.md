# Contributing Guide

感谢你愿意为 TI Cup 资源库做贡献！

## 可以贡献的内容

- 自己的比赛经验和踩过的坑
- 好用的工具和使用技巧
- 模板和示例文件
- 学习资源推荐
- 报告/答辩经验

## 开发检查

核心工具只使用 Python 标准库。pytest 和 ruff 写在 `pyproject.toml` 的 `dev` 额外依赖里。

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check tools tests .github/quality
python tools/project_audit.py . --strict
```

Python 3.8 到 3.13 都在 CI 矩阵里。3.8 使用 pytest 8.3，3.10 及以上使用 pytest 9。

## 提交方式

1. Fork 本仓库
2. 创建新分支
3. 添加或修改内容
4. 提交 Pull Request

我们欢迎所有有价值的贡献！