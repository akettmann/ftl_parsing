from typing import Any, ClassVar
from xml.etree.ElementTree import Element

from pydantic import Field

from .base import ElementModel, JustAttribs, StringLookup
from ..exceptions import Sad


class Augment(JustAttribs, ElementModel):
    tag_name = "augment"
    name: str


class Text(ElementModel):
    tag_name = "text"
    text: str = None

    @classmethod
    def from_elem(cls, e: Element):
        kw = e.attrib.copy()
        if e.text and e.text.strip():
            kw["text"] = e.text
        return cls(**kw)


class Environment(JustAttribs, ElementModel):
    tag_name = "environment"
    type_: str = Field(alias="type")


class Ship(JustAttribs, ElementModel):
    tag_name = "ship"
    """
    Note that this can be used as a "diff" 
    """
    load: str = None
    hostile: bool = False


class Choice(ElementModel):
    tag_name = "choice"
    hidden: bool = False
    text: Text
    event: "Event"
    choice: "Choice" = None

    @classmethod
    def from_elem(cls, e: Element):
        kw: dict[str, Any] = e.attrib.copy()
        for sub in e:
            match sub:
                case Element(tag=Event.tag_name):
                    kw["event"] = Event.from_elem(sub)
                case Element(tag=Text.tag_name):
                    kw["text"] = Text.from_elem(sub)
                case Element(tag=cls.tag_name):
                    kw["choice"] = cls.from_elem(sub)
                case _:
                    raise Sad.from_elem(sub)
        return cls(**kw)


class EventModifyItem(JustAttribs, ElementModel):
    tag_name = "item"
    """
    This is an element at event/item_modify/item. This defines when an event temporarily
     affects your subsystems.
    """
    type_: str = Field(alias="type")
    min: int = None
    max: int = None


class AutoReward(ElementModel):
    tag_name = "autoReward"
    level: str
    text: str

    @classmethod
    def from_elem(cls, e: Element):
        assert cls.tag_name == e.tag
        kw: dict[str, Any] = e.attrib.copy()
        kw["text"] = e.text
        return cls(**kw)


class Event(ElementModel):
    tag_name: ClassVar[str] = "event"
    unique: bool = False
    name: str = None
    text: Text = None
    distress_beacon: bool = False
    ship: Ship = None
    choices: list[Choice]
    store: bool = False
    auto_reward: AutoReward = None
    item_modify: list[EventModifyItem] = Field(default_factory=list)
    augment: Augment = None

    @classmethod
    def from_elem(cls, e: Element):
        kw: dict[str, Any] = e.attrib.copy()
        kw["choices"] = choices = []
        for sub in e:
            match sub:
                case Element(tag=Choice.tag_name):
                    choices.append(Choice.from_elem(sub))
                case Element(tag="item_modify"):
                    # item_modify seems to be a
                    kw["item_modify"] = [EventModifyItem.from_elem(i) for i in sub]
                case Element(tag=Text.tag_name):
                    kw["text"] = Text.from_elem(sub)
                case Element(tag=Ship.tag_name):
                    kw["ship"] = Ship.from_elem(sub)
                case Element(tag=Environment.tag_name):
                    kw["environment"] = Environment.from_elem(sub)
                case Element(tag="distressBeacon"):
                    kw["distress_beacon"] = True
                case Element(tag="store"):
                    kw["store"] = True
                case Element(tag=AutoReward.tag_name):
                    kw["auto_reward"] = AutoReward.from_elem(sub)
                case Element(tag=Augment.tag_name):
                    kw["augment"] = Augment.from_elem(sub)
                case _:
                    pass
                    # raise Sad.from_elem(sub)
        return cls(**kw)


Choice.update_forward_refs()
