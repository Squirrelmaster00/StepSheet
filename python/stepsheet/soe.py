"""Read and write .soe work-instruction files.

A .soe file is ISO-8859-1 XML:

<roots>
  <mainroot>
    <version>4.0</version>
    <FileInfo><name/><url/></FileInfo>
    <FileProperties> header fields (udc1..udc7), options, PDF security, logo </FileProperties>
    <isDirty/>
    <FileData> one <Task> per step </FileData>
  </mainroot>
  <imageroot><images> <GUID>base64 jpeg</GUID> ... </images></imageroot>
</roots>
"""
from __future__ import annotations

import base64
import io
import os
import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict

TASK_TYPES = ["Work Content", "Check", "Verify", "Safety", "Quality"]
# "Quality" is a step type the original .soe program doesn't know: saved as Safety plus a
# <customtype> tag it ignores. Any other type can also be flagged quality-critical
# (Check + Quality); that flag is saved in a <quality> tag the old program also ignores.
CUSTOM_TYPES = {"Quality": "Safety"}
PAGE_TYPES = [
    "1 Picture Landscape", "1 Picture Portrait", "2 Picture Portrait", "4 Picture Landscape",
    "4 Picture Portrait", "6 Picture Landscape", "6 Picture Portrait",
    "9 Picture Portrait",
]
WASTES = ["overproduction", "overprocessing", "waiting", "transport",
          "inventory", "operatormovement", "defects"]
SECURITY_FLAGS = ["Encrypt128Bit", "Encrypt40Bit", "AllowPrinting", "AllowCopy",
                  "AllowFillIn", "AllowModifyAnnotation", "AllowModifyContent",
                  "AllowAssembly", "AllowScreenReaders", "AllowDegradedPrinting"]

# Header boxes as the original Options dialog labels them.
HEADER_LABELS = {
    "udc1": "Title",
    "udc2": "Subtitle (row 1, box 2)",
    "udc3": "Row 2, box 1",
    "udc4": "Row 2, box 2",
    "udc5": "Row 3, box 1",
    "udc6": "Row 3, box 2",
    "udc7": "Footer",
}


def new_image_id() -> str:
    """GUID-shaped id that is also a valid XML tag name (starts with A-F)."""
    h = "%032X" % random.getrandbits(128)
    h = random.choice("ABCDEF") + h[1:]
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


def _b(v) -> bool:
    return str(v).strip().lower() == "true"


def _s(v: bool) -> str:
    return "true" if v else "false"


@dataclass
class Task:
    caption: str = ""
    tasktype: str = "Work Content"
    pics_per_page: str = "4 Picture Landscape"
    cycletime: str = ""
    image_id: str = ""
    image_title: str = ""
    image_path: str = ""
    font_size: str = "12"
    caption_es: str = ""
    caption_es_src: str = ""
    quality: bool = False   # quality-critical flag on top of the step type
    wastes: dict = field(default_factory=lambda: {w: False for w in WASTES})
    setup: dict = field(default_factory=lambda: {"selected": False, "machine": False, "labor": False})
    work: dict = field(default_factory=lambda: {"selected": True, "machine": False, "labor": False})
    value_added: bool = False
    non_value_added: bool = True
    tqc: bool = False

    @property
    def value_class(self) -> str:
        if self.value_added:
            return "VA"
        if self.tqc:
            return "TQC"
        return "NVA"


