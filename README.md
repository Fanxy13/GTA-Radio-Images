# GTA-Radio-Images

Radio station logos for the GTA radio website, one image per station.
Keys are identical to the station ids of the radio API (`<game>/<station>`).

```
images/3/chat.png
images/4/liberty_rock.png
images/sa/k-dst.png
images/manifest.json   # key -> { path, source }
```

All images are PNG, exactly 512x512 px (1:1), logo scaled proportionally and centered on a transparent background.

## Use on the website

```js
const BASE = 'https://raw.githubusercontent.com/fanxy13/gta-radio-images/main/images/';
const logoUrl = (id) => `${BASE}${id}.png`;   // logoUrl('3/chat')
```

(For production traffic prefer jsDelivr: `https://cdn.jsdelivr.net/gh/fanxy13/gta-radio-images@main/images/<id>.png`)

## Notes

- All logos are transparent PNGs. SVG sources are rendered crisp, small raster sources are upscaled with smoothing and sharpening.
- `3/head` is the in-game building texture (background removed).
- `lcs/kjah` keeps its black square: it is part of the badge (leaves and stripes).
- `4/the_vibe` is a hand-made image: its source is `scripts/custom/the_vibe.png`.
- `lcs/lips` and `vcs/flash|vcpr|vrock|wave` reuse the logo of the same station from the earlier game.

## Regenerating

```bash
pip install pillow cairosvg numpy scipy opencv-python-headless
python3 scripts/fetch_logos.py
```

This downloads everything listed in `scripts/logo-map.json` from the GTA Wiki (plus local files from `scripts/custom/`), removes backgrounds where configured, and writes 512x512 PNGs and `images/manifest.json`. `source` in the manifest links each file's wiki page.

## Copyright

The logos are trademarks / copyrighted material of Rockstar Games / Take-Two. They are collected from the GTA Wiki for a non-commercial fan project and are not covered by any license of this repo.
