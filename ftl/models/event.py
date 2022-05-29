from abc import ABC
from typing import Any, ClassVar, Iterator
from xml.etree.ElementTree import Element

from pydantic import Field

from .base import ElementModel, JustAttribs, StringLookup
from ..exceptions import Sad


class Item(StringLookup, JustAttribs, ElementModel):
    """This holds the name of a loot table that an item will come from as a result of an
    event"""


class Augment(Item):
    tag_name = "augment"


class Weapon(Item):
    tag_name = "weapon"


class Drone(Item):
    tag_name = "drone"


class Remove(Item):
    tag_name = "remove"
    """
    This says what you will lose when this event happens, kind of Anti-Loot
    """


class RemoveCrew(Remove):
    tag_name = "removeCrew"
    pass


class CrewMember(Item):
    """People are things too apparently"""

    tag_name = "crewMember"
    amount: int
    class_: str = Field(None, alias="class")


class Damage(Remove):
    tag_name = "damage"


@Damage.attach
@RemoveCrew.attach
@Remove.attach
@Drone.attach
@Weapon.attach
@Augment.attach
@CrewMember.attach
class EventLoot(ElementModel, ABC):
    """Using this class to track, not to actually create"""

    pass


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


class Fleet(ElementModel):
    tag_name = "fleet"
    text: str

    @classmethod
    def from_elem(cls, e: Element):
        return cls(text=e.text)


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


class Status(JustAttribs, ElementModel):
    tag_name = "status"
    target: str
    type_: str = Field(alias="type")
    system: str
    amount: int


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


class Boarders(JustAttribs, ElementModel):
    tag_name = "boarders"
    breach: bool = False
    min: int
    max: int
    class_: str = Field(alias="class")


class Quest(ElementModel):
    tag_name = "quest"
    event: str

    @classmethod
    def from_elem(cls, e: Element):
        return cls(event=e.attrib["event"])


class Image(JustAttribs, ElementModel):
    tag_name = "img"
    back: str = None
    planet: str = None


class Upgrade(JustAttribs, ElementModel):
    tag_name = "upgrade"
    amount: int
    system: str


@Upgrade.attach
@Image.attach
@Quest.attach
@AutoReward.attach
@Boarders.attach
@Ship.attach
@Text.attach
@Fleet.attach
@Status.attach
class Event(ElementModel):
    tag_name: ClassVar[str] = "event"
    name: str = None
    text: Text = None
    ship: Ship = None
    choices: list[Choice]
    distress_beacon: bool = False
    repair: bool = False
    reveal_map: bool = False
    secret_sector: bool = Field(
        False,
        description="Indicates that this event triggers the crystal homeworlds sector",
    )
    store: bool = False
    unique: bool = False
    auto_reward: AutoReward = None
    item_modify: list[EventModifyItem] = Field(default_factory=list)
    loot: list[Item | CrewMember | Remove] = Field(default_factory=list)
    modify_pursuit: int = None
    boarders: Boarders = None
    statuses: list[Status] = Field(default_factory=list)
    quest: Quest = None
    image: Image = None
    unlock_ship: int = Field(None, alias="unlockShip")

    @classmethod
    def from_elem(cls, e: Element):
        kw: dict[str, Any] = e.attrib.copy()
        kw["choices"] = choices = []
        kw["loot"] = loot = []
        kw["statuses"] = statuses = []
        for sub in cls._xml_to_model(e, kw):
            match sub:
                case Element(tag=Choice.tag_name):
                    choices.append(Choice.from_elem(sub))
                case Element(tag=tag) if tag in EventLoot._tag_set:
                    kls = EventLoot._dependents[tag]
                    loot.append(kls.from_elem(sub))
                case Element(tag="item_modify"):
                    # item_modify seems to be a dumb list, so just using a dumb list
                    kw["item_modify"] = [EventModifyItem.from_elem(i) for i in sub]
                case Element(tag=Environment.tag_name):
                    kw["environment"] = Environment.from_elem(sub)
                # booleans
                case Element(tag=t) if t in {
                    "distressBeacon",
                    "store",
                    "secretSector",
                    "reveal_map",
                    "repair",
                }:
                    kw[t] = True
                case Element(tag="modifyPursuit", attrib={"amount": a}):
                    kw["modify_pursuit"] = int(a)
                case Element(tag="unlockShip", attrib={"id": num}):
                    kw["unlockShip"] = int(num)
                case _:
                    raise Sad.from_sub_elem(e, sub)

        return cls(**kw)

    @classmethod
    def _xml_to_model(cls, e: Element, kw: dict[str, Any]) -> Iterator[Element]:
        """This iterates over the sub elements and yields the ones it doesn't handle"""
        for sub in e:
            match sub:
                case Element(tag=tag) if tag in cls._tag_set:
                    kls: ElementModel = cls._dependents[tag]
                    kw[kls.py_tag_name()] = kls.from_elem(sub)
                case _:
                    yield sub


Choice.update_forward_refs()
