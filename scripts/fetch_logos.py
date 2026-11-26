#!/usr/bin/env python3
"""Build images/<key>.png (512x512, transparent) for every station in logo-map.json.

Sources are downloaded from the GTA Wiki (Fandom) or read from scripts/custom/.
Every logo is: background removed (if configured) -> trimmed -> scaled to fit
512x512 (SVGs are rendered crisp, small rasters are upscaled with smoothing +
sharpening) -> centered on a transparent canvas.

logo-map.json values:
  "File.png"                                  wiki file
  {"file": "File.png", "bg": "black"}         wiki file + remove background
  {"custom": "scripts/custom/x.png", ...}     local source file
  bg: "black" | "head"  (flood-fill from the border, see remove_bg), tol: black threshold (default 40)

Usage: pip install pillow cairosvg numpy scipy opencv-python-headless
       python3 scripts/fetch_logos.py [--cache DIR]
"""
import io, json, os, sys, time, urllib.parse, urllib.request

import cairosvg
import cv2
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

SIZE = 512      # output is SIZE x SIZE
PAD = 16        # transparent margin around the logo
SS = 2          # supersampling factor for upscaling
API = "https://gta.fandom.com/api.php"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = {"User-Agent": "gta-radio-images-fetch/1.0"}


def http(url):
    for i in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception:
            if i == 3:
                raise
            time.sleep(1 + i)


def image_urls(titles):
    out = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        q = urllib.parse.urlencode({
            "action": "query", "prop": "imageinfo", "iiprop": "url",
            "titles": "|".join("File:" + t for t in chunk), "format": "json", "redirects": 1})
        d = json.loads(http(API + "?" + q))
        redirects = {r["to"]: r["from"] for r in d["query"].get("redirects", [])}
        norm = {n["to"]: n["from"] for n in d["query"].get("normalized", [])}
        for p in d["query"]["pages"].values():
            src = redirects.get(p["title"], p["title"])
            src = norm.get(src, src)
            if "imageinfo" in p:
                out[src[len("File:"):]] = p["imageinfo"][0]["url"]
    return out


# ---------------------------------------------------------------- background
def _flood_mask(cand):
    """Pixels of `cand` that are connected to the image border."""
    lab, _ = ndi.label(cand)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    return np.isin(lab, list(border))


def remove_bg(img, mode, tol=40):
    a = np.array(img.convert("RGB")).astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    if mode == "black":
        cand = a.max(axis=2) <= tol
    elif mode == "head":     # bluish background + light glow around dark teal letters
        cand = (b > g + 8) | (a.min(axis=2) > 170)
    else:
        raise ValueError(mode)
    bg = _flood_mask(cand)
    alpha = Image.fromarray(((~bg) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    alpha = np.array(alpha)
    alpha[bg & (alpha < 255)] = np.minimum(alpha[bg & (alpha < 255)], 128)
    out = np.dstack([a.astype(np.uint8), alpha])
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------------- scaling
def _trim(img):
    bbox = img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return img.crop(bbox) if bbox else img


def _upscale(img, scale):
    """Smooth upscale of a small raster logo: Lanczos, bilateral smoothing,
    unsharp mask and a crisper alpha edge, computed at SS x the target size."""
    arr = np.array(img)
    a = arr[..., 3]
    opaque = a >= 128
    rgb = arr[..., :3]
    if opaque.sum() > 16 and (~opaque).any():  # colors of (semi-)transparent px are unreliable: take the nearest solid color
        idx = ndi.distance_transform_edt(~opaque, return_distances=False, return_indices=True)
        rgb = rgb[idx[0], idx[1]]
    s = scale * SS
    size = (max(1, round(img.width * s)), max(1, round(img.height * s)))
    rgb_big = np.array(Image.fromarray(rgb).resize(size, Image.LANCZOS))
    a_big = np.array(Image.fromarray(a).resize(size, Image.BICUBIC)).astype(np.float32) / 255

    sig = max(1.0, s * 0.9)
    rgb_big = cv2.bilateralFilter(rgb_big, d=0, sigmaColor=28, sigmaSpace=sig)
    blur = cv2.GaussianBlur(rgb_big, (0, 0), sig * 0.7)
    rgb_big = np.clip(rgb_big.astype(np.float32) * 1.6 - blur.astype(np.float32) * 0.6, 0, 255).astype(np.uint8)

    a_big = cv2.GaussianBlur(a_big, (0, 0), max(0.6, s * 0.25))
    a_big = np.clip((a_big - 0.5) * 1.8 + 0.5, 0, 1)
    out = np.dstack([rgb_big, (a_big * 255).astype(np.uint8)])
    return Image.fromarray(out, "RGBA")


def to_square_png(data, is_svg, bg=None, tol=40):
    box = SIZE - 2 * PAD
    if is_svg:      # render large, the final downscale keeps it crisp
        img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=data, output_width=SIZE * 3))).convert("RGBA")
        img = _trim(img)
    else:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        if bg:
            img = remove_bg(img, bg, tol)
        img = _trim(img)
        scale = min(box / img.width, box / img.height)
        if scale > 1:                       # small source: smooth upscale (result is SS x target)
            img = _upscale(img, scale)
    fit = min(box / img.width, box / img.height)
    img = img.resize((max(1, round(img.width * fit)), max(1, round(img.height * fit))), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2), img)
    return canvas


def main():
    cache = None
    if "--cache" in sys.argv:
        cache = sys.argv[sys.argv.index("--cache") + 1]
        os.makedirs(cache, exist_ok=True)
    mapping = json.load(open(os.path.join(HERE, "logo-map.json")))
    norm = {k: (v if isinstance(v, dict) else {"file": v}) for k, v in mapping.items()}
    urls = image_urls(sorted({v["file"] for v in norm.values() if "file" in v}))
    manifest, missing = {}, []
    for key, cfg in norm.items():
        if "custom" in cfg:
            data = open(os.path.join(ROOT, cfg["custom"]), "rb").read()
            fname, source = cfg["custom"], "custom"
        else:
            fname = cfg["file"]
            url = urls.get(fname) or urls.get(fname.replace("_", " "))
            if not url:
                missing.append(key)
                continue
            cp = os.path.join(cache, key.replace("/", "__") + "_" + fname.replace(" ", "_")) if cache else None
            if cp and os.path.exists(cp):
                data = open(cp, "rb").read()
            else:
                data = http(url)
                if cp:
                    open(cp, "wb").write(data)
            source = "https://gta.fandom.com/wiki/File:" + urllib.parse.quote(fname.replace(" ", "_"))
        rel = f"images/{key}.png"
        dest = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        to_square_png(data, fname.lower().endswith(".svg"), cfg.get("bg"), cfg.get("tol", 40)).save(dest, optimize=True)
        manifest[key] = {"path": rel, "source": source}
    json.dump(manifest, open(os.path.join(ROOT, "images", "manifest.json"), "w"), indent=2, sort_keys=True)
    print(f"ok: {len(manifest)}  missing: {missing}")


if __name__ == "__main__":
    sys.exit(main())
