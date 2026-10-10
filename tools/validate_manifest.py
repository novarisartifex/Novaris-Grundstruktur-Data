#!/usr/bin/env python3
"""Validate all files listed in the published Novaris manifest."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
manifest_path = root / "manifest.json"
if not manifest_path.is_file():
    raise SystemExit("manifest.json missing: no published dataset yet")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
assert manifest.get("schema_version") in (1, 2), "Unsupported schema"
assert manifest.get("status") == "published", "Manifest is not published"
entries = manifest.get("files")
assert isinstance(entries, list) and entries, "No manifest file entries"
seen = set()
for item in entries:
    path = item["path"]
    rel = Path(path)
    assert not rel.is_absolute() and ".." not in rel.parts, f"Unsafe path: {path}"
    assert path not in seen, f"Duplicate path: {path}"
    seen.add(path)
    binary = (root / rel).read_bytes()
    assert len(binary) == item["size_bytes"], f"Size mismatch: {path}"
    assert hashlib.sha256(binary).hexdigest() == item["sha256"], f"SHA-256 mismatch: {path}"
    if path.endswith(".json"):
        json.loads(binary)
print(f"Validated {len(entries)} files against manifest")
