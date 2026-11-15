"""Validate the archive's source records and generated index."""

import argparse
import json
import re
import stat
import sys
from dataclasses import dataclass, field
from ipaddress import IPv6Address
from pathlib import Path
from urllib.parse import urlsplit

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ARTICLE_HOST = "backrooms-wiki.wikidot.com"
STATUSES = ("complete", "placeholder")
INDEX_FIELDS = {"id", "name", "status", "path"}


@dataclass
class Validation:
    level_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    filesystem_errors: list[str] = field(default_factory=list)
    levels: dict[str, dict] = field(default_factory=dict)

    def error(self, location, message):
        self.errors.append(f"{location}：{message}")

    def warn(self, location, message):
        self.warnings.append(f"{location}：{message}")

    def filesystem_error(self, location, exc):
        self.filesystem_errors.append(f"{location}：檔案系統作業失敗（{exc}）")

    def report(self):
        for message in self.errors + self.filesystem_errors:
            print(f"錯誤：{message}", file=sys.stderr)
        for message in self.warnings:
            print(f"警告：{message}", file=sys.stderr)
        error_count = len(self.errors) + len(self.filesystem_errors)
        print(f"共檢查 {self.level_count} 個層級，{error_count} 個錯誤，{len(self.warnings)} 個警告。")
        if self.filesystem_errors:
            return 2
        return 1 if self.errors else 0


def supported_id(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9]+", value) is not None


def id_sort_key(ident):
    # Compare the numeric value without changing the stored identifier.
    digits = ident.lstrip("0")
    return len(digits), digits, ident


def nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def valid_url(value, article=False):
    if not isinstance(value, str) or re.search(
        r'''[\s\x00-\x1f\x60\x7f<>"{}|\\^\ud800-\udfff]|%(?![0-9a-fA-F]{2})''', value
    ):
        return False
    try:
        url = urlsplit(value)
        host = url.hostname
        credentials, _, authority = url.netloc.rpartition("@")
        if not host or "@" in credentials or authority.endswith(":") or url.port == 0:
            return False
        if article:
            return url.scheme == "https" and host == ARTICLE_HOST
        if url.scheme not in ("http", "https"):
            return False
        if ":" in host:
            if not re.fullmatch(r"\[[^\]]+\](?::[0-9]+)?", authority):
                return False
            IPv6Address(host)
            return True
        labels = host.removesuffix(".").encode("idna").decode("ascii").split(".")
        return all(re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", label)
                   for label in labels)
    except ValueError:
        return False


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"重複的物件欄位 {key!r}")
        obj[key] = value
    return obj


def reject_constant(value):
    raise ValueError(f"不支援的 JSON 數值 {value}")


def read_object(path, location, result):
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            result.error(location, "必須是一般 JSON 檔案")
            return None
        obj = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=unique_object, parse_constant=reject_constant)
    except FileNotFoundError:
        result.error(location, "缺少必要的 JSON 檔案")
        return None
    except json.JSONDecodeError as exc:
        result.error(location, f"JSON 語法無效（第 {exc.lineno} 行，第 {exc.colno} 欄）")
        return None
    except UnicodeDecodeError:
        result.error(location, "JSON 檔案必須使用 UTF-8 編碼")
        return None
    except ValueError as exc:
        result.error(location, f"無效的 JSON（{exc}）")
        return None
    except RecursionError:
        result.error(location, "JSON 巢狀層數過多")
        return None
    except OSError as exc:
        result.filesystem_error(location, exc)
        return None
    if not isinstance(obj, dict):
        result.error(location, "JSON 最外層必須是物件")
        return None
    return obj


def require_fields(obj, fields, location, result):
    for key in fields:
        if key not in obj:
            result.error(f"{location}.{key}", "缺少必要欄位")


def validate_image_path(value, directory, location, result):
    parts = value.split("/")
    if (len(parts) < 2 or parts[0] != "images"
            or any(part in ("", ".", "..") for part in parts)
            or re.search(r'[\\:<>"|?*\x00-\x1f\ud800-\udfff]', value)
            or any(part.endswith((" ", ".")) for part in parts)):
        result.error(location, "圖片路徑必須位於該層級的 images/ 目錄，並使用安全的相對路徑")
        return

    try:
        image_root = directory.resolve() / "images"
        image = (directory / value).resolve()
        if image == image_root or not image.is_relative_to(image_root):
            result.error(location, "圖片路徑解析後超出該層級的 images/ 目錄")
        elif not stat.S_ISREG(image.stat().st_mode):
            result.error(location, f"圖片路徑須指向檔案（{value!r}）")
    except (FileNotFoundError, NotADirectoryError):
        result.error(location, f"找不到圖片檔案（{value!r}）")
    except RuntimeError:
        result.error(location, f"無法解析圖片路徑（{value!r}）")
    except OSError as exc:
        result.filesystem_error(location, exc)


