# StepSheet

Offline work-instruction editor and PDF exporter for the `.soe` file format.
Create and edit visual work instructions, keep photos as the primary content,
export print-ready PDFs, translate captions, and reformat steps with help from
Microsoft 365 Copilot — all running locally in the browser, nothing uploaded.

## Ways to run it

| You want… | Use |
|---|---|
| Nothing to install, one file | Open **`StepSheet.html`** in Chrome or Edge |
| Install to phone / desktop home screen, works offline | The **PWA** at the GitHub Pages URL (`index.html`) |
| A local launcher + headless PDF export | The **`python/`** edition (`python -m stepsheet`) |
| In-browser side panel while you work | The **`extension/`** (Chrome/Edge, load unpacked) |

All four are generated from the **same source**, so they always have the same
features (see *Building* below) — they can't drift apart.

## Repository layout

```
StepSheet.html            single-file offline app (open directly)
index.html                PWA entry (GitHub Pages serves the repo root)
sw.js  manifest.webmanifest  icon-180/192/512.png   PWA support files
extension/                Chrome/Edge extension (load unpacked)
  app.js  editor.html  manifest.json  background.js  INSTALL.txt  icons/
python/                   Python edition
  stepsheet/              the package (launcher + reportlab PDF CLI)
  run-stepsheet.bat  run-stepsheet.sh  requirements.txt  README.md
src/                      source of truth
  src.html                the whole app (edit this)
  build.py                regenerates every output above
  widths.json  header-block.html
LICENSE  README.md  NOTICE.md  AI-USAGE.md  CONTRIBUTING.md
```

## Building

Edit **`src/src.html`**, then regenerate every output:

```
python3 src/build.py
```

That rewrites `StepSheet.html`, the PWA files, the extension, and the Python
edition's bundled copy, and bumps the extension version. Bump `CACHE` in
`src/build.py` when you change the app so installed PWAs refresh.

## The .soe format

ISO-8859-1 XML with the work-instruction data in `<mainroot>` and base64 JPEG
photos in `<imageroot>`. The custom **Quality** step type is stored as `Safety`
plus a `<customtype>Quality</customtype>` tag the original program ignores, so
files stay openable both ways.

## License

MIT — see `LICENSE`. Independent implementation of the `.soe` format; not
affiliated with or derived from any other application. See `NOTICE.md` and
`AI-USAGE.md`.
