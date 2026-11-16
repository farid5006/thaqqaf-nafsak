"""موديول قراءة المستندات الموحد (docx, txt, md, html) بدون مكتبات خارجية."""
import os
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser


class _HTMLTextExtractor(HTMLParser):
    IGNORE = {"style", "script", "head", "svg", "noscript"}

    def __init__(self):
        super().__init__()
        self.lines, self._current, self._ign = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.IGNORE: self._ign += 1

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in self.IGNORE and self._ign > 0: self._ign -= 1
        if self._ign == 0 and t in ("p", "div", "li", "br", "h1", "h2", "h3", "h4", "tr"):
            text = "".join(self._current).strip()
            if text: self.lines.append(text)
            self._current = []

    def handle_data(self, data):
        if self._ign == 0: self._current.append(data)

    def get_text(self):
        if self._current and self._ign == 0:
            text = "".join(self._current).strip()
            if text: self.lines.append(text)
        return "\n".join(self.lines)


def read_text_from_file(file_path: str) -> str:
    """قراءة محتوى الملفات (docx, txt, md, html) وإرجاع نصوصها موحدة."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"الملف غير موجود: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".docx":
        return _read_docx(file_path)
    if ext in (".html", ".htm"):
        return _read_html(file_path)
    return _read_plain_text(file_path)


def _read_docx(file_path: str) -> str:
    """استخراج النصوص من مستندات Word دون أي مكتبات خارجية."""
    lines = []
    w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    with zipfile.ZipFile(file_path, "r") as zf:
        if "word/document.xml" not in zf.namelist():
            return ""
        xml_content = zf.read("word/document.xml")
        tree = ET.fromstring(xml_content)
        for p in tree.iter(f"{{{w_ns}}}p"):
            texts = [t.text for t in p.iter(f"{{{w_ns}}}t") if t.text]
            para_text = "".join(texts).strip()
            if para_text:
                lines.append(para_text)
    return "\n".join(lines)


def _read_html(file_path: str) -> str:
    raw = _read_plain_text(file_path)
    parser = _HTMLTextExtractor()
    parser.feed(raw)
    return parser.get_text()


def _read_plain_text(file_path: str) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1256", "latin-1"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
