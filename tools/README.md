# 工具 | Tools

## `project_audit.py`

零第三方依赖的工程仓库基础审计工具，可检查：

- README、LICENSE 和 `.gitignore`
- 超过指定阈值的大文件
- 常见私钥、访问令牌和硬编码密钥特征
- Markdown 中不存在或越出仓库的本地链接

```bash
python3 tools/project_audit.py .
python3 tools/project_audit.py . --format json --output audit.json
python3 tools/project_audit.py . --large-file-mb 20 --strict
```

工具只做启发式检查，不能替代人工代码审查、专业密钥扫描或许可证审计。检测到疑似凭据时，应先从 Git 历史中移除并立即轮换，而不是只删除当前文件。
