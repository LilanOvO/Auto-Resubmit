import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auto_resubmit.pipeline import _stabilize_target_style_files


class PipelineTests(unittest.TestCase):
    def test_stabilize_target_style_files_is_noop_for_acl(self) -> None:
        root = Path("test_acl_style_patch")
        root.mkdir(exist_ok=True)
        style_path = root / "acl.sty"
        original = r"""
\ifacl@linenumbers
  \usepackage[switch,mathlines]{lineno}
  \AtBeginDocument{\linenumbers}
\fi
""".strip()
        style_path.write_text(original, encoding="utf-8")

        warnings = _stabilize_target_style_files(root, "acl")
        patched = style_path.read_text(encoding="utf-8")
        self.assertEqual(patched, original)
        self.assertFalse(warnings)

        style_path.unlink()
        root.rmdir()


if __name__ == "__main__":
    unittest.main()
