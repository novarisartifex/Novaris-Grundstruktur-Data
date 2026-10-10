#!/usr/bin/env python3
"""Safe import of Novaris data export ZIP from a GitHub Release asset."""
import hashlib
import json
import pathlib
import sys
import zipfile

root = pathlib.Path(__file__).resolve().parent.parent
archive = pathlib.Path(sys.argv[1])
with zipfile.ZipFile(archive) as z:
    names = {name for name in z.namelist() if not name.endswith("/")}
    assert "manifest.json" in names, "Missing manifest"
    manifest = json.loads(z.read("manifest.json"))
    assert manifest.get("status") == "published", "Not published"
    files = manifest["files"]
    expected = {item["path"] for item in files}
    assert len(expected) == len(files), "Duplicate paths"
    assert names == expected | {"manifest.json"}, f"Unexpected or missing ZIP members: {names ^ (expected | {'manifest.json'})}"
    prepared = {}
    for item in files:
        name = item["path"]
        path = pathlib.PurePosixPath(name)
        assert path.parts[0] in ("data", "media") and ".." not in path.parts and not path.is_absolute(), name
        blob = z.read(name)
        assert len(blob) == item["size_bytes"], name
        assert hashlib.sha256(blob).hexdigest() == item["sha256"], name
        if name.endswith(".json"):
            json.loads(blob)
        target = root.joinpath(*path.parts)
        if target.exists():
            assert target.read_bytes() == blob, f"Existing file differs: {name}"
        prepared[target] = blob
    manifest_bytes = z.read("manifest.json")
    target_manifest = root / "manifest.json"
    if target_manifest.exists():
        assert target_manifest.read_bytes() == manifest_bytes, "Existing manifest differs; refusing overwrite"
    for path, blob in prepared.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(blob)
    if not target_manifest.exists():
        target_manifest.write_bytes(manifest_bytes)
    print(f"Imported {len(files)} verified files; no existing files overwritten")
