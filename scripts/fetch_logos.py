#!/usr/bin/env python3
"""Download station logos listed in logo-map.json from the GTA Wiki (Fandom),
convert every one to a 512x512 PNG (logo scaled to fit, transparent padding)
and write images/<key>.png plus images/manifest.json.

Usage: pip install pillow cairosvg && python3 scripts/fetch_logos.py
"""
import io, json, os, sys, time, urllib.parse, urllib.request

import cairosvg
from PIL import Image

SIZE = 512      # output is SIZE x SIZE
PAD = 16        # transparent margin around the logo

API = "https://gta.fandom.com/api.php"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = {"User-Agent": "gta-radio-images-fetch/1.0"}


def http(url):
    for i in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception as e:
            if i == 3:
                raise
            time.sleep(1 + i)


def to_square_png(data, is_svg):
    if is_svg:
        data = cairosvg.svg2png(bytestring=data, output_width=SIZE * 2)
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    bbox = img.getchannel("A").getbbox()      # trim transparent borders
    if bbox:
        img = img.crop(bbox)
    box = SIZE - 2 * PAD
    scale = min(box / img.width, box / img.height)
    img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2), img)
    return canvas


def image_urls(titles):
    out = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        q = urllib.parse.urlencode({
            "action": "query", "prop": "imageinfo", "iiprop": "url",
            "titles": "|".join("File:" + t for t in chunk), "format": "json",
            "redirects": 1})
        d = json.loads(http(API + "?" + q))
        pages = d["query"]["pages"].values()
        redirects = {r["to"]: r["from"] for r in d["query"].get("redirects", [])}
        norm = {n["to"]: n["from"] for n in d["query"].get("normalized", [])}
        for p in pages:
            title = p["title"]
            src = redirects.get(title, title)
            src = norm.get(src, src)
            if "imageinfo" in p:
                out[src[len("File:"):]] = p["imageinfo"][0]["url"]
    return out


def main():
    mapping = json.load(open(os.path.join(HERE, "logo-map.json")))
    urls = image_urls(sorted(set(mapping.values())))
    manifest, missing = {}, []
    for key, fname in mapping.items():
        url = urls.get(fname) or urls.get(fname.replace("_", " "))
        if not url:
            missing.append(key)
            continue
        rel = f"images/{key}.png"
        dest = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if not os.path.exists(dest):
            is_svg = fname.lower().endswith(".svg")
            to_square_png(http(url), is_svg).save(dest, optimize=True)
        manifest[key] = {
            "path": rel,
            "source": "https://gta.fandom.com/wiki/File:" + urllib.parse.quote(fname.replace(" ", "_")),
        }
    json.dump(manifest, open(os.path.join(ROOT, "images", "manifest.json"), "w"), indent=2, sort_keys=True)
    print(f"ok: {len(manifest)}  missing: {missing}")


if __name__ == "__main__":
    sys.exit(main())
