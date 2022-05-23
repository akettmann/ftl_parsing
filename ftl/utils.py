import io
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree


def get_xml(e: Element) -> str:
    buffer = io.StringIO()
    et = ElementTree(e)
    et.write(buffer, "unicode")
    return buffer.getvalue()


def dump_xml(path: Path, *elements: Element):
    parent = Element("FTL")
    parent.extend(elements)
    path.write_text(get_xml(parent))
