import io
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree

from rich.table import Table
from rich.console import group


def get_xml(e: Element) -> str:
    buffer = io.StringIO()
    et = ElementTree(e)
    et.write(buffer, "unicode")
    return buffer.getvalue()


def dump_xml(path: Path, *elements: Element):
    parent = Element("FTL")
    parent.extend(elements)
    path.write_text(get_xml(parent))


@group
def make_element_group(e: Element):
    attr_table = Table("Name", "Value", title=f"Attributes of {e.tag}")
    for k, v in e.attrib.items():
        attr_table.add_row(k, v)