@dataclass
class Document:
    name: str = "untitled.soe"
    url: str = ""
    version: str = "4.0"
    header: dict = field(default_factory=lambda: {k: "" for k in HEADER_LABELS})
    header_es: dict = field(default_factory=lambda: {k: "" for k in HEADER_LABELS})
    advanced: bool = True
    borders: bool = True
    shapes: bool = True
    template: str = "Standard"
    soe_title: bool = True
    encrypt: bool = False
    password: str = ""
    security: dict = field(default_factory=lambda: {k: "" for k in SECURITY_FLAGS})
    font: str = "helvetica"
    default_ppp: str = "4 Picture Landscape"
    logo_path: str = ""
    logo_id: str = ""
    tasks: list = field(default_factory=list)
    images: dict = field(default_factory=dict)  # id -> raw image bytes

    # ---------------------------------------------------------------- load
    @classmethod
    def load(cls, path_or_bytes) -> "Document":
        if isinstance(path_or_bytes, (bytes, bytearray)):
            root = ET.fromstring(path_or_bytes)
        else:
            root = ET.parse(path_or_bytes).getroot()
        m = root.find("mainroot")
        d = cls()
        d.version = m.findtext("version", "4.0")
        d.name = m.findtext("FileInfo/name", "untitled.soe")
        d.url = m.findtext("FileInfo/url", "")
        p = m.find("FileProperties")
        if p is not None:
            for k in HEADER_LABELS:
                d.header[k] = p.findtext(k, "")
                d.header_es[k] = p.findtext(k + "_es", "")
            d.advanced = _b(p.findtext("Advanced", "true"))
            d.borders = _b(p.findtext("Borders", "true"))
            d.shapes = _b(p.findtext("Shapes", "true"))
            d.template = p.findtext("Template", "Standard")
            d.soe_title = _b(p.findtext("SOETitle", "true"))
            d.encrypt = _b(p.findtext("Encrypt", "false"))
            d.password = p.findtext("password", "")
            for k in SECURITY_FLAGS:
                d.security[k] = p.findtext(k, "")
            d.font = p.findtext("Font", "helvetica")
            d.default_ppp = p.findtext("DefaultPPP", "4 Picture Landscape")
            d.logo_path = p.findtext("logo/imagepath", "")
            d.logo_id = p.findtext("logo/imageid", "")
        for t in m.findall("FileData/Task"):
            a = t.find("Analysis")
            task = Task(
                caption=t.findtext("caption", ""),
                tasktype=t.findtext("tasktype", "Work Content"),
                pics_per_page=t.findtext("PicsPerPage", d.default_ppp),
                cycletime=t.findtext("cycletime", ""),
                image_id=t.findtext("VmsInfo/imageid", ""),
                image_title=t.findtext("VmsInfo/imagetitle", ""),
                image_path=t.findtext("VmsInfo/imagepath", ""),
                font_size=t.findtext("VmsInfo/FontSize", "12"),
                caption_es=t.findtext("caption_es", ""),
                caption_es_src=t.findtext("caption_es_src", ""),
            )
            task.quality = (t.findtext("quality", "") or "").strip().lower() == "true"
            ct = (t.findtext("customtype", "") or "").strip()
            if ct in CUSTOM_TYPES:
                task.tasktype = ct
            if a is not None:
                task.wastes = {w: _b(a.findtext(f"Muda/{w}", "false")) for w in WASTES}
                task.setup = {k: _b(a.findtext(f"Setup/{k}", "false")) for k in ("selected", "machine", "labor")}
                task.work = {k: _b(a.findtext(f"Work/{k}", "false")) for k in ("selected", "machine", "labor")}
                task.value_added = _b(a.findtext("ValueAdded", "false"))
                task.non_value_added = _b(a.findtext("NonValueAdded", "false"))
                task.tqc = _b(a.findtext("TQC", "false"))
            d.tasks.append(task)
        imgs = root.find("imageroot/images")
        if imgs is not None:
            for e in imgs:
                txt = "".join((e.text or "").split())
                if txt:
                    d.images[e.tag] = base64.b64decode(txt)
        return d

    # ---------------------------------------------------------------- save
    def to_xml(self) -> bytes:
        def cd(tag, val):
            val = "" if val is None else str(val)
            if val == "":
                return f"<{tag}/>"
            return f"<{tag}><![CDATA[{val.replace(']]>', ']]]]><![CDATA[>')}]]></{tag}>"

        def cd_keep(tag, val):  # always write CDATA, even when empty (matches original)
            val = "" if val is None else str(val)
            return f"<{tag}><![CDATA[{val}]]></{tag}>"

        o = ['<?xml version="1.0" encoding="ISO-8859-1"?><roots><mainroot>']
        o.append(cd_keep("version", self.version))
        o.append("<FileInfo>" + cd_keep("name", self.name) + cd_keep("url", self.url) + "</FileInfo>")
        o.append("<FileProperties>")
        for k in HEADER_LABELS:
            o.append(cd_keep(k, self.header.get(k, "")))
        o.append(cd_keep("Advanced", _s(self.advanced)))
        o.append(cd_keep("Borders", _s(self.borders)))
        o.append(cd_keep("Shapes", _s(self.shapes)))
        o.append(cd_keep("Template", self.template))
        o.append(cd_keep("SOETitle", _s(self.soe_title)))
        o.append(cd_keep("Encrypt", _s(self.encrypt)))
        o.append(cd("password", self.password))
        for k in SECURITY_FLAGS:
            o.append(cd(k, self.security.get(k, "")))
        o.append(cd_keep("Font", self.font))
        o.append(cd_keep("DefaultPPP", self.default_ppp))
        o.append("<logo>" + cd("imagepath", self.logo_path) + cd("imageid", self.logo_id) + "</logo>")
        for k in HEADER_LABELS:
            if (self.header_es.get(k, "") or "").strip():
                o.append(cd_keep(k + "_es", self.header_es[k]))
        o.append("</FileProperties>")
        o.append(cd_keep("isDirty", "false"))
        o.append("<FileData>")
        for t in self.tasks:
            o.append("<Task><VmsInfo>")
            o.append(cd("imagetitle", t.image_title) + cd("imagepath", t.image_path)
                     + cd("imageid", t.image_id) + cd_keep("FontSize", t.font_size))
            o.append("</VmsInfo><Analysis><Muda>")
            o.extend(cd_keep(w, _s(t.wastes.get(w, False))) for w in WASTES)
            o.append("</Muda><Setup>")
            o.extend(cd_keep(k, _s(t.setup.get(k, False))) for k in ("selected", "machine", "labor"))
            o.append("</Setup><Work>")
            o.extend(cd_keep(k, _s(t.work.get(k, False))) for k in ("selected", "machine", "labor"))
            o.append("</Work>")
            o.append(cd_keep("ValueAdded", _s(t.value_added)) + cd_keep("NonValueAdded", _s(t.non_value_added))
                     + cd_keep("TQC", _s(t.tqc)))
            o.append("</Analysis>")
            o.append(cd("cycletime", t.cycletime) + cd_keep("tasktype", CUSTOM_TYPES.get(t.tasktype, t.tasktype))
                     + cd_keep("PicsPerPage", t.pics_per_page) + cd_keep("caption", t.caption))
            if t.tasktype in CUSTOM_TYPES:
                o.append(cd_keep("customtype", t.tasktype))
            elif t.quality:
                o.append(cd_keep("quality", "true"))
            if (t.caption_es or "").strip():
                o.append(cd_keep("caption_es", t.caption_es) + cd_keep("caption_es_src", t.caption_es_src))
            o.append("</Task>")
        o.append("</FileData></mainroot><imageroot><images>")
        used = self.used_image_ids()
        for iid, data in self.images.items():
            if iid not in used:
                continue
            b = base64.b64encode(data).decode("ascii")
            wrapped = "\n".join(b[i:i + 76] for i in range(0, len(b), 76))
            o.append(f"<{iid}>{wrapped}\n</{iid}>")
        o.append("</images></imageroot></roots>")
        return "".join(o).encode("iso-8859-1", errors="replace")

    def save(self, path: str) -> None:
        self.name = os.path.basename(path)
        self.url = os.path.abspath(path)
        data = self.to_xml()
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)

    # ---------------------------------------------------------------- helpers
    def used_image_ids(self) -> set:
        ids = {t.image_id for t in self.tasks if t.image_id}
        if self.logo_id:
            ids.add(self.logo_id)
        return ids

    def add_image(self, data: bytes, max_px: int = 1600, quality: int = 85) -> str:
        """Store an image (re-encoded as JPEG like the original) and return its id."""
        try:
            from PIL import Image, ImageOps
            im = Image.open(io.BytesIO(data))
            im = ImageOps.exif_transpose(im)
            if im.mode not in ("RGB", "L"):
                bg = Image.new("RGB", im.size, "white")
                bg.paste(im, mask=im.convert("RGBA").split()[-1])
                im = bg
            im.thumbnail((max_px, max_px))
            buf = io.BytesIO()
            im.convert("RGB").save(buf, "JPEG", quality=quality)
            data = buf.getvalue()
        except Exception:
            pass
        iid = new_image_id()
        self.images[iid] = data
        return iid

    # JSON-friendly view for the UI (no image bytes)
    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("images")
        return d

    def update_from_dict(self, d: dict) -> None:
        for k in ("name", "header", "advanced", "borders", "shapes", "template", "soe_title",
                  "encrypt", "password", "security", "font", "default_ppp", "logo_path", "logo_id"):
            if k in d:
                setattr(self, k, d[k])
        if "tasks" in d:
            self.tasks = [Task(**{k: v for k, v in t.items() if k in Task.__dataclass_fields__})
                          for t in d["tasks"]]
