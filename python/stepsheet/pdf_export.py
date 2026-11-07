"""PDF output: visual work instructions and the SOE analysis sheet."""
from __future__ import annotations

import io
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, portrait
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .soe import Document, WASTES

DEFAULT_COLORS = {
    "Check": "#FF0000",
    "Work Content": "#FFFF00",
    "Verify": "#0000FF",
    "Safety": "#FF6347",
    "Quality": "#00A651",
    "Border": "#000000",
}

TYPE_ES = {"Work Content": "Trabajo", "Check": "Revisar", "Verify": "Verificar",
           "Safety": "Seguridad", "Quality": "Calidad"}

# layout name -> (columns, rows, orientation)
LAYOUTS = {
    "1 Picture Landscape": (1, 1, "L"),
    "2 Picture Portrait": (1, 2, "P"),
    "4 Picture Landscape": (2, 2, "L"),
    "4 Picture Portrait": (2, 2, "P"),
    "6 Picture Landscape": (3, 2, "L"),
    "6 Picture Portrait": (2, 3, "P"),
    "9 Picture Portrait": (3, 3, "P"),
}
QUALITY_PX = {"Low": 800, "Medium": 1400, "High": 2400}

FONT_MAP = {
    "helvetica": ("Helvetica", "Helvetica-Bold"),
    "times": ("Times-Roman", "Times-Bold"),
    "courier": ("Courier", "Courier-Bold"),
}

MARGIN = 28


def _fonts(doc):
    return FONT_MAP.get((doc.font or "helvetica").lower(), FONT_MAP["helvetica"])


class _ImageCache:
    def __init__(self, doc: Document, max_px: int):
        self.doc, self.max_px, self.cache = doc, max_px, {}

    def get(self, iid):
        if not iid or iid not in self.doc.images:
            return None
        if iid not in self.cache:
            try:
                im = Image.open(io.BytesIO(self.doc.images[iid]))
                im.load()
                if im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")
                if max(im.size) > self.max_px:
                    im.thumbnail((self.max_px, self.max_px))
                buf = io.BytesIO()
                im.save(buf, "JPEG", quality=85)
                buf.seek(0)
                self.cache[iid] = (ImageReader(buf), im.size)
            except Exception:
                self.cache[iid] = None
        return self.cache[iid]


def _hex(c):
    return colors.HexColor(c)


def _shape(c, kind, x, y, r, color, number=None, bold="Helvetica-Bold", fs=10):
    """Step marker as in the original: outlined shape with the step number inside.
    Check = triangle, Work Content = square, Verify = circle, Safety = diamond."""
    c.saveState()
    c.setStrokeColor(color)
    c.setFillColor(colors.white)
    c.setLineWidth(max(1.8, r * 0.26))
    ty = y
    if kind == "Check":
        p = c.beginPath(); p.moveTo(x, y + r); p.lineTo(x + r * 1.08, y - r * .78); p.lineTo(x - r * 1.08, y - r * .78); p.close()
        c.drawPath(p, fill=1, stroke=1)
        ty = y - r * .3
    elif kind == "Verify":
        c.circle(x, y, r, fill=1, stroke=1)
    elif kind == "Safety":
        p = c.beginPath(); p.moveTo(x, y + r * 1.1); p.lineTo(x + r * 1.1, y); p.lineTo(x, y - r * 1.1); p.lineTo(x - r * 1.1, y); p.close()
        c.drawPath(p, fill=1, stroke=1)
    elif kind == "Quality":
        import math
        R = r * 1.1
        p = c.beginPath()
        for kk in range(8):
            a = math.pi / 8 + kk * math.pi / 4
            px, py = x + R * math.cos(a), y + R * math.sin(a)
            (p.moveTo if kk == 0 else p.lineTo)(px, py)
        p.close(); c.drawPath(p, fill=1, stroke=1)
    else:
        c.rect(x - r * .9, y - r * .9, r * 1.8, r * 1.8, fill=1, stroke=1)
    if number is not None:
        if kind == "Check" and len(str(number)) > 1:
            fs *= 0.78 if len(str(number)) == 2 else 0.62
        if kind == "Quality" and len(str(number)) > 2:
            fs *= 0.8
        c.setFillColor(colors.black)
        c.setFont(bold, fs)
        c.drawCentredString(x, ty - fs * 0.35, str(number))
    c.restoreState()


