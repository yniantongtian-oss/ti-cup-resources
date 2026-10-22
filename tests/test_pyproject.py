import sys
import unittest
from pathlib import Path

import tools

ROOT = Path(__file__).resolve().parents[1]


class PyprojectTests(unittest.TestCase):
    @unittest.skipUnless(sys.version_info >= (3, 11), "tomllib is required to parse pyproject.toml")
    def test_dev_dependencies_and_scripts(self) -> None:
        import tomllib

        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(data["project"]["name"], "ti-cup-resources")
        self.assertEqual(data["project"]["version"], tools.__version__)
        self.assertEqual(data["project"]["requires-python"], ">=3.8")

        def package(requirement: str) -> str:
            return requirement.split(";")[0].split(">")[0].split("<")[0].split("=")[0].strip()

        dev = {package(item) for item in data["project"]["optional-dependencies"]["dev"]}
        self.assertEqual(dev, {"pytest", "ruff"})
        scripts = data["project"]["scripts"]
        self.assertEqual(scripts["ti-cup-prep"], "tools.contest_prep:main")
        self.assertEqual(scripts["ti-cup-bom"], "tools.bom:main")


if __name__ == "__main__":
    unittest.main()
