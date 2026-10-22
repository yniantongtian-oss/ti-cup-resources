import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

from tools.contest_prep import main, prepare

ROOT = Path(__file__).resolve().parents[1]


class ContestPrepTests(unittest.TestCase):
    def test_repository_templates_have_no_errors(self) -> None:
        report = prepare(ROOT, today=date(2026, 10, 22))
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["errors"], 0)
        self.assertGreater(report["counts"]["warnings"], 0)
        self.assertEqual(report["audit"]["findings"], [])
        self.assertEqual(report["risks"]["findings"], [])
        self.assertEqual(report["checklist"]["findings"], [])
        self.assertEqual(report["checklist"]["checked"], 0)
        self.assertGreater(report["checklist"]["unchecked"], 0)
        self.assertFalse(report["checklist"]["complete"])
        self.assertEqual([item.code for item in report["bom"]["findings"]], ["incomplete-part"] * 3)
        self.assertEqual([item.code for item in report["schedule"]["findings"]], ["schedule-undated"])
        self.assertGreater(report["schedule"]["undated"], 0)
        self.assertEqual(report["schedule"]["overdue"], 0)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main([str(ROOT), "--format", "json", "--today", "2026-10-22"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(stdout.getvalue())["ok"])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(ROOT), "--format", "json", "--strict", "--today", "2026-10-22"]), 1)

    def test_fixture_counts_overdue_score_and_fenced_boxes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / ".gitignore").write_text("build/\n", encoding="utf-8")
            (root / "design-review-checklist.md").write_text(
                "```\n- [x] ignored\n```\n- [x] done\n- [ ] open\n- [X] also\n",
                encoding="utf-8",
            )
            (root / "bom.csv").write_text(
                "id,category,manufacturer,part_number,description,quantity,"
                "unit_price,currency,supplier,alternative_part,status,notes\n"
                "BOM-001,mcu,TI,MSPM0G3507,mcu,2,10.5,CNY,,,ordered,\n",
                encoding="utf-8",
            )
            (root / "competition-schedule.csv").write_text(
                "id,task,end,status\n"
                "1,finished,2020-01-01,done\n"
                "2,late,2020-01-02,todo\n"
                "3,open,,todo\n"
                "4,bad,2026-13-40,todo\n",
                encoding="utf-8",
            )
            (root / "risk-register.csv").write_text(
                "risk_id,likelihood_1_5,impact_1_5,score\n"
                "RISK-001,3,5,15\n"
                "RISK-002,3,4,16\n"
                "RISK-003,6,4,24\n",
                encoding="utf-8",
            )
            report = prepare(root, today=date(2026, 10, 22))
            self.assertFalse(report["ok"])
            self.assertEqual(report["checklist"]["checked"], 2)
            self.assertEqual(report["checklist"]["unchecked"], 1)
            self.assertEqual(report["bom"]["cost"], {"CNY": "21.0"})
            self.assertEqual(report["bom"]["findings"], [])
            self.assertEqual(report["schedule"]["overdue"], 1)
            self.assertEqual(report["schedule"]["undated"], 1)
            codes = {item.code for item in report["schedule"]["findings"]}
            self.assertEqual(codes, {"schedule-overdue", "schedule-undated", "schedule-bad-date"})
            risk_codes = {item.code for item in report["risks"]["findings"]}
            self.assertEqual(risk_codes, {"risk-score-mismatch", "risk-factor-range"})
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main([str(root), "--format", "json", "--today", "2026-10-22"]), 1)
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                missing = root / "missing.md"
                self.assertEqual(main([str(root), "--checklist", str(missing), "--format", "json"]), 2)
            self.assertIn("missing.md", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
