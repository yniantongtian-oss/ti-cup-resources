import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.project_audit import iter_files


class LinkBoundaryTests(unittest.TestCase):
    def test_audit_does_not_read_linked_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            linked = root / 'private.py'
            linked.write_text('PRIVATE_SENTINEL = 42\n')
            regular = root / 'normal.py'
            regular.write_text('answer = 42\n')
            original = Path.is_symlink
            with patch.object(Path, 'is_symlink', lambda path: path == linked or original(path)):
                self.assertEqual(list(iter_files(root)), [regular])


if __name__ == '__main__':
    unittest.main()
