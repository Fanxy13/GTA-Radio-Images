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

- `3/game` is the GameSpy sponsor logo (Game Radio FM has no own logo), `3/head` is the in-game building texture, `4/the_vibe` is the in-game ad.
- `lcs/lips` and `vcs/flash|vcpr|vrock|wave` reuse the logo of the same station from the earlier game.

## Regenerating

`pip install pillow cairosvg && python3 scripts/fetch_logos.py` re-downloads everything listed in `scripts/logo-map.json` from the GTA Wiki and converts it to 512x512 PNG; `source` in the manifest links each file's wiki page.

## Copyright

The logos are trademarks / copyrighted material of Rockstar Games / Take-Two. They are collected from the GTA Wiki for a non-commercial fan project and are not covered by any license of this repo.
