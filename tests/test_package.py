import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from package import build_package, validate_package


class PackageTest(unittest.TestCase):
    def test_markdown_becomes_complete_visual_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "article.md"
            source.write_text("# 管理从会后开始\n\n## 先明确责任\n会议不是结束。\n\n## 再推进动作\n责任要落到人。\n", encoding="utf-8")
            target = build_package(source, root / "out")
            self.assertEqual(validate_package(target), [])
            manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["assets"]), 3)
            self.assertIn("media/body-img-01.png", (target / "article.md").read_text(encoding="utf-8"))
            self.assertTrue((target / "小红书.md").exists())
            (target / "media" / "cover.png").unlink()
            self.assertIn("缺少图片：cover.png", validate_package(target))


if __name__ == "__main__":
    unittest.main()
