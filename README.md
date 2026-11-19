# GTA-Radio-Images

Radio station logos for the GTA radio website, one image per station.
Keys are identical to the station ids of the radio API (`<game>/<station>`).

```
images/3/chat.svg
images/4/liberty_rock.png
images/sa/k-dst.jpg
images/manifest.json   # key -> { path, source }
```

The file extension differs per station (svg/png/jpg/gif), so look the path up in the manifest.

## Use on the website

```js
const BASE = 'https://raw.githubusercontent.com/fanxy13/gta-radio-images/main/';
const manifest = await (await fetch(BASE + 'images/manifest.json')).json();
const logoUrl = (id) => BASE + manifest[id].path;   // logoUrl('3/chat')
```

(For production traffic prefer jsDelivr: `https://cdn.jsdelivr.net/gh/fanxy13/gta-radio-images@main/images/...`)

## Notes

- `3/game` is the GameSpy sponsor logo (Game Radio FM has no own logo), `3/head` is the in-game building texture, `4/the_vibe` is the in-game ad.
- `lcs/lips` and `vcs/flash|vcpr|vrock|wave` reuse the logo of the same station from the earlier game.

## Regenerating

`python3 scripts/fetch_logos.py` re-downloads everything listed in `scripts/logo-map.json` from the GTA Wiki; `source` in the manifest links each file's wiki page.

## Copyright

The logos are trademarks / copyrighted material of Rockstar Games / Take-Two. They are collected from the GTA Wiki for a non-commercial fan project and are not covered by any license of this repo.