def validate_block(block, directory, location, result):
    if not isinstance(block, dict):
        result.error(location, "內容區塊必須是物件")
        return False

    kind = block.get("type")
    if kind == "text":
        if not isinstance(block.get("content"), str):
            result.error(f"{location}.content", "文字區塊必須提供字串內容")
    elif kind == "image":
        for key in ("src", "caption", "source_url", "license"):
            if not nonempty_string(block.get(key)):
                result.error(f"{location}.{key}", "圖片欄位必須是非空字串")
        if nonempty_string(block.get("source_url")) and not valid_url(block["source_url"]):
            result.error(f"{location}.source_url", "圖片來源必須是有效的 HTTP 或 HTTPS 網址")
        if nonempty_string(block.get("src")):
            validate_image_path(block["src"], directory, f"{location}.src", result)
    else:
        result.error(f"{location}.type", "區塊類型必須是 text 或 image")
    return kind == "image"


def validate_sections(sections, directory, location, result):
    if not sections:
        result.warn(location, "完整層級沒有文章段落")

    image_count = 0
    for index, section in enumerate(sections):
        section_location = f"{location}[{index}]"
        if not isinstance(section, dict):
            result.error(section_location, "段落必須是物件")
            continue
        if not nonempty_string(section.get("title")):
            result.error(f"{section_location}.title", "段落標題必須是非空字串")
        blocks = section.get("blocks")
        if not isinstance(blocks, list):
            result.error(f"{section_location}.blocks", "段落必須提供 blocks 陣列")
            continue
        for block_index, block in enumerate(blocks):
            block_location = f"{section_location}.blocks[{block_index}]"
            if validate_block(block, directory, block_location, result):
                image_count += 1
    if not image_count:
        result.warn(location, "文章沒有圖片")


def validate_connections(connections, location, result):
    for index, connection in enumerate(connections):
        connection_location = f"{location}[{index}]"
        if not isinstance(connection, dict):
            result.error(connection_location, "連線紀錄必須是物件")
            continue
        if not isinstance(connection.get("description"), str):
            result.error(f"{connection_location}.description", "連線必須提供字串說明")
        if "target" in connection:
            target_location = f"{connection_location}.target"
            target = connection["target"]
            if supported_id(target):
                yield target, target_location
            else:
                result.error(target_location, "目標必須是由 ASCII 數字組成的非空字串")


def validate_level(record, directory, location, result):
    status = record.get("status")
    if status not in STATUSES:
        result.error(f"{location}.status", "狀態必須是 complete 或 placeholder")
        return

    if status == "placeholder":
        for key in sorted(record.keys() - {"id", "status"}):
            result.error(f"{location}.{key}", "佔位層級只允許 id 和 status")
        return

    fields = ("name", "language", "source_url", "sections", "entrances", "exits")
    require_fields(record, fields, location, result)
    if "name" in record:
        name = record["name"]
        if not nonempty_string(name) or re.search(r"[\ud800-\udfff]", name):
            result.error(f"{location}.name", "名稱必須是非空且有效的 Unicode 字串")
    if "language" in record and record["language"] != "zh-TW":
        result.error(f"{location}.language", "語言必須是 zh-TW")
    if "source_url" in record and not valid_url(record["source_url"], article=True):
        result.error(f"{location}.source_url", f"來源必須是 {ARTICLE_HOST} 上的有效 HTTPS 網址")

    for key in ("sections", "entrances", "exits"):
        if key not in record:
            continue
        value = record[key]
        field_location = f"{location}.{key}"
        if not isinstance(value, list):
            result.error(field_location, "必須是陣列")
        elif key == "sections":
            validate_sections(value, directory, field_location, result)
        else:
            for target in validate_connections(value, field_location, result):
                if key == "exits":
                    yield target


