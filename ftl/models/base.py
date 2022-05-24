from abc import abstractmethod
from functools import wraps
from typing import ClassVar, Type, TypeVar
from xml.etree.ElementTree import Element

from pydantic import BaseModel as BaseM, Field

from ..data import STRING_DATA


class Tracker:
    _children = set()

    @classmethod
    def track(cls, c: Type):
        cls._children.add(c)

        @wraps(c)
        def inner(*args, **kwargs):
            return c(*args, **kwargs)

        return inner


class JustAttribs:
    @classmethod
    def from_elem(cls, e: Element):
        # noinspection PyArgumentList
        return cls(**e.attrib)


class BaseModel(BaseM):
    class Config:
        allow_population_by_field_name = True


class ElementModel(BaseModel):
    tag_name: ClassVar[str]

    @classmethod
    @abstractmethod
    def from_elem(cls, e: Element):
        raise NotImplementedError()


class StringLookup(BaseModel):
    id_: str = Field(alias="id")

    @staticmethod
    def _lookup(name: str) -> str:
        return STRING_DATA.get(name, "STRING NOT FOUND")

    def __str__(self):
        return self._lookup(self.id_)


M = TypeVar("M", bound=ElementModel)
