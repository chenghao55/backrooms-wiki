"""Build the archive index after validating all source records."""

import argparse
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from validate import DATA_DIR, expected_index, run_cli, validate_sources


def write_index(path, index):
    content = (json.dumps(index, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    try:
        if path.read_bytes() == content:
            return False
    except FileNotFoundError:
        pass

    temporary_path = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=".index-", suffix=".tmp", delete=False) as temp:
            temporary_path = Path(temp.name)
            temp.write(content)
        temporary_path.replace(path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="驗證層級資料並重建 Backrooms Archive 索引。")
    parser.parse_args(argv)
    result = validate_sources(DATA_DIR)
    if result.errors or result.filesystem_errors:
        return result.report()

    try:
        changed = write_index(DATA_DIR / "index.json", expected_index(result.levels))
    except OSError as exc:
        result.filesystem_error("data/index.json", exc)
        return result.report()

    exit_code = result.report()
    print("已產生 data/index.json。" if changed else "data/index.json 內容相同，無須重寫。")
    return exit_code


if __name__ == "__main__":
    run_cli(main)
