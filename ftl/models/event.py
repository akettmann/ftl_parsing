import re
from typing import Any, ClassVar
from xml.etree.ElementTree import Element

from pydantic import Field
from rich.table import Table
from rich.text import Text as RText

from .base import Child, ElementModel, JustAttribs, Parent
from .loot import Augment, CrewMember, Damage, Drone, Item, Remove, RemoveCrew, Weapon
from .ship import Fleet, Ship
from .text import Text
from ..exceptions import Sad


class Environment(JustAttribs, Child):
    tag_name: ClassVar[str] = "environment"
    type_: str = Field(alias="type")
    target: str = None


class Choice(Child):
    _PAREN_RE = re.compile(r"\((?P<req>[\w ]+)\)(?P<text>.*$)")
    tag_name: ClassVar[str] = "choice"
    hidden: bool = None
    text: Text
    event: "Event"
    choice: "Choice" = None
    req: str = None

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

    def render(self) -> RText:
        r = self.text.render()
        if not isinstance(r, str):
            # This is not just a string, return it as is
            return r
        if self.hidden is True and self.req is None:
            # TODO: Support looking up an event list, looking at the itemmodify tag
            #  and seeing what one of them costs and hope they all cost that?
            return RText(r)

        m = self._PAREN_RE.fullmatch(r)
        if m is None:
            return RText.assemble(f"👻 {r}")
        return RText.assemble((m.group("req"), "blue1"), " 👻", m.group("text"))

    def __rich__(self):
        return self.render()


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
    name: str = ""
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
    environment: Environment = None
    augment: Augment = None
    status: Status = None
    fleet: Fleet = None
    img: Image = None
    upgrade: Upgrade = None
    load: str = None  # TODO: Need to implement a draw method or something?
    min: int = None
    max: int = None

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

    def __rich__(self):
        event_table = Table(self.name, expand=False, min_width=80)
        event_table.add_row(self.text)
        event_table.add_row(self._modifier_row())
        event_table.add_row()
        for idx, choice in enumerate(self.choices):
            t = RText(f"{idx + 1}. ")
            t.append(choice.render())
            event_table.add_row(t)
        if len(self.choices) == 0:
            if self.ship:
                event_table.add_row("Fight Ship!!!")
            else:
                event_table.add_row("1. Continue...")

        return event_table

    def _modifier_row(self):
        t = RText()
        if self.distress_beacon:
            t.append("Distress Beacon", "yellow")
        if self.ship:
            t.append("Ship Detected", "red")
        return t


Choice.update_forward_refs()
