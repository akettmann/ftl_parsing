from abc import ABC
from typing import ClassVar
from xml.etree.ElementTree import Element

from pydantic import Field
from rich.console import RenderableType

from .ftl_list import BaseList
from ..data import STRING_DATA
from .base import Child, Tagged


class StringLookup(Tagged, ABC):
    id_: str = Field(None, alias="id")
    name: str = None
    load: str = Field(
        None, description="This indicates a text list to load a text from"
    )

    def _lookup(self) -> str:
        return STRING_DATA.get(self.id_, None)


class Text(Child, StringLookup):
    tag_name: ClassVar[str] = "text"
    text: str = None
    id_: str = Field(None, alias="id")
    load: str = None

    @classmethod
    def from_elem(cls, e: Element):
        kw = e.attrib.copy()
        if e.text and e.text.strip():
            kw["text"] = e.text.strip()
        return cls(**kw)

    def get_ref(self) -> "TextList":
        from ftl import FTL

        return FTL.text_lists.get(self.load)

    def render(self) -> RenderableType:
        return self.text or self._lookup() or self.get_ref()

    def __rich__(self) -> RenderableType:
        return self.render()


@Text.attach()
class TextList(BaseList):
    tag_name: ClassVar[str] = "textList"
    name: str
