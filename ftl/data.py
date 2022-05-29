import logging
import re
from io import StringIO
from pathlib import Path
from typing import Iterable
from xml.etree.ElementTree import Element, ElementTree, parse, ParseError

LOG = logging.getLogger()
RESOURCES_DIR = Path(__file__).parent / "resources"
DATA_DIR = RESOURCES_DIR / "data"
RAW_DATA = Element("FTL")


def _hack(xmlfp: Path) -> ElementTree:
    """To deal with xml files that have multiple root elements, wraps it (after the
    encoding declaration) in an `<FTL>` tag"""
    fake_fp = StringIO(
        re.sub(r"(<\?xml[^>]+\?>)", r"\1<FTL>", xmlfp.read_text()) + "</FTL>"
    )
    return parse(fake_fp)


def _load_data():
    global RAW_DATA
    for xmlfp in DATA_DIR.glob("*.xml"):
        try:
            tree = parse(xmlfp)
        except ParseError as err:
            try:
                tree = _hack(xmlfp)
            except ParseError:
                LOG.warning(
                    f"File `{str(xmlfp.absolute())}` is not valid XML.\n"
                    f"Original error: `{err.msg}`"
                )
                continue
        for e in tree.iter("FTL"):
            RAW_DATA.extend(e)


def load_one_thing(tag: str, name: str) -> Element:
    e = list(load_all_things(tag, (name,)))
    assert len(e) == 1
    return e[0]


def load_all_things(tag: str, names: Iterable[str] = ()) -> Iterable[Element]:
    for name in names:
        yield from RAW_DATA.findall(f".{tag}[@name='{name}']")


_load_data()
STRING_DATA = {sub.get("name"): sub.text for sub in RAW_DATA.findall("text[@name]")}