def _fit(text, font, size, width, c):
    while size > 5 and c.stringWidth(text, font, size) > width:
        size -= 0.5
    return size


def _cell_text(c, txt, x, y, w, h, font, size, align="left", min_size=5):
    """Draw text inside a box, wrapping to as many lines as fit and shrinking if needed."""
    from reportlab.lib.utils import simpleSplit
    txt = (txt or "").strip()
    if not txt:
        return
    while True:
        lines = simpleSplit(txt, font, size, w - 6)
        if len(lines) * size * 1.1 <= h - 2 or size <= min_size:
            break
        size -= 0.5
    total = len(lines) * size * 1.1
    yy = y + h / 2 + total / 2 - size
    c.setFont(font, size)
    for ln in lines:
        if align == "center":
            c.drawCentredString(x + w / 2, yy, ln)
        else:
            c.drawString(x + 4, yy, ln)
        yy -= size * 1.1


def _header(c, doc, W, H, fonts, imgs, palette, lang="en"):
    """Logo + title on top, then a 2-row table: small label box | big text box | legend."""
    reg, bold = fonts
    if lang == "es":
        h = {k: (((doc.header_es or {}).get(k, "") or "").strip() or doc.header.get(k, ""))
             for k in doc.header}
    else:
        h = doc.header
    s = W / 792.0 if W < H else 1.0          # portrait pages are narrower
    top = H - 14
    x0, x1 = 10, W - 10
    if lang == "es":
        tag = "ESPAÑOL"; tw_ = c.stringWidth(tag, bold, 10) + 16
        c.setFillColor(colors.black); c.rect(x1 - tw_, top - 24, tw_, 18, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont(bold, 10)
        c.drawCentredString(x1 - tw_ / 2, top - 19, tag); c.setFillColor(colors.black)
    # logo
    logo = imgs.get(doc.logo_id)
    lw, lh = 96 * s + 20, 30
    if logo:
        ir, (iw, ih) = logo
        k = min(lw / iw, lh / ih)
        c.drawImage(ir, 18, top - 10 - lh + (lh - ih * k) / 2, iw * k, ih * k, mask="auto")
    # title / subtitle
    c.setFillColor(colors.black)
    title = h.get("udc1", "")
    tw = x1 - x0 - 2 * (lw + 20)
    fs = _fit(title, bold, 18, tw, c)
    c.setFont(bold, fs)
    c.drawCentredString(W / 2, top - 18, title)
    if h.get("udc2", "").strip():
        c.setFont(reg, 10)
        c.drawCentredString(W / 2, top - 32, h["udc2"].strip())

    # table
    rh = 24
    ty = top - 56
    cw1 = 118 * s
    use_q = any(getattr(t, "tasktype", "") == "Quality" for t in doc.tasks)
    legend_w = (272 * s if W > H else 250) + ((70 * s if W > H else 62) if use_q else 0)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(x0, ty - 2 * rh, x1 - x0, 2 * rh)
    c.line(x0, ty - rh, x1, ty - rh)
    c.line(x0 + cw1, ty, x0 + cw1, ty - 2 * rh)
    # row 1: udc3 | udc4 | legend
    _cell_text(c, h.get("udc3", ""), x0, ty - rh, cw1, rh, bold, 7.5, "center")
    _cell_text(c, h.get("udc4", ""), x0 + cw1, ty - rh, x1 - x0 - cw1 - legend_w, rh, bold, 11)
    _cell_text(c, h.get("udc5", ""), x0, ty - 2 * rh, cw1, rh, bold, 7.5, "center")
    _cell_text(c, h.get("udc6", ""), x0 + cw1, ty - 2 * rh, x1 - x0 - cw1, rh, bold, 11)
    # legend (right of row 1)
    lx = x1 - legend_w
    items = ["Check", "Work Content", "Verify", "Safety"] + (["Quality"] if use_q else [])
    lfs = 10 if W > H else 8.5
    labels = {it: (TYPE_ES[it] if lang == "es" else it) for it in items}
    widths = [c.stringWidth(labels[i], bold, lfs) + 22 for i in items]
    pad = (legend_w - sum(widths)) / (len(items) + 1)
    xx = lx + pad
    for it, wv in zip(items, widths):
        _shape(c, it, xx + 8, ty - rh / 2, 7.5, _hex(palette[it]))
        c.setFillColor(colors.black)
        c.setFont(bold, lfs)
        c.drawString(xx + 18, ty - rh / 2 - lfs * .35, labels[it])
        xx += wv + pad
    return ty - 2 * rh


def _footer(c, doc, W, fonts, palette, page_no=1, page_count=1, pdf_name="", date_text="", lang="en"):
    reg, bold = fonts
    y = 12
    c.setFillColor(colors.black)
    c.setFont(reg, 10)
    c.drawString(20, y, (f"Página {page_no} de {page_count}" if lang == "es" else f"Page {page_no} of {page_count}"))
    centre = ((doc.header_es or {}).get("udc7", "").strip() if lang == "es" else "") or doc.header.get("udc7", "").strip()
    if pdf_name:
        tail = pdf_name if len(pdf_name) <= 20 else "..." + pdf_name[-17:]
        centre = f"{centre}  - {tail}" if centre else tail
    c.setFont(reg, 9)
    c.drawCentredString(W / 2, y, centre)
    if date_text:
        c.setFont(reg, 10)
        c.drawRightString(W - 20, y, date_text)

def _pages(tasks):
    """Group consecutive steps with the same layout into pages."""
    pages, i = [], 0
    while i < len(tasks):
        layout = tasks[i].pics_per_page if tasks[i].pics_per_page in LAYOUTS else "4 Picture Landscape"
        cols, rows, _ = LAYOUTS[layout]
        n = cols * rows
        chunk = []
        while i < len(tasks) and len(chunk) < n:
            lt = tasks[i].pics_per_page if tasks[i].pics_per_page in LAYOUTS else "4 Picture Landscape"
            if lt != layout:
                break
            chunk.append(i)
            i += 1
        pages.append((layout, chunk))
    return pages


def _apply_security(c, doc):
    if not doc.encrypt or not doc.password:
        return
    from reportlab.lib.pdfencrypt import StandardEncryption
    sec = doc.security
    allow = lambda k: str(sec.get(k, "")).lower() == "true"
    enc = StandardEncryption(
        doc.password, ownerPassword=doc.password,
        canPrint=allow("AllowPrinting") or allow("AllowDegradedPrinting"),
        canModify=allow("AllowModifyContent") or allow("AllowAssembly"),
        canCopy=allow("AllowCopy") or allow("AllowScreenReaders"),
        canAnnotate=allow("AllowModifyAnnotation") or allow("AllowFillIn"),
        strength=40 if allow("Encrypt40Bit") and not allow("Encrypt128Bit") else 128,
    )
    c._doc.encrypt = enc


def build_instructions_pdf(doc: Document, out, palette=None, quality="Medium",
                           pdf_name: str = "", add_date: bool = True, lang: str = "en") -> None:
    """Visual work instructions, laid out like Visual Instructor's own PDF."""
    import datetime, os
    palette = {**DEFAULT_COLORS, **(palette or {})}
    fonts = _fonts(doc)
    reg, bold = fonts
    imgs = _ImageCache(doc, QUALITY_PX.get(quality, 1400))
    if not pdf_name and isinstance(out, str):
        pdf_name = os.path.basename(out)
    today = datetime.date.today()
    date_text = f"{today.month}/{today.day}/{today.year}" if add_date else ""

    c = canvas.Canvas(out, pagesize=landscape(letter))
    c.setTitle(((doc.header_es or {}).get("udc1") if lang == "es" else "") or doc.header.get("udc1") or doc.name)
    c.setAuthor(doc.header.get("udc6", ""))
    _apply_security(c, doc)
    pages = _pages(doc.tasks) or [("4 Picture Landscape", [])]
    black = colors.black

    for pno, (layout, idxs) in enumerate(pages, 1):
        cols, rows, orient = LAYOUTS[layout]
        size = landscape(letter) if orient == "L" else portrait(letter)
        c.setPageSize(size)
        W, H = size
        body_top = _header(c, doc, W, H, fonts, imgs, palette, lang) - 7
        body_bot = 30
        gap = 7
        x0, x1 = 10, W - 10
        cw = (x1 - x0 - gap * (cols - 1)) / cols
        ch = (body_top - body_bot - gap * (rows - 1)) / rows
        n = cols * rows
        dense = n >= 6
        for k, ti in enumerate(idxs):
            t = doc.tasks[ti]
            col, row = k % cols, k // cols
            x = x0 + col * (cw + gap)
            y = body_top - (row + 1) * ch - row * gap
            accent = _hex(palette.get(t.tasktype, palette["Work Content"]))

            # outer coloured frame
            fw = 3.2 if doc.borders else 0
            if doc.borders:
                c.setStrokeColor(accent)
                c.setLineWidth(fw)
                c.rect(x + fw / 2, y + fw / 2, cw - fw, ch - fw, fill=0, stroke=1)
            ix, iy, iw_, ih_ = x + fw + 1, y + fw + 1, cw - 2 * fw - 2, ch - 2 * fw - 2

            # inner black box + top row
            top_h = min(42, ih_ * 0.24) if not dense else min(34, ih_ * 0.28)
            shape_w = top_h
            side_w = min(52, iw_ * 0.15)
            c.setStrokeColor(black)
            c.setLineWidth(1)
            c.rect(ix, iy, iw_, ih_)
            c.line(ix, iy + ih_ - top_h, ix + iw_, iy + ih_ - top_h)
            c.line(ix + shape_w, iy + ih_, ix + shape_w, iy + ih_ - top_h)
            c.line(ix + iw_ - side_w, iy + ih_, ix + iw_ - side_w, iy + ih_ - top_h)
            c.line(ix + iw_ - side_w, iy + ih_ - top_h / 2, ix + iw_, iy + ih_ - top_h / 2)

            # step marker
            r = top_h * 0.3
            if doc.shapes:
                _shape(c, t.tasktype, ix + shape_w / 2, iy + ih_ - top_h / 2, r, accent,
                       number=ti + 1, bold=bold, fs=max(7, r * 0.95))
            else:
                c.setFillColor(black); c.setFont(bold, max(7, r))
                c.drawCentredString(ix + shape_w / 2, iy + ih_ - top_h / 2 - r * .35, str(ti + 1))

            # caption (top-aligned like the original)
            from reportlab.lib.utils import simpleSplit
            cap_src = (t.caption_es if lang == "es" and (t.caption_es or "").strip() else t.caption)
            cap_w = iw_ - shape_w - side_w - 6
            fsz = float(t.font_size or 12)
            fsz = min(fsz, 12.0) * (0.75 if dense else 1.0)
            while True:
                lines = simpleSplit(cap_src.strip(), reg, fsz, cap_w)
                if len(lines) * fsz * 1.02 <= top_h - 2 or fsz <= 5:
                    break
                fsz -= 0.5
            c.setFillColor(black)
            c.setFont(reg, fsz)
            yy = iy + ih_ - fsz * 0.95
            for ln in lines:
                c.drawString(ix + shape_w + 4, yy, ln)
                yy -= fsz * 1.02
            if t.cycletime.strip():
                c.setFont(reg, 7)
                c.drawCentredString(ix + iw_ - side_w / 2, iy + ih_ - top_h / 2 + top_h / 4 - 2.5, t.cycletime.strip())

            # picture
            img = imgs.get(t.image_id)
            ax, ay, aw, ah = ix + 2, iy + 2, iw_ - 4, ih_ - top_h - 4
            if img:
                ir, (pw, ph) = img
                s = min(aw / pw, ah / ph)
                c.drawImage(ir, ax + (aw - pw * s) / 2, ay + (ah - ph * s) / 2, pw * s, ph * s)
        _footer(c, doc, W, fonts, palette, pno, len(pages), pdf_name, date_text, lang)
        c.showPage()
    c.save()

def _num(v):
    try:
        return float(str(v).strip())
    except ValueError:
        return 0.0


def build_soe_pdf(doc: Document, out, palette=None, pdf_name: str = "") -> None:
    """Standard Operation Elements sheet: per-step analysis table and totals."""
    palette = {**DEFAULT_COLORS, **(palette or {})}
    fonts = _fonts(doc)
    reg, bold = fonts
    imgs = _ImageCache(doc, 1000)
    W, H = landscape(letter)
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle((doc.header.get("udc1") or doc.name) + " - SOE")
    _apply_security(c, doc)

    hdr = ["#", "Task", "Type", "Cycle", "VA", "NVA", "C&V", "Setup", "Work", "Mach.", "Labor",
           "OvrP", "OvrPr", "Wait", "Trans", "Inv", "Move", "Def"]
    small = ParagraphStyle("s", fontName=reg, fontSize=7.5, leading=9)
    X = "✓"
    rows = []
    for i, t in enumerate(doc.tasks, 1):
        rows.append([
            str(i), Paragraph(escape(t.caption.strip()), small), t.tasktype, t.cycletime,
            X if t.value_added else "", X if (t.non_value_added and not t.value_added and not t.tqc) else "",
            X if t.tqc else "",
            X if t.setup.get("selected") else "", X if t.work.get("selected") else "",
            X if (t.setup.get("machine") or t.work.get("machine")) else "",
            X if (t.setup.get("labor") or t.work.get("labor")) else "",
            *[X if t.wastes.get(w) else "" for w in WASTES],
        ])
    total = sum(_num(t.cycletime) for t in doc.tasks)
    va = sum(_num(t.cycletime) for t in doc.tasks if t.value_added)
    widths = [20, 290, 62, 34] + [26] * 7 + [28] * 7
    usable = W - 2 * MARGIN
    scale = usable / sum(widths)
    widths = [w * scale for w in widths]

    # paginate rows
    page_rows, chunk, est = [], [], 0
    for r in rows:
        _, h = r[1].wrap(widths[1] - 6, 1000)
        if est + h + 6 > H - 2 * MARGIN - 150 and chunk:
            page_rows.append(chunk); chunk, est = [], 0
        chunk.append(r); est += h + 6
    page_rows.append(chunk)

    for pno, chunk in enumerate(page_rows, 1):
        top = _header(c, doc, W, H, fonts, imgs, palette)
        data = [hdr] + chunk
        tbl = Table(data, colWidths=widths, repeatRows=1)
        style = [
            ("FONT", (0, 0), (-1, 0), bold, 7),
            ("FONT", (0, 1), (-1, -1), reg, 7.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#888888")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("FONT", (4, 1), (-1, -1), "ZapfDingbats", 8),
        ]
        for ri, r in enumerate(chunk, 1):
            kind = r[2]
            col = _hex(palette.get(kind, "#FFFFFF"))
            style.append(("BACKGROUND", (2, ri), (2, ri), colors.Color(col.red, col.green, col.blue, alpha=0.35)))
        tbl.setStyle(TableStyle(style))
        tw, th = tbl.wrapOn(c, usable, H)
        tbl.drawOn(c, MARGIN, top - 10 - th)
        if pno == len(page_rows):
            y = top - 10 - th - 22
            c.setFont(bold, 9)
            c.setFillColor(colors.black)
            nva = total - va
            txt = (f"Total cycle time: {total:g}    Value added: {va:g}"
                   f"    Non-value added: {nva:g}")
            if total:
                txt += f"    VA ratio: {va / total * 100:.0f}%"
            c.drawString(MARGIN, y, txt)
            counts = {w: sum(1 for t in doc.tasks if t.wastes.get(w)) for w in WASTES}
            c.setFont(reg, 8)
            c.drawString(MARGIN, y - 13, "Wastes flagged:  " + "   ".join(
                f"{k.replace('operatormovement', 'movement').title()}: {v}" for k, v in counts.items()))
        _footer(c, doc, W, fonts, palette, pno, len(page_rows), pdf_name)
        c.showPage()
    c.save()
