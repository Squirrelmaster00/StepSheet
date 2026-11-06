# StepSheet

A single-file, offline web app for writing picture-based **work instructions** and
exporting them as print-ready PDFs — in English and Mexican Spanish.

StepSheet reads and writes the `.soe` work-instruction file format, so documents
move back and forth with existing `.soe` tooling. It runs entirely in the browser:
your files and photos never leave your device, and no server, account, or build
step is involved.

> **Independent implementation.** StepSheet is an original, interoperable reader/writer
> for the `.soe` format. It contains **no** code or assets from any other application
> and is **not affiliated with, endorsed by, or derived from** any commercial
> work-instruction product. File formats themselves are not copyrightable; this is a
> clean implementation built from the format's structure.

---

## Features

- **Step editor** — per step: photo, quality type (Work Content, Check, Verify, Safety,
  and a custom **Quality** octagon), page layout, task text, and font size.
- **PDF export** — "visual instructions" pages (1/2/4/6/9 pictures per page) and an
  analysis (SOE) sheet, rendered by a small built-in PDF writer. No libraries.
- **Spanish PDFs** — translate steps (via copy/paste with an AI assistant), keep
  domain terms in English through an editable glossary, and export a separate,
  clearly-marked Spanish PDF.
- **Auto-recovery** — in-progress work is saved to the browser (IndexedDB) and restored
  after a reload or crash.
- **Offline** — open the single HTML file and it works with no network connection.
- **Responsive** — desktop, tablet, and phone layouts.

## Run it locally

No build step. Either:

- **Open the file:** double-click `StepSheet.html` (or open it in any modern browser).
- **Serve it** (optional, if your browser restricts `file://` features):
  ```bash
  # any static server works; e.g. Python
  python3 -m http.server 8000
  # then visit http://localhost:8000/StepSheet.html
  ```

Tested in current Chrome and Edge; Firefox and Safari work with minor file-dialog
differences.

### Browser extension (optional)

The `extension/` folder is a toolbar button that opens the editor in a tab. Load it
via `chrome://extensions` → **Developer mode** → **Load unpacked**. It is the same app
as `StepSheet.html`; the HTML file alone is fully functional without it.

## Project structure

```
StepSheet.html        The whole app: HTML + inline CSS + inline JS.
extension/            Optional Chrome/Edge wrapper (manifest, background, editor).
LICENSE               MIT.
```

**Why one file?** StepSheet is intentionally a single, dependency-free HTML file so it
runs from a `file://` path with no server, no bundler, and no CDN. That constraint —
not a lack of modularity — is why the CSS and JS are inlined.

## AI assistance

Portions of this project were generated with the help of an AI coding assistant and
then reviewed, edited, and tested by the author. See
[`AI-USAGE.md`](AI-USAGE.md) for details. Under current U.S. guidance, purely
AI-generated material may not be independently copyrightable; the human authorship lies
in the selection, editing, arrangement, and testing of the result.

## Data & privacy

StepSheet processes everything **locally in your browser**. It makes no network
requests, sends no telemetry, and stores nothing on any server. Auto-recovery data
lives only in your own browser and can be cleared from the app or your browser settings.

**Do not commit real work files.** `.soe` documents and photos are excluded by
`.gitignore` on purpose — they may contain proprietary or confidential content. Use a
synthetic sample for demos.

## License

[MIT](LICENSE) © 2026 StepSheet contributors. Any brand or product names a user adds to the
terminology glossary belong to their respective owners and are
used for identification only.
