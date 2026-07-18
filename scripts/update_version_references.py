#!/usr/bin/env python3
"""Update every version source declared by the specification roadmap."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROADMAP_PATH = "data/governance/specification_roadmap.json"
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def load_json(path: Path):
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def set_dotted_value(value: dict, dotted_path: str, replacement: str) -> None:
    current = value
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = replacement


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_version_references(root: Path, new_version: str) -> tuple[str, str]:
    if not SEMVER.fullmatch(new_version):
        raise ValueError(f"Invalid semantic version: {new_version}")
    roadmap_path = root / ROADMAP_PATH
    roadmap = load_json(roadmap_path)
    old_version = (root / "version.txt").read_text(encoding="utf-8-sig").strip()

    for source in roadmap["version_sources"]:
        path = root / source["path"]
        kind = source["kind"]
        if kind == "plain":
            path.write_text(new_version + "\n", encoding="utf-8")
        elif kind == "json_field":
            value = load_json(path)
            set_dotted_value(value, source["field"], new_version)
            write_json(path, value)
        elif kind == "text_template":
            text = path.read_text(encoding="utf-8-sig")
            old_marker = source["template"].format(version=old_version)
            new_marker = source["template"].format(version=new_version)
            if old_marker not in text:
                raise ValueError(f"Version marker not found in {source['path']}: {old_marker}")
            path.write_text(text.replace(old_marker, new_marker), encoding="utf-8")

    roadmap["repository_baseline"] = new_version
    write_json(roadmap_path, roadmap)
    return old_version, new_version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if not SEMVER.fullmatch(args.version):
        parser.error("version must use MAJOR.MINOR.PATCH")
    old_version, new_version = update_version_references(args.root.resolve(), args.version)
    print(f"Updated repository version references from {old_version} to {new_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
