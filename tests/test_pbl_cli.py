import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
PBL = ROOT / "pbl"


def run_pbl(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PBL), *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class PblCliTests(unittest.TestCase):
    def test_help_needs_no_optional_packages(self):
        result = run_pbl("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Projects by Laksh", result.stdout)
        self.assertNotIn("Pocket Board Lab", result.stdout)
        self.assertIn("pbl configure", result.stdout)

    def test_option_style_command_aliases_work(self):
        result = run_pbl("--run", "native-ai-probe", "--dry-run", "--yes")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Firmware tools", result.stdout)
        self.assertNotIn("idf.py", result.stdout)

    def test_catalog_projects_exist(self):
        catalog = json.loads((ROOT / "pbl_cli" / "test_codes.json").read_text())
        self.assertGreaterEqual(len(catalog["tests"]), 10)
        for item in catalog["tests"]:
            self.assertTrue((ROOT / item["project"]).is_dir(), item["id"])

    def test_test_codes_lists_hardware_examples(self):
        result = run_pbl("test-codes")
        self.assertEqual(result.returncode, 0)
        self.assertIn("microphone-meter", result.stdout)
        self.assertIn("agent-hardware-screen", result.stdout)
        self.assertIn("native-ai-probe", result.stdout)



if __name__ == "__main__":
    unittest.main()
