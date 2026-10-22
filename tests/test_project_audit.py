import stat
import tempfile
import unittest
from pathlib import Path

from tools.project_audit import audit, iter_files


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

    def test_ignores_fenced_comments_and_external_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root)
            (root / "README.md").write_text(
                "See [Guide](docs/guide.md).\n\n"
                "```md\n[Missing](docs/missing.md)\n```\n\n"
                "Inline `[Also missing](docs/nope.md)` is an example.\n"
                "[Site](//example.com/path)\n"
                "<!-- [Old](docs/old.md) -->\n",
                encoding="utf-8",
            )
            self.assertEqual(audit(root), [])

    def test_link_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root)
            (root / "README.md").write_text("[Out](../outside.md)\n", encoding="utf-8")
            self.assertIn("link-outside-root", {item.code for item in audit(root)})

    def test_env_file_and_encrypted_private_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root)
            (root / ".env").write_text("pass" + "word=abcdefghijkl\n", encoding="utf-8")
            (root / "notes.txt").write_text("-----BEGIN " + "ENCRYPTED PRIVATE KEY-----\n", encoding="utf-8")
            messages = " ".join(item.message for item in audit(root))
            self.assertIn("assigned-secret", messages)
            self.assertIn("private-key", messages)

    def test_reports_distinct_secret_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root)
            token = "gh" + "p_" + ("a" * 36)
            (root / "leak.py").write_text("-----BEGIN " + "RSA PRIVATE KEY-----\n" + token + "\n", encoding="utf-8")
            messages = " ".join(item.message for item in audit(root))
            self.assertIn("private-key", messages)
            self.assertIn("github-token", messages)

    def test_missing_reparse_attribute_does_not_crash(self) -> None:
        original = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", None)
        if original is not None:
            delattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT")
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "README.md").write_text("ok\n", encoding="utf-8")
                self.assertEqual([path.name for path in iter_files(root)], ["README.md"])
        finally:
            if original is not None:
                stat.FILE_ATTRIBUTE_REPARSE_POINT = original

    def test_rejects_bad_size_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root)
            with self.assertRaises(ValueError):
                audit(root, large_file_mb=float("nan"))
            with self.assertRaises(ValueError):
                audit(root, large_file_mb=-1)
            with self.assertRaises(ValueError):
                audit(root, large_file_mb=True)


if __name__ == "__main__":
    unittest.main()
