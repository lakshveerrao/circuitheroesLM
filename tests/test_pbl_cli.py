import json
import importlib.machinery
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PBL = ROOT / "pbl"
PBL_MODULE = importlib.machinery.SourceFileLoader("pbl_test_module", str(PBL)).load_module()


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

    def test_git_import_accepts_only_public_https_urls(self):
        self.assertEqual(
            PBL_MODULE.validate_git_url("https://github.com/example/firmware.git"),
            "https://github.com/example/firmware.git",
        )
        for unsafe in ("http://example.com/code.git", "file:///tmp/code", "https://user:secret@example.com/code.git"):
            with self.assertRaises(SystemExit):
                PBL_MODULE.validate_git_url(unsafe)

    def test_git_import_detects_idf_projects_and_risky_hooks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "CMakeLists.txt").write_text(
                "cmake_minimum_required(VERSION 3.16)\n"
                "include($ENV{IDF_PATH}/tools/cmake/project.cmake)\n"
                "project(sample)\n"
            )
            (root / "main").mkdir()
            safe = root / "main" / "component.cmake"
            safe.write_text("idf_component_register(SRCS main.c)\n")
            self.assertEqual(PBL_MODULE.locate_idf_project(root), root.resolve())
            self.assertEqual(PBL_MODULE.verify_build_files(root, PBL_MODULE.repository_files(root)), [])
            safe.write_text("execute_process(COMMAND bad)\n")
            findings = PBL_MODULE.verify_build_files(root, PBL_MODULE.repository_files(root))
            self.assertIn("CMake execute_process", findings[0])

    def test_display_compatibility_is_enforced(self):
        item = {"processors": ["esp32s3"], "boards": ["*"], "displays": ["st7789-spi"]}
        config = {"processor": "esp32s3", "board": "custom", "display": "waveshare-amoled-1.8-touch"}
        self.assertEqual(PBL_MODULE.compatibility(item, config), "display mismatch")



if __name__ == "__main__":
    unittest.main()
