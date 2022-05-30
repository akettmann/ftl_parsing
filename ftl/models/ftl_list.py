# Named it goofy so that I don't clobber list on accident
from abc import ABC
from random import choice
from typing import Any, TypeVar
from xml.etree.ElementTree import Element

from .base import ElementModel, Parent

M = TypeVar("M")


class BaseList(Parent, ABC):
    contents: dict[str, ElementModel]

    @classmethod
    def from_elem(cls, e: Element):
        kw: dict[str, Any] = e.attrib.copy()
        kw["contents"] = dict()
        return cls._from_elem(e, kw)

    def draw(self) -> ElementModel:
        """draws a string from its list, returns the fetched instance"""
        return choice(list(self.contents.values()))

    def get(self, key: str, default=None):
        return self.contents.get(key, default)

    @classmethod
    def adopt(cls, kls, tag_name: str, destination: str):
        """This override is because we don't care where something thinks it is going,
        it is going to content"""
        cls._dependents.add(tag_name)
        cls._child_tags[tag_name] = (kls, "content")