def validate_sources(data_dir):
    result = Validation()
    levels_dir = data_dir / "levels"
    try:
        children = sorted(levels_dir.iterdir())
    except OSError as exc:
        result.filesystem_error("data/levels", exc)
        return result

    seen = {}
    exits = []
    for directory in children:
        directory_location = f"data/levels/{directory.name}"
        try:
            is_directory = stat.S_ISDIR(directory.stat().st_mode)
        except OSError as exc:
            result.filesystem_error(directory_location, exc)
            continue
        if not is_directory and not directory.name.startswith("level-"):
            continue
        if not is_directory or not directory.name.startswith("level-") or not supported_id(directory.name[6:]):
            result.error(directory_location, "層級必須使用 level-{數字 ID}/index.json 目錄格式")
            if not is_directory:
                continue

        result.level_count += 1
        location = f"{directory_location}/index.json"
        record = read_object(directory / "index.json", location, result)
        if record is None:
            continue

        ident = record.get("id")
        if not supported_id(ident):
            result.error(f"{location}.id", "層級 ID 必須是由 ASCII 數字組成的非空字串")
        else:
            if directory.name != f"level-{ident}":
                result.error(f"{location}.id", f"目錄名稱必須與 ID 一致，應為 level-{ident}")
            if ident in seen:
                result.error(f"{location}.id", f"層級 ID {ident} 重複，首次出現於 {seen[ident]}")
            else:
                seen[ident] = location
            if directory.name == f"level-{ident}" and record.get("status") in STATUSES:
                result.levels[ident] = record
        exits.extend(validate_level(record, directory, location, result))

    for target, location in exits:
        if target not in result.levels:
            result.error(location, f"出口目標 {target} 找不到對應的完整或佔位層級")
    return result


def expected_index(levels):
    entries = []
    for ident in sorted(levels, key=id_sort_key):
        level = levels[ident]
        entries.append({
            "id": ident,
            "name": level["name"] if level["status"] == "complete" else None,
            "status": level["status"],
            "path": f"levels/level-{ident}/index.json",
        })
    return {"schema_version": 1, "levels": entries}


def validate_index(data_dir, result):
    location = "data/index.json"
    sources_valid = not (result.errors or result.filesystem_errors)
    index = read_object(data_dir / "index.json", location, result)
    if index is None:
        return

    start_errors = len(result.errors)
    if index.keys() != {"schema_version", "levels"}:
        result.error(location, "索引只允許 schema_version 和 levels，且兩者皆為必要欄位")
    if type(index.get("schema_version")) is not int or index["schema_version"] != 1:
        result.error(f"{location}.schema_version", "索引版本必須是整數 1")
    entries = index.get("levels")
    if not isinstance(entries, list):
        result.error(f"{location}.levels", "索引層級必須是陣列")
        return

    actual = {}
    for position, entry in enumerate(entries):
        entry_location = f"{location}.levels[{position}]"
        if not isinstance(entry, dict) or entry.keys() != INDEX_FIELDS:
            result.error(entry_location, "項目必須是含 id、name、status 和 path 的物件")
            continue
        ident = entry["id"]
        if not supported_id(ident):
            result.error(f"{entry_location}.id", "索引 ID 必須是由 ASCII 數字組成的非空字串")
        elif ident in actual:
            result.error(f"{entry_location}.id", f"索引 ID {ident} 重複")
        else:
            actual[ident] = entry
        status = entry["status"]
        if status not in STATUSES:
            result.error(f"{entry_location}.status", "狀態必須是 complete 或 placeholder")
        elif status == "complete" and not nonempty_string(entry["name"]):
            result.error(f"{entry_location}.name", "完整層級名稱必須是非空字串")
        elif status == "placeholder" and entry["name"] is not None:
            result.error(f"{entry_location}.name", "佔位層級名稱必須是 null")
        if not isinstance(entry["path"], str) or entry["path"] != f"levels/level-{ident}/index.json":
            result.error(f"{entry_location}.path", "索引路徑必須是相對於 data/ 且符合該 ID 的路徑")

    if not sources_valid or len(result.errors) != start_errors:
        return

    expected = {entry["id"]: entry for entry in expected_index(result.levels)["levels"]}
    for ident, entry in expected.items():
        if ident not in actual:
            result.error(location, f"索引缺少層級 {ident}")
        elif actual[ident] != entry:
            result.error(location, f"層級 {ident} 的索引項目與來源資料不一致")
    for ident in actual:
        if ident not in expected:
            result.error(location, f"索引含有來源資料中不存在的層級 {ident}")
    if list(actual) != sorted(actual, key=id_sort_key):
        result.error(location, "索引層級必須按 ID 的數值升冪排列")


def main(argv=None):
    parser = argparse.ArgumentParser(description="驗證 Backrooms Archive 層級資料與索引。")
    parser.add_argument("--source-only", action="store_true", help="只驗證原始層級資料")
    args = parser.parse_args(argv)
    result = validate_sources(DATA_DIR)
    if not args.source_only:
        validate_index(DATA_DIR, result)
    return result.report()


def run_cli(main_function):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    raise SystemExit(main_function())


if __name__ == "__main__":
    run_cli(main)
