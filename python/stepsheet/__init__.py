"""StepSheet - offline work-instruction editor and PDF exporter for the .soe format.

Two ways to use it:

    python -m stepsheet [file.soe]     open the full editor in your browser (offline)
    python -m stepsheet convert IN.soe OUT.pdf [--soe] [--lang es]   headless PDF export

The editor is the same self-contained StepSheet web app; it runs entirely on this
computer with no internet. The convert command renders PDFs with reportlab and needs
no browser.
"""

__version__ = "2.0.0"
