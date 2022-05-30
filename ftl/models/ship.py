from typing import ClassVar
from xml.etree.ElementTree import Element

from ftl.models.base import JustAttribs, Child


class Ship(JustAttribs, Child):
    tag_name: ClassVar[str] = "ship"
    """
    Note that this can be used as a "diff" 
    """
    load: str = None
    hostile: bool = False


class Fleet(Child):
    tag_name: ClassVar[str] = "fleet"
    text: str

    @classmethod
    def from_elem(cls, e: Element):
        return cls(text=e.text)
