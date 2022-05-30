from abc import ABC
from random import choice
from typing import Any, ClassVar
from xml.etree.ElementTree import Element

from pydantic import Field

from ..data import STRING_DATA
from .base import Child, Parent, Tagged
from ..exceptions import Sad


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

    def _load(self) -> str:
        from ftl import FTL

        txt = FTL.text_lists.get(self.load).draw().render()

        return f":game_die: {txt}"

    def render(self) -> str:
        return self.text or self._lookup() or self._load()

    def __rich__(self) -> str:
        out = self.render()
        if out is None:
            raise Sad()
        return out


@Text.attach
class TextList(Parent, StringLookup):
    tag_name: ClassVar[str] = "textList"
    text: list[Text] = Field(default_factory=list)

    @classmethod
    def from_elem(cls, e: Element):
        kw: dict[str, Any] = e.attrib.copy()
        kw["text"] = list()
        return cls._from_elem(e, kw)

    def draw(self) -> Text:
        """draws a string from its list, returns the fetched instance"""
        return choice(self.text)
