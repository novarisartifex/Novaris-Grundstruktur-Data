#!/usr/bin/env python3
"""Extract v1.4 without overwriting existing files.
Requires beautifulsoup4; use an empty output directory.
"""
import base64, hashlib, json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup

def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")[:90]

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def main():
    source=Path(sys.argv[1])
    root=Path(sys.argv[2])
    if root.exists() and any(root.iterdir()):
        raise SystemExit("Output directory must be empty; refusing to overwrite files")
    root.mkdir(parents=True,exist_ok=True)
    soup=BeautifulSoup(source.read_text(encoding="utf-8"),"html.parser")
    js=soup.script.get_text()
    start=js.index("const NOVARIS_SCENES = ")+len("const NOVARIS_SCENES = ")
    scenes,_=json.JSONDecoder().raw_decode(js[start:])
    files={}
    def put(path,data):
        if path in files and files[path]!=data:
            raise ValueError("Duplicate path: "+path)
        files[path]=data
    def image_rewrite(card):
        for img in card.select('img[src^="data:image/"]'):
            head,encoded=img["src"].split(",",1)
            ext="png" if "png" in head else "jpg" if "jpeg" in head else "webp"
            binary=base64.b64decode(encoded,validate=True)
            path="media/"+sha(binary)+"."+ext
            put(path,binary)
            img["src"]=path
    def card(section,element):
        name=element.select_one("h3").get_text(" ",strip=True)
        image_rewrite(element)
        record={"id":slug(name),"name":name,"category":element.get("data-class",""),
                "description":element.get_text(" ",strip=True),"source_html":str(element)}
        path=f"data/{section}/{slug(name)}.json"
        put(path,(json.dumps(record,ensure_ascii=False,indent=2)+"\n").encode())
    for section,selector in (("people",".person-card"),("districts",".district-card"),("world",".world-card")):
        for element in soup.select(selector): card(section,element)
    for index,scene in enumerate(scenes,1):
        ident=f"{index:04d}-{slug(scene['title'])}"
        put(f"data/scenes/{ident}.json",(json.dumps({"id":ident,**scene},ensure_ascii=False,indent=2)+"\n").encode())
    manifest={"schema_version":2,"data_version":1,"status":"published","source_file":source.name,
              "source_sha256":sha(source.read_bytes()),
              "files":[{"path":p,"sha256":sha(blob),"size_bytes":len(blob),"file_version":sha(blob)[:16]} for p,blob in sorted(files.items())],
              "counts":{name:sum(p.startswith(f"data/{name}/") for p in files) for name in ("people","districts","world","scenes")}}
    for path,blob in files.items():
        target=root/path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(blob)
    (root/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(manifest["counts"],"media",sum(p.startswith("media/") for p in files))

if __name__=="__main__":main()
