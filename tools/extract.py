#!/usr/bin/env python3
"""Extract original Novaris HTML content into versioned, sharded JSON and media.
Usage: python3 tools/extract.py INPUT.html [OUTPUT_DIR]
Requires: beautifulsoup4. Never deletes existing output files.
"""
import base64
import hashlib
import json
import mimetypes
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return value[:90] or "entry"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise RuntimeError(f"Existing file differs; refusing overwrite: {path}")
    if not path.exists():
        path.write_bytes(data)

def main():
    source = Path(sys.argv[1])
    root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    soup = BeautifulSoup(source.read_text(encoding="utf-8"), "html.parser")
    assets = {}
    def extract_images(node):
        for img in node.select("img[src^='data:image/']"):
            raw = img["src"]
            head, encoded = raw.split(",", 1)
            ext = "png" if "png" in head else "jpeg" if "jpeg" in head else "webp" if "webp" in head else None
            if not ext:
                raise ValueError(f"Unknown image type: {head}")
            binary = base64.b64decode(encoded, validate=True)
            key = digest(binary)
            path = f"media/{key}.{ext}"
            assets[path] = binary
            img["src"] = path
    script = soup.script.string or soup.script.get_text()
    marker = "const NOVARIS_SCENES = "
    start = script.index(marker) + len(marker)
    decoder = json.JSONDecoder()
    scenes, _ = decoder.raw_decode(script[start:])
    counts = {}
    records = []
    def add(section, key, data):
        base = slug(key)
        index = counts.get((section, base), 0)
        counts[(section, base)] = index + 1
        ident = base if index == 0 else f"{base}-{index+1}"
        data["id"] = ident
        data["section"] = section
        path = f"data/{section}/{ident}.json"
        records.append((path, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"))
    for card in soup.select("#people .person-card"):
        name = card.select_one(".person-name, h3, h2")
        extract_images(card)
        title = name.get_text(" ", strip=True) if name else card.get("data-search","").split(" ")[0]
        add("people", title, {"name":title,"classification":card.get("data-class",""),"source_html":str(card)})
    for card in soup.select("#districts .district-card"):
        title = card.select_one("h3").get_text(" ",strip=True)
        add("districts", title, {"name":title,"source_html":str(card)})
    for card in soup.select("#world .world-card"):
        title = card.select_one("h3").get_text(" ",strip=True)
        add("world", title, {"name":title,"source_html":str(card)})
    for index, scene in enumerate(scenes):
        add("scenes", scene.get("title",f"scene-{index+1}"), dict(scene))
    for path, binary in assets.items():
        write(root / path, binary)
    for path, binary in records:
        write(root / path, binary)
    files = []
    for path, binary in sorted([*records, *assets.items()]):
        files.append({"path":path,"sha256":digest(binary),"size_bytes":len(binary),"file_version":digest(binary)[:16]})
    manifest = {"schema_version":1,"data_version":1,"source_file":source.name,
                "source_sha256":digest(source.read_bytes()),"status":"published",
                "files":files,"counts":{section:sum(path.startswith(f"data/{section}/") for path,_ in records) for section in ("people","districts","scenes","world")}}
    manifest_bytes = (json.dumps(manifest,ensure_ascii=False,indent=2)+"\n").encode()
    write(root/"manifest.json",manifest_bytes)
    print(json.dumps(manifest["counts"],ensure_ascii=False))
    print(f"{len(assets)} images; {len(files)} files; manifest generated")

if __name__ == "__main__":
    main()
