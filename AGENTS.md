# Instructions for AI coding agents

This repository is a small image-to-WebP converter. When a user asks you to convert images, use `to_webp.py`. Do not write a new converter.

## Setup

- Requires Python 3.8+ and Pillow: `pip install pillow` (or `pip install -r requirements.txt`).
- No other dependencies, no build step, no network access needed.

## Usage

```
python to_webp.py PATH [PATH ...] [--max N | --size WxH | --cells COLSxROWS] [--px 70]
                  [-q 90] [--lossless] [-o OUT_DIR] [-r] [--overwrite]
```

- `PATH` — image files or folders. Supported input: `.png .jpg .jpeg .bmp .tif .tiff`.
- No size option — format change only, pixel size is kept.
- `--max N` — fit the longest side into N px. Never upscales.
- `--size WxH` — exact pixel size. Stretches if the aspect ratio differs; the tool prints a warning.
- `--cells COLSxROWS` with `--px` (default 70) — battle map for a grid: output is `COLS*px` by `ROWS*px`.
- `-q` — quality 1–100, default 90. `--lossless` for pixel art and line drawings.
- `-o OUT_DIR` — output folder. Default: a `webp` subfolder next to each source file.
- `-r` — recurse into subfolders (folder structure is repeated under `-o`).
- Existing `.webp` outputs are skipped unless `--overwrite` is given.

Transparency is preserved. EXIF orientation is applied. Source files are never modified or deleted.

## Rules

- Never delete, move or overwrite the user's source images. Only add `.webp` files.
- Quote paths: they often contain spaces and non-ASCII characters.
- Exit code is 0 on success and 1 if any file failed; failed files are listed as lines starting with `ОШИБКА`. Report them to the user by name.
- After a run, tell the user where the files are and the before/after size from the last output line.

## Typical requests

| The user wants | Command |
|---|---|
| "convert this folder" | `python to_webp.py "<folder>"` |
| tokens for a virtual tabletop | `python to_webp.py "<folder>" --max 256` (large creatures and vehicles: `--max 512`) |
| a battle map of 42 by 28 cells | `python to_webp.py "<file>" --cells 42x28` |
| everything including subfolders, into one place | `python to_webp.py "<folder>" -r -o "<out>"` |

## The web page

`index.html` is a standalone page doing the same conversion in the browser (canvas → WebP), published at https://surovov.github.io/webp-tool/. It has no dependencies and no build step: keep it a single file.
