from typing import Any, ClassVar
from xml.etree.ElementTree import Element

from pydantic import Field

from .base import Child, ElementModel, JustAttribs, Parent
from .loot import Item, Augment, Weapon, Drone, Remove, CrewMember, Damage, RemoveCrew
from .text import Text
from ..exceptions import Sad


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


class Choice(Child):
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


@Choice.attach(destination="choices")
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
    loot: list[Item] = Field(default_factory=list)
    modify_pursuit: int = None
    boarders: Boarders = None
    statuses: list[Status] = Field(default_factory=list)
    quest: Quest = None
    image: Image = None
    unlock_ship: int = Field(None, alias="unlockShip")

    @classmethod
    def from_elem(cls, e: Element):
        kw: dict[str, Any] = e.attrib.copy()
        kw["choices"] = []
        kw["loot"] = []
        kw["statuses"] = []
        for sub in cls._xml_to_model(e, kw):
            match sub:
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
