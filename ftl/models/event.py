from abc import ABC
from typing import Any, ClassVar, Iterator, Generic
from xml.etree.ElementTree import Element

from pydantic import Field

from .base import ElementModel, JustAttribs, StringLookup, Tagged, Child, Parent
from ..exceptions import Sad


class Item(StringLookup, JustAttribs, Child, ABC):
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


class Text(Child):
    tag_name: ClassVar[str] = "text"
    text: str = None

    @classmethod
    def from_elem(cls, e: Element):
        kw = e.attrib.copy()
        if e.text and e.text.strip():
            kw["text"] = e.text.strip()
        return cls(**kw)


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


class Environment(JustAttribs, Child):
    tag_name: ClassVar[str] = "environment"
    type_: str = Field(alias="type")


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


class Choice(ElementModel):
    tag_name: ClassVar[str] = "choice"
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
    tag_name: ClassVar[str] = "item"
    """
    This is an element at event/item_modify/item. This defines when an event temporarily
     affects your subsystems.
    """
    type_: str = Field(alias="type")
    min: int = None
    max: int = None


class Status(JustAttribs, Child):
    tag_name: ClassVar[str] = "status"
    target: str
    type_: str = Field(alias="type")
    system: str
    amount: int


class AutoReward(Child):
    tag_name: ClassVar[str] = "autoReward"
    level: str
    text: str

    @classmethod
    def from_elem(cls, e: Element):
        assert cls.tag_name == e.tag
        kw: dict[str, Any] = e.attrib.copy()
        kw["text"] = e.text
        return cls(**kw)


class Boarders(JustAttribs, Child):
    tag_name: ClassVar[str] = "boarders"
    breach: bool = False
    min: int
    max: int
    class_: str = Field(alias="class")


class Quest(Child):
    tag_name: ClassVar[str] = "quest"
    event: str

    @classmethod
    def from_elem(cls, e: Element):
        return cls(event=e.attrib["event"])


class Image(JustAttribs, Child):
    tag_name: ClassVar[str] = "img"
    back: str = None
    planet: str = None


class Upgrade(JustAttribs, Child):
    tag_name: ClassVar[str] = "upgrade"
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
@Augment.attach
@Damage.attach(destination="loot")
@RemoveCrew.attach(destination="loot")
@Remove.attach(destination="loot")
@Drone.attach(destination="loot")
@Weapon.attach(destination="loot")
@Augment.attach(destination="loot")
@CrewMember.attach(destination="loot")
@Environment.attach
class Event(Parent):
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
                case Element(tag="item_modify"):
                    # item_modify seems to be a dumb list, so just using a dumb list
                    kw["item_modify"] = [EventModifyItem.from_elem(i) for i in sub]

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


Choice.update_forward_refs()
