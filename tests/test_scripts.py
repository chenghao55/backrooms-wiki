"""CLI tests using isolated archives and standard-library fixtures."""

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


class ArchiveScriptsTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.working_dir = Path(temporary.name)
        self.project = self.working_dir / "archive"
        self.data = self.project / "data"
        self.levels = self.data / "levels"
        self.levels.mkdir(parents=True)
        self.index = self.data / "index.json"
        self.scripts = self.project / "scripts"
        self.scripts.mkdir()
        for script in ("validate.py", "build_index.py"):
            shutil.copyfile(SCRIPTS / script, self.scripts / script)

    def run_script(self, script, *args, code=0, diagnostic=None):
        completed = subprocess.run(
            [sys.executable, "-B", str(self.scripts / script), *args],
            cwd=self.working_dir,
            capture_output=True,
            encoding="utf-8",
        )
        output = completed.stdout + completed.stderr
        self.assertEqual(completed.returncode, code, output)
        self.assertIn("個層級", completed.stdout)
        if diagnostic:
            self.assertIn(diagnostic, output)
        return completed

    def validate(self, *args, **kwargs):
        return self.run_script("validate.py", *args, **kwargs)

    def build(self, **kwargs):
        return self.run_script("build_index.py", **kwargs)

    def write_level(self, record, directory=None):
        level = self.levels / (directory or f"level-{record['id']}")
        level.mkdir(exist_ok=True)
        self.write_json(level / "index.json", record)
        return level

    def write_json(self, path, data):
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def placeholder(self, ident):
        return self.write_level({"id": ident, "status": "placeholder"})

    def complete(self):
        return {
            "id": "2",
            "status": "complete",
            "name": "測試層級",
            "language": "zh-TW",
            "source_url": "https://backrooms-wiki.wikidot.com/level-2",
            "sections": [{"title": "描述", "blocks": [{"type": "text", "content": "測試內容"}]}],
            "entrances": [],
            "exits": [],
        }

    def image_level(self, src="images/pool.jpg"):
        record = self.complete()
        record["sections"][0]["blocks"].append({
            "type": "image",
            "src": src,
            "caption": "測試圖片",
            "source_url": "https://example.test/pool.jpg",
            "license": "測試授權",
        })
        return record

    def test_valid_complete_level_with_image(self):
        level = self.write_level(self.image_level())
        image = level / "images" / "pool.jpg"
        image.parent.mkdir()
        image.write_bytes(b"image fixture")
        result = self.validate("--source-only")
        self.assertIn("0 個警告", result.stdout)

    def test_placeholder_and_empty_sections_warning(self):
        self.placeholder("10")
        record = self.complete()
        record["sections"] = []
        self.write_level(record)
        self.validate("--source-only", diagnostic="完整層級沒有文章段落")
        self.build(diagnostic="已產生")
        self.validate()

    def test_source_only_does_not_require_or_read_index(self):
        self.placeholder("10")
        self.validate("--source-only")
        self.validate(code=1, diagnostic="data/index.json：缺少")
        self.index.write_text("{broken", encoding="utf-8")
        self.validate("--source-only")
        self.validate(code=1, diagnostic="data/index.json：JSON 語法無效")

    def test_invalid_source_json_and_unsupported_values(self):
        level = self.placeholder("2")
        for payload in ('{broken', '{"id":"2","id":"3"}', '{"id":NaN}', "[]"):
            with self.subTest(payload=payload):
                (level / "index.json").write_text(payload, encoding="utf-8")
                self.validate("--source-only", code=1, diagnostic="level-2/index.json")

    def test_missing_required_field(self):
        record = self.complete()
        del record["language"]
        self.write_level(record)
        self.validate("--source-only", code=1, diagnostic=".language：缺少必要欄位")

    def test_invalid_status_and_field_types(self):
        for status in ("draft", [], None):
            with self.subTest(status=status):
                record = self.complete()
                record["status"] = status
                self.write_level(record)
                self.validate("--source-only", code=1, diagnostic=".status：")
        record = self.complete()
        record["sections"] = {}
        self.write_level(record)
        self.validate("--source-only", code=1, diagnostic=".sections：必須是陣列")

    def test_placeholder_rejects_article_content(self):
        self.write_level({"id": "2", "status": "placeholder", "sections": []})
        self.validate("--source-only", code=1, diagnostic="佔位層級只允許 id 和 status")

    def test_duplicate_id_and_directory_mismatch(self):
        self.placeholder("2")
        self.write_level({"id": "2", "status": "placeholder"}, directory="level-3")
        result = self.validate("--source-only", code=1, diagnostic="層級 ID 2 重複")
        self.assertIn("目錄名稱必須與 ID 一致", result.stderr)

    def test_malformed_directory_flat_file_and_missing_level_index(self):
        (self.levels / "level-special").mkdir()
        (self.levels / "level-3").mkdir()
        self.write_json(self.levels / "level-4.json", {"id": "4", "status": "placeholder"})
        result = self.validate("--source-only", code=1, diagnostic="level-special：層級必須使用")
        self.assertIn("level-3/index.json：缺少", result.stderr)
        self.assertIn("level-4.json：層級必須使用", result.stderr)

    def test_missing_image_file(self):
        self.write_level(self.image_level())
        self.validate("--source-only", code=1, diagnostic="找不到圖片檔案")

    def test_unsafe_image_paths(self):
        for path in ("../outside.jpg", "images/../outside.jpg", "images\\pool.jpg",
                     "C:/pool.jpg", "/images/pool.jpg", "images/C:pool.jpg"):
            with self.subTest(path=path):
                self.write_level(self.image_level(path))
                self.validate("--source-only", code=1, diagnostic="安全的相對路徑")

    def test_source_urls_and_image_metadata(self):
        record = self.image_level()
        record["source_url"] = "https://backrooms-wiki.wikidot.com@other.test/level-2"
        image = record["sections"][0]["blocks"][-1]
        image["src"] = ""
        image["source_url"] = "https://example.test:wrong/image"
        del image["license"]
        self.write_level(record)
        result = self.validate("--source-only", code=1, diagnostic="上的有效 HTTPS 網址")
        self.assertIn("圖片來源必須是有效", result.stderr)
        self.assertIn(".license：圖片欄位必須是非空字串", result.stderr)

    def test_unsupported_block(self):
        record = self.complete()
        record["sections"][0]["blocks"][0]["type"] = ["audio"]
        self.write_level(record)
        self.validate("--source-only", code=1, diagnostic="區塊類型必須是 text 或 image")

    def test_missing_exit_target(self):
        record = self.complete()
        record["exits"] = [{"target": "95", "description": "測試出口"}]
        self.write_level(record)
        self.validate("--source-only", code=1, diagnostic="出口目標 95 找不到")

    def test_valid_placeholder_destination_and_descriptive_connections(self):
        record = self.complete()
        record["entrances"] = [{"target": "90", "description": "測試入口"}]
        record["exits"] = [
            {"target": "95", "description": "測試出口"},
            {"description": "無編號的出口"},
        ]
        level = self.write_level(record)
        self.placeholder("95")
        self.validate("--source-only")
        self.build()
        self.validate()
        self.assertEqual(json.loads((level / "index.json").read_text(encoding="utf-8")), record)

    def test_invalid_connection_types(self):
        record = self.complete()
        record["exits"] = [{"target": None, "description": 123}]
        self.write_level(record)
        result = self.validate("--source-only", code=1, diagnostic=".exits[0].target：")
        self.assertIn(".exits[0].description：", result.stderr)

    def test_numeric_sort_and_exact_index_shape_from_different_working_directory(self):
        self.placeholder("10")
        self.write_level(self.complete())
        self.validate("--source-only")
        self.build()
        self.validate()
        self.assertEqual(json.loads(self.index.read_text(encoding="utf-8")), {
            "schema_version": 1,
            "levels": [
                {"id": "2", "name": "測試層級", "status": "complete",
                 "path": "levels/level-2/index.json"},
                {"id": "10", "name": None, "status": "placeholder",
                 "path": "levels/level-10/index.json"},
            ],
        })

    def test_index_is_deterministic_and_identical_contents_are_not_rewritten(self):
        self.write_level(self.complete())
        self.build()
        original = self.index.read_bytes()
        self.assertIn("測試層級".encode("utf-8"), original)
        self.index.unlink()
        self.build()
        self.assertEqual(self.index.read_bytes(), original)
        modified = self.index.stat().st_mtime_ns
        self.build(diagnostic="無須重寫")
        self.assertEqual(self.index.stat().st_mtime_ns, modified)

    def test_build_preserves_index_on_validation_failure(self):
        self.placeholder("10")
        self.build()
        original = self.index.read_bytes()
        modified = self.index.stat().st_mtime_ns
        record = self.complete()
        record["exits"] = [{"target": "9", "description": "測試出口"}]
        self.write_level(record)
        self.build(code=1, diagnostic="出口目標 9 找不到")
        self.assertEqual(self.index.read_bytes(), original)
        self.assertEqual(self.index.stat().st_mtime_ns, modified)
        self.assertEqual(list(self.data.glob(".index-*.tmp")), [])

    def test_failed_atomic_replace_keeps_index_and_removes_temporary_file(self):
        self.placeholder("10")
        self.build()
        original = self.index.read_bytes()
        self.placeholder("11")
        (self.scripts / "fail_replace.py").write_text(
            'from pathlib import Path\n'
            'from unittest.mock import patch\n'
            'from build_index import main, run_cli\n'
            'with patch.object(Path, "replace", side_effect=OSError("simulated failure")):\n'
            '    run_cli(main)\n',
            encoding="utf-8",
        )
        self.run_script("fail_replace.py", code=2, diagnostic="檔案系統作業失敗")
        self.assertEqual(self.index.read_bytes(), original)
        self.assertEqual(list(self.data.glob(".index-*.tmp")), [])

    def test_stale_missing_and_extra_index_entries(self):
        record = self.complete()
        self.write_level(record)
        old_level = self.placeholder("3")
        self.build()
        original = self.index.read_bytes()

        record["name"] = "新名稱"
        self.write_level(record)
        (old_level / "index.json").unlink()
        old_level.rmdir()
        self.placeholder("10")

        result = self.validate(code=1, diagnostic="層級 2 的索引項目與來源資料不一致")
        self.assertIn("索引缺少層級 10", result.stderr)
        self.assertIn("不存在的層級 3", result.stderr)
        self.assertEqual(self.index.read_bytes(), original)

    def test_invalid_index_types_and_order(self):
        self.placeholder("2")
        self.placeholder("10")
        self.build()
        index = json.loads(self.index.read_text(encoding="utf-8"))
        index["schema_version"] = True
        index["levels"][0]["name"] = ""
        self.write_json(self.index, index)
        result = self.validate(code=1, diagnostic="索引版本必須是整數 1")
        self.assertIn("佔位層級名稱必須是 null", result.stderr)

        index["schema_version"] = 1
        index["levels"][0]["name"] = None
        index["levels"].reverse()
        self.write_json(self.index, index)
        self.validate(code=1, diagnostic="按 ID 的數值升冪排列")

    def test_missing_source_directory_is_filesystem_error(self):
        self.levels.rmdir()
        self.validate("--source-only", code=2, diagnostic="檔案系統作業失敗")
        self.build(code=2, diagnostic="檔案系統作業失敗")
        self.assertFalse(self.index.exists())


if __name__ == "__main__":
    unittest.main()
