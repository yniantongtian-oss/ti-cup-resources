#!/usr/bin/env python3
"""Audit a student engineering repository with no third-party dependencies."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlsplit

SKIP_DIRS = {".git", ".idea", ".vscode", "build", "dist", "node_modules", ".venv", "venv", "__pycache__"}
TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".h", ".hpp", ".ini", ".json", ".md", ".py", ".toml",
    ".txt", ".yaml", ".yml", ".tex", ".csv", ".sh", ".ps1", ".xml",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


def iter_files(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(item for item in dirs if item not in SKIP_DIRS)
        for name in sorted(files):
            yield Path(current) / name


def is_text_candidate(path: Path, max_bytes: int = 1_000_000) -> bool:
    try:
        return path.stat().st_size <= max_bytes and (path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Makefile", "Dockerfile"})
    except OSError:
        return False


def scan_structure(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    required = {"README.md": "项目入口说明", "LICENSE": "开源许可证"}
    for name, purpose in required.items():
        if not (root / name).is_file():
            findings.append(Finding("error", "missing-required-file", name, f"缺少{purpose}"))
    if not (root / ".gitignore").is_file():
        findings.append(Finding("warning", "missing-gitignore", ".gitignore", "建议添加工具链对应的忽略规则"))
    return findings


def scan_large_files(root: Path, limit_bytes: int) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(root):
        try:
            size = path.stat().st_size
        except OSError as exc:
            findings.append(Finding("warning", "unreadable-file", str(path.relative_to(root)), str(exc)))
            continue
        if size > limit_bytes:
            findings.append(Finding(
                "warning", "large-file", str(path.relative_to(root)),
                f"文件大小 {size / 1024 / 1024:.2f} MiB，建议使用 Git LFS 或发布附件",
            ))
    return findings


def secret_patterns() -> list[tuple[str, re.Pattern[str]]]:
    return [
        ("private-key", re.compile("-----BEGIN " + "(?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
        ("github-token", re.compile("gh" + r"[ps]_[A-Za-z0-9]{30,}")),
        ("aws-access-key", re.compile("AK" + r"IA[0-9A-Z]{16}")),
        ("assigned-secret", re.compile(
            r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"
        )),
    ]


def scan_secrets(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    patterns = secret_patterns()
    for path in iter_files(root):
        if not is_text_candidate(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        relative = str(path.relative_to(root))
        for name, pattern in patterns:
            if pattern.search(text):
                findings.append(Finding("error", "possible-secret", relative, f"检测到疑似 {name}；提交前请人工确认并轮换凭据"))
                break
    return findings


def markdown_targets(text: str) -> Iterable[str]:
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for match in pattern.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith("<") and raw.endswith(">"):
            raw = raw[1:-1]
        target = raw.split(maxsplit=1)[0]
        if target:
            yield target


def scan_markdown_links(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(root):
        if path.suffix.lower() != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for target in markdown_targets(text):
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith(("#", "mailto:")):
                continue
            relative_target = unquote(parsed.path)
            if not relative_target:
                continue
            resolved = (path.parent / relative_target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                findings.append(Finding("warning", "link-outside-root", str(path.relative_to(root)), f"链接指向仓库外部路径：{target}"))
                continue
            if not resolved.exists():
                findings.append(Finding("warning", "broken-local-link", str(path.relative_to(root)), f"本地链接不存在：{target}"))
    return findings


def audit(root: Path, large_file_mb: float = 10.0) -> list[Finding]:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    findings: list[Finding] = []
    findings.extend(scan_structure(root))
    findings.extend(scan_large_files(root, int(large_file_mb * 1024 * 1024)))
    findings.extend(scan_secrets(root))
    findings.extend(scan_markdown_links(root))
    return sorted(findings, key=lambda item: (item.severity != "error", item.path, item.code))


def markdown_report(root: Path, findings: list[Finding]) -> str:
    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    lines = [
        "# Repository Audit Report", "", f"- Root: `{root.resolve()}`",
        f"- Errors: **{errors}**", f"- Warnings: **{warnings}**", "",
    ]
    if not findings:
        lines.append("No findings. 基础检查未发现问题。")
    else:
        lines.extend(["| Severity | Code | Path | Message |", "|---|---|---|---|"])
        for item in findings:
            message = item.message.replace("|", "\\|")
            lines.append(f"| {item.severity} | `{item.code}` | `{item.path}` | {message} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--large-file-mb", type=float, default=10.0)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true", help="return non-zero when any error is found")
    args = parser.parse_args()

    try:
        findings = audit(args.root, args.large_file_mb)
    except (OSError, ValueError) as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        return 2

    report = (json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2) + "\n"
              if args.format == "json" else markdown_report(args.root, findings))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"report written to {args.output}")
    else:
        print(report, end="")
    return 1 if args.strict and any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
