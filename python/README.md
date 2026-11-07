# StepSheet — Python edition

An offline desktop runner for **StepSheet**, the work-instruction editor and PDF
exporter for the `.soe` format. It does two things:

1. **Editor** — launches the full StepSheet app in your browser, running entirely
   on this computer (no internet, nothing uploaded). Opening/saving `.soe` files,
   the Spanish view, the Copilot/VWI *Reformat & bundle* + *Review & replace*
   workflow, and PDF creation all work exactly like the web version.
2. **Convert** — a headless command that renders a `.soe` straight to PDF with
   reportlab, no browser needed. Handy for batch jobs or a server.

## Requirements

- **Python 3.9+** (3.11+ recommended).
- The **editor** needs nothing beyond the Python standard library.
- The **convert** command needs two packages:

  ```
  pip install -r requirements.txt
  ```

## Run the editor

From the folder that contains the `stepsheet/` folder:

```
python -m stepsheet                 # open the editor
python -m stepsheet path/to/file.soe   # open it and load that file
```

Windows users can double-click **run-stepsheet.bat**; macOS/Linux users can run
**./run-stepsheet.sh**. Leave the small console window open while you work; close
it (or press Ctrl+C) to stop the local server.

> The editor serves on `http://127.0.0.1:<port>` and opens your default browser.
> It is bound to localhost, so it is not reachable from other machines.

## Convert to PDF (no browser)

```
python -m stepsheet convert IN.soe                  # -> IN.pdf  (picture pages)
python -m stepsheet convert IN.soe OUT.pdf
python -m stepsheet convert IN.soe OUT.pdf --soe     # SOE summary table instead
python -m stepsheet convert IN.soe --lang es         # use the file's Spanish text
python -m stepsheet convert IN.soe --quality High    # Low | Medium | High
python -m stepsheet convert IN.soe --no-date
```

## Notes

- `.soe` files are read and written byte-for-byte compatible with the original
  program. The custom **Quality** step type is stored as `Safety` plus a
  `<customtype>Quality</customtype>` tag the old program ignores, so files stay
  openable both ways.
- The editor is the single source of truth; this package simply runs it offline
  and adds the headless PDF path. See the project README for the feature list.
