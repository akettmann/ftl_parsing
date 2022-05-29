from abc import abstractmethod
from functools import wraps
from typing import ClassVar, Type, TypeVar
from xml.etree.ElementTree import Element

from inflection import underscore
from pydantic import BaseModel as BaseM, Field

# noinspection PyProtectedMember
from pydantic.main import ModelMetaclass

from ..data import STRING_DATA


class TrackDependentsMeta(ModelMetaclass):
    # noinspection PyTypeHints
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        cls._dependents: ClassVar[dict[str, Type["ElementModel"]]] = {}
        cls._tag_set: ClassVar[set[str]] = set()
        return cls


class Tagged:
    tag_name: ClassVar[str]
    py_tag_name: ClassVar[str]


class Parent(Tagged, metaclass=TrackDependentsMeta):
    _dependents: ClassVar[set] = set()
    _child_tags: ClassVar[dict] = {}

    @classmethod
    def adopt(cls, kls, tag_name: str, destination: str):
        cls._dependents.add(kls)
        cls._child_tags[tag_name] = (kls, destination)


class Child(Tagged):
    @classmethod
    def attach(
        cls, kls: Type[Parent] = None, *, tag_name: str = None, destination: str = None
    ):
        def adopt():
            nonlocal tag_name, destination
            tag_name = tag_name or cls.tag_name
            destination = destination or cls.py_tag_name
            kls.adopt(cls, tag_name, destination)
            # We don't even want to wrap this, just return the class here
            return kls

        if kls is None:

            def wrap_class(k: Type[Parent]):
                nonlocal kls
                kls = k
                return adopt()

            return wrap_class
        return adopt()


class JustAttribs:
    @classmethod
    def from_elem(cls, e: Element):
        # noinspection PyArgumentList
        return cls(**e.attrib)


class BaseModel(BaseM):
    class Config:
        allow_population_by_field_name = True


class ElementModel(BaseModel, metaclass=TrackDependentsMeta):
    tag_name: ClassVar[str] = ""
    _dependents: ClassVar[dict[str, Type["ElementModel"]]] = dict()
    _tag_set: ClassVar[set[str]] = set()

    @classmethod
    def attach(cls, parent: Type["ElementModel"]):
        parent.adopt(cls)
        return parent

    @classmethod
    def adopt(cls, other: Type["ElementModel"]):
        cls._dependents[other.tag_name] = other
        cls._tag_set.add(other.tag_name)
        return other

    @classmethod
    @abstractmethod
    def from_elem(cls, e: Element):
        raise NotImplementedError()

    @classmethod
    def py_tag_name(cls) -> str:
        return underscore(cls.tag_name)


class StringLookup(BaseModel):
    id_: str = Field(None, alias="id")
    name: str = None

    @staticmethod
    def _lookup(name: str) -> str:
        return STRING_DATA.get(name, "STRING NOT FOUND")

    def __str__(self):
        return self._lookup(self.id_)


M = TypeVar("M", bound=ElementModel)
