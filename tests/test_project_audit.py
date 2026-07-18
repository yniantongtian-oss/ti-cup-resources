import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from project_audit import audit  # noqa: E402


class ProjectAuditTests(unittest.TestCase):
    def make_repo(self, root: Path) -> None:
        (root / "README.md").write_text("[Guide](docs/guide.md)\n", encoding="utf-8")
        (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
        (root / ".gitignore").write_text("build/\n", encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")

    def test_clean_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root)
            self.assertEqual(audit(root), [])

    def test_missing_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            findings = audit(Path(directory))
            codes = {item.code for item in findings}
            self.assertIn("missing-required-file", codes)
            self.assertIn("missing-gitignore", codes)

    def test_broken_markdown_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root)
            (root / "README.md").write_text("[Missing](docs/missing.md)\n", encoding="utf-8")
            self.assertIn("broken-local-link", {item.code for item in audit(root)})

    def test_secret_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root)
            (root / "config.py").write_text('api_' + 'key = "abcdefghijklmnop"\n', encoding="utf-8")
            self.assertIn("possible-secret", {item.code for item in audit(root)})

    def test_large_file_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root)
            (root / "capture.bin").write_bytes(b"x" * 32)
            self.assertIn("large-file", {item.code for item in audit(root, large_file_mb=0.00001)})


if __name__ == "__main__":
    unittest.main()
