import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.bom import check_bom, main
from tools.ti_parts import CHECKED, catalog, lookup

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "project-plan" / "bom.csv"
HEADER = (
    "id,category,manufacturer,part_number,description,quantity,"
    "unit_price,currency,supplier,alternative_part,status,notes\n"
)


class CatalogTests(unittest.TestCase):
    def test_lookup_orderables_and_families(self) -> None:
        self.assertEqual(lookup("mspm0g3507")["part_number"], "MSPM0G3507")
        self.assertEqual(lookup("MSPM0G3507SRHBR")["part_number"], "MSPM0G3507")
        self.assertEqual(lookup("TLV9062IDR")["function"], "amplifier")
        self.assertEqual(lookup("LP-MSPM0G3507")["function"], "dev-kit")
        self.assertEqual(lookup("REF35250")["part_number"], "REF35")
        self.assertIsNone(lookup("MSPM0G3506"))
        self.assertIsNone(lookup("TPS62932"))
        self.assertIsNone(lookup(""))

    def test_catalog_is_a_copy_of_checked_ti_pages(self) -> None:
        found = lookup("TLV9062")
        assert found is not None
        found["description"] = "mutated"
        self.assertNotEqual(lookup("TLV9062")["description"], "mutated")
        mcus = [item["part_number"] for item in catalog("mcu")]
        self.assertEqual(mcus, ["MSPM0G3507", "TMS320F280039C"])
        self.assertEqual(catalog("missing"), [])
        for item in catalog():
            self.assertTrue(item["url"].startswith("https://www.ti.com/"))
            self.assertEqual(item["verified"], CHECKED)
            self.assertNotIn("family_prefix", item)


class BomTests(unittest.TestCase):
    def test_template_has_warnings_only(self) -> None:
        report = check_bom(TEMPLATE)
        self.assertTrue(report.ok)
        self.assertEqual(report.rows, 3)
        self.assertEqual(report.cost, {})
        self.assertEqual([item.code for item in report.findings], ["incomplete-part"] * 3)

    def test_cost_catalog_and_duplicates(self) -> None:
        text = (
            HEADER
            + "BOM-001,mcu,TI,MSPM0G3507,mcu,2,10.5,CNY,,,ordered,\n"
            + "BOM-001,mcu,TI,TLV9062,dup,1,,CNY,,,ordered,\n"
            + "BOM-003,driver,TI,UCC27524,old,1,1,CNY,,,ordered,\n"
            + "BOM-004,amp,ST,MSPM0G3507,wrong maker,1,1,USD,,,ordered,\n"
            + "BOM-005,drop,TI,TLV9062,skip,4,3,USD,,,do-not-use,\n"
            + "BOM-006,bad,TI,INA181,bad qty,0,1,CNY,,,ordered,\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bom.csv"
            path.write_text(text, encoding="utf-8")
            report = check_bom(path)
        codes = {item.code for item in report.findings}
        self.assertFalse(report.ok)
        self.assertIn("duplicate-id", codes)
        self.assertIn("ti-part-unlisted", codes)
        self.assertIn("catalog-manufacturer-mismatch", codes)
        self.assertIn("bad-quantity", codes)
        self.assertEqual(report.cost, {"CNY": "22.0", "USD": "1"})

    def test_cli_lookup_and_strict_template(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main(["lookup", "THVD1450", "--format", "json"]), 0)
        self.assertTrue(json.loads(stdout.getvalue())["found"])
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main(["lookup", "LM741", "--format", "json"]), 1)
        self.assertFalse(json.loads(stdout.getvalue())["found"])
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(main(["check", str(TEMPLATE), "--format", "json"]), 0)
        self.assertTrue(json.loads(stdout.getvalue())["ok"])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["check", str(TEMPLATE), "--format", "json", "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
