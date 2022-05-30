from abc import ABC, abstractmethod
from typing import Any, ClassVar, Iterator, Type, TypeVar
from xml.etree.ElementTree import Element

from inflection import underscore
from pydantic import BaseModel as BaseM

# noinspection PyProtectedMember
from pydantic.main import ModelMetaclass

from ftl.exceptions import Sad


class TrackDependentsMeta(ModelMetaclass):
    # noinspection PyTypeHints
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        cls._dependents: ClassVar[set[str]] = set()
        cls._tag_set: ClassVar[set[str]] = set()
        return cls


class JustAttribs:
    @classmethod
    def from_elem(cls, e: Element):
        # noinspection PyArgumentList
        return cls(**e.attrib)


class BaseModel(BaseM):
    class Config:
        allow_population_by_field_name = True


class Tagged(BaseModel):
    @property
    @classmethod
    @abstractmethod
    def tag_name(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def py_tag_name(cls) -> str:
        # noinspection PyTypeChecker
        return underscore(cls.tag_name)

    @classmethod
    @abstractmethod
    def from_elem(cls, e: Element):
        raise NotImplementedError()


class ElementModel(Tagged):
    tag_name: ClassVar[str] = ""

    @classmethod
    @abstractmethod
    def from_elem(cls, e: Element):
        raise NotImplementedError()


M = TypeVar("M", bound=ElementModel)


class Parent(Tagged, ABC, metaclass=TrackDependentsMeta):
    _dependents: ClassVar[set] = set()
    _child_tags: ClassVar[dict] = {}

    @classmethod
    def adopt(cls, kls, tag_name: str, destination: str):
        cls._dependents.add(tag_name)
        cls._child_tags[tag_name] = (kls, destination)

    @classmethod
    def _from_elem(cls, e: Element, kw: dict = None):
        """This default implementation will take care of any elements handled by
        Children that are attached, though the class still needs to have the field
        required."""
        kw: dict[str, Any] = kw or e.attrib.copy()
        for sub in cls._xml_to_model(e, kw):
            match sub:
                case _:
                    raise Sad.from_sub_elem(e, sub)
        # noinspection PyArgumentList
        return cls(**kw)

    @classmethod
    def _xml_to_model(cls, e: Element, kw: dict[str, Any]) -> Iterator[Element]:
        """This iterates over the sub elements and yields the ones it doesn't handle"""
        for sub in e:
            match sub:
                case Element(tag=tag) if tag in cls._dependents:
                    (kls, destination) = cls._child_tags[tag]
                    d = kw.get(destination, False)
                    if isinstance(d, list):
                        d.append(kls.from_elem(sub))
                    else:
                        kw[destination] = kls.from_elem(sub)
                case _:
                    yield sub


class Child(Tagged, ABC):
    @classmethod
    def attach(
        cls, kls: Type[Parent] = None, *, tag_name: str = None, destination: str = None
    ):
        def attach():
            nonlocal tag_name, destination
            tag_name = tag_name or cls.tag_name
            destination = destination or cls.py_tag_name()
            kls.adopt(cls, tag_name=tag_name, destination=destination)
            # We don't even want to wrap this, just return the class here
            return kls

        if kls is None:

            def wrap_class(k: Type[Parent]):
                nonlocal kls
                kls = k
                return attach()

            return wrap_class
        return attach()
