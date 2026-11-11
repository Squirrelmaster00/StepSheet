"""Command line entry point.

    python -m stepsheet                 open the editor in your browser
    python -m stepsheet file.soe        open the editor and load file.soe
    python -m stepsheet serve [file]    same as above (explicit)
    python -m stepsheet convert IN.soe [OUT.pdf] [options]

convert options:
    --soe              lay out the SOE summary table instead of the picture pages
    --lang es          use the Spanish captions/headers stored in the file
    --quality LEVEL    image quality: Low | Medium | High  (default Medium)
    --no-date          leave the date off the footer
"""
from __future__ import annotations

import os
import sys



def pdf_file_name(doc, src, soe=False, lang="en"):
    """Same naming as the app: the number from header row 2, box 2, then the title,
    e.g. "000123 RAIL INSTALL.pdf"; Spanish uses the Spanish title + "(Español)"."""
    import re
    def clean(x):
        x = re.sub(r"[\\/]+", "-", x or "")
        return re.sub(r"\s+", " ", re.sub(r'[:*?"<>|\x00-\x1f]+', "", x)).strip()
    h = doc.header or {}
    raw = (h.get("udc4") or "").strip()
    runs = sorted(re.findall(r"\d+", raw), key=len, reverse=True)
    num = runs[0] if runs else ""   # only the number from row 2, box 2
    title = clean(((doc.header_es or {}).get("udc1") or h.get("udc1")) if lang == "es" else h.get("udc1"))
    base = " ".join(x for x in (num, title) if x) or os.path.splitext(os.path.basename(src))[0]
    base = base[:150].strip()
    return base + (" Analysis.pdf" if soe else " (Español).pdf" if lang == "es" else ".pdf")

def _convert(args: list[str]) -> int:
    from . import pdf_export
    from .soe import Document

    pos, soe, lang, quality, add_date = [], False, "en", "Medium", True
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--soe":
            soe = True
        elif a == "--no-date":
            add_date = False
        elif a == "--lang":
            i += 1; lang = args[i] if i < len(args) else "en"
        elif a == "--quality":
            i += 1; quality = args[i] if i < len(args) else "Medium"
        elif a.startswith("--"):
            print(f"Unknown option: {a}"); return 2
        else:
            pos.append(a)
        i += 1

    if not pos:
        print("Usage: python -m stepsheet convert IN.soe [OUT.pdf] [--soe] [--lang es]")
        return 2
    src = pos[0]
    if not os.path.isfile(src):
        print(f"File not found: {src}"); return 1
    doc = Document.load(src)
    out = pos[1] if len(pos) > 1 else os.path.join(os.path.dirname(src) or ".", pdf_file_name(doc, src, soe, lang))
    name = os.path.basename(out)
    if soe:
        pdf_export.build_soe_pdf(doc, out, pdf_name=name)
    else:
        pdf_export.build_instructions_pdf(doc, out, quality=quality, pdf_name=name,
                                          add_date=add_date, lang=lang)
    print(f"Wrote {out}  ({len(doc.tasks)} steps)")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    from . import server

    if argv and argv[0] == "convert":
        return _convert(argv[1:])
    if argv and argv[0] == "serve":
        rest = argv[1:]
        server.serve(rest[0] if rest else "")
        return 0
    # default: serve, with an optional file to auto-load
    server.serve(argv[0] if argv else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
