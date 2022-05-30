from abc import ABC
from typing import ClassVar
from xml.etree.ElementTree import Element

from pydantic import Field

from ftl.exceptions import Sad
from ftl.models.base import JustAttribs, Child, Parent
from ftl.models.text import StringLookup, Text


class Item(JustAttribs, StringLookup, Child, ABC):
    """This holds the name of a loot table that an item will come from as a result of an
    event"""


class Augment(Item):
    tag_name: ClassVar[str] = "augment"


class Weapon(Item):
    tag_name: ClassVar[str] = "weapon"


class Drone(Item):
    tag_name: ClassVar[str] = "drone"


class Remove(Item):
    tag_name: ClassVar[str] = "remove"
    """
    This says what you will lose when this event happens, kind of Anti-Loot
    """


class CrewMember(Item):
    """People are things too apparently"""

    tag_name: ClassVar[str] = "crewMember"
    amount: int
    class_: str = Field(None, alias="class")


class Damage(Remove):
    tag_name: ClassVar[str] = "damage"


class EventLoot(Parent, ABC):
    """Using this class to track, not to actually create"""

    pass


@Text.attach
class RemoveCrew(Remove, Parent):
    tag_name: ClassVar[str] = "removeCrew"
    clone: bool = Field(True, description="True means you are able to clone them")
    text: Text = None

    @classmethod
    def from_elem(cls, e: Element):
        if len(e) == 0:
            return super().from_elem(e)
        kw = {}
        for sub in cls._xml_to_model(e, kw):
            match sub:
                case Element(tag="clone" as t):
                    kw[t] = bool(sub.text.strip())
                case _:
                    raise Sad.from_sub_elem(e, sub)
        return cls(**kw)
