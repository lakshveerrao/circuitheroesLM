from pathlib import Path
import unittest

from pbl_lm import __version__
from pbl_lm.cli import ARCHIVE_URL, _safe_relative


class PblLmPackageTests(unittest.TestCase):
    def test_version_matches_release_tag(self):
        self.assertEqual(__version__, "0.2.0")
        self.assertTrue(ARCHIVE_URL.endswith("/pbl-v0.2.0.zip"))

    def test_archive_paths_are_scoped_and_safe(self):
        self.assertEqual(_safe_relative("repo/pbl", "repo"), Path("pbl"))
        self.assertIsNone(_safe_relative("repo/folder/", "repo"))
        self.assertIsNone(_safe_relative("other/pbl", "repo"))
        with self.assertRaises(RuntimeError):
            _safe_relative("repo/../escape", "repo")


if __name__ == "__main__":
    unittest.main()
