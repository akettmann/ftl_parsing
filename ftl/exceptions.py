from xml.etree.ElementTree import Element

from ftl.utils import get_xml


class Sad(BaseException):
    @classmethod
    def from_elem(cls, e: Element):
        return Sad(f"Unhandled element: `{get_xml(e)}`")
