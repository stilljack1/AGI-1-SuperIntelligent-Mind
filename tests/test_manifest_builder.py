from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestManifestBuilder(unittest.TestCase):
    def test_build_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "manifest.json"
            subprocess.run(
                [sys.executable, str(ROOT / "build_manifests.py"), "--mode", "staging", "--output", str(output)],
                check=True,
                cwd=str(ROOT),
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "staging")
            self.assertGreaterEqual(len(payload["executives"]), 4)
            self.assertIn("signature", payload)


if __name__ == "__main__":
    unittest.main()
