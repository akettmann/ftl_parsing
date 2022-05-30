from typing import Any
from xml.etree.ElementTree import Element

from pydantic import Field

from .base import ElementModel, JustAttribs
from .text import StringLookup
from ..exceptions import Sad


class Drone(JustAttribs, ElementModel):
    tag_name = "drone"
    name: str


class DroneList(ElementModel):
    tag_name = "droneList"
    drones: list[Drone]
    count: int = 0
    load: str = None

    @classmethod
    def from_elem(cls, e: Element) -> "DroneList":
        kw: dict[str, Any] = e.attrib.copy()
        kw["drones"] = [Drone.from_elem(sub) for sub in e]
        return cls(**kw)

    def resolve(self):
        """
        loads the BlueprintList defined by the attribute `load`
        """
        if self.load:
            raise NotImplementedError


class Weapon(JustAttribs, ElementModel):
    tag_name = "weapon"
    name: str


class WeaponList(ElementModel):
    tag_name = "weaponList"
    count: int = 0
    missiles: int = 0
    weapons: list[Weapon]

    @classmethod
    def from_elem(cls, e: Element) -> "WeaponList":
        kw: dict[str, Any] = e.attrib.copy()
        kw["weapons"] = [Weapon.from_elem(sub) for sub in e]
        return cls(**kw)

    def resolve(self):
        """loads any lazy references if they exist"""
        raise NotImplementedError()


class ShipClass(JustAttribs, ElementModel):
    tag_name = "class"
    id_: str = Field(alias="id")

    @classmethod
    def from_elem(cls, e: Element):
        # Special cases! Yay Video game codeeeeeee
        if e.text and e.text.strip().lower() == "kestrel":
            e.attrib["id"] = e.text
        return super().from_elem(e)


class System(JustAttribs, ElementModel):
    tag_name = ("pilot", "doors", "medbay", "oxygen", "shields", "engines", "weapons")
    power: int
    max: int = None
    room: int
    start: bool = True


class SystemList(ElementModel):
    tag_name = "systemList"
    systems: dict[str, System]

    @classmethod
    def from_elem(cls, e: Element):
        return cls(systems={s.tag: System.from_elem(s) for s in e})


class CrewCount(JustAttribs, ElementModel):
    tag_name = "crewCount"
    amount: int
    max: int = None
    class_: str = Field(alias="class")


class Augment(JustAttribs, ElementModel):
    tag_name = "aug"
    name: str


class CloakImage(ElementModel):
    tag_name = "cloakImage"
    text: str

    @classmethod
    def from_elem(cls, e: Element):
        return cls(text=e.text)


class Description(StringLookup, JustAttribs, ElementModel):
    tag_name = "desc"


class Unlock(StringLookup, JustAttribs, ElementModel):
    tag_name = "unlock"


class ShieldImage(JustAttribs, ElementModel):
    tag_name = "shieldImage"


class FloorImage(ElementModel):
    tag_name = "floorImage"
    id_: str = Field(alias="id")

    @classmethod
    def from_elem(cls, e: Element):
        return cls(**{"id": e.text})


class ShipBlueprint(ElementModel):
    tag_name = "shipBlueprint"
    name: str  # attrib
    layout: str  # attrib
    img: str  # attrib
    display_name: str = None
    description: Description = None
    class_: ShipClass = Field(alias="class")
    system_list: SystemList = None
    weapon_list: WeaponList = None
    crew_count: CrewCount = None
    cloak_image: CloakImage = None
    shield_image: ShieldImage = None
    floor_image: FloorImage = None
    augments: list[Augment]
    health: int
    max_power: int = Field(alias="maxPower")
    boarding_ai: str = Field(None, alias="boardingAI")
    min_sector: int = Field(None, alias="minSector")
    max_sector: int = Field(None, alias="maxSector")
    weapon_slots: int = Field(None, alias="weaponSlots")

    @classmethod
    def from_elem(cls, e: Element) -> "ShipBlueprint":
        kw: dict[str, Any] = e.attrib.copy()
        kw["augments"] = augs = []
        for sub in e:
            match sub:
                case Element(tag=ShipClass.tag_name):
                    kw["class"] = ShipClass.from_elem(sub)
                case Element(tag=SystemList.tag_name):
                    kw["system_list"] = SystemList.from_elem(sub)
                case Element(tag=WeaponList.tag_name):
                    kw["weapon_list"] = WeaponList.from_elem(sub)
                case Element(tag=CrewCount.tag_name):
                    kw["crew_count"] = CrewCount.from_elem(sub)
                case Element(tag=CloakImage.tag_name):
                    kw["cloak_image"] = CloakImage.from_elem(sub)
                case Element(tag=DroneList.tag_name):
                    kw["drone_list"] = DroneList.from_elem(sub)
                case Element(tag=Description.tag_name):
                    kw["description"] = Description.from_elem(sub)
                case Element(tag=Unlock.tag_name):
                    kw["unlock"] = Unlock.from_elem(sub)
                case Element(tag=ShieldImage.tag_name):
                    kw["shield_image"] = ShieldImage.from_elem(sub)
                case Element(tag=FloorImage.tag_name):
                    kw["floor_image"] = FloorImage.from_elem(sub)
                case Element(tag=Augment.tag_name):
                    augs.append(Augment.from_elem(sub))
                case Element(tag=tag, attrib={"amount": amt}) if tag in (
                    "health",
                    "maxPower",
                ):
                    kw[tag] = amt
                case Element(tag=tag, text=t) if tag in (
                    "boardingAI",
                    "maxSector",
                    "minSector",
                ):
                    kw[tag] = t
                case Element(tag=tag, text=t) if tag in (
                    "droneSlots",
                    "weaponSlots",
                    "name",
                ):
                    if tag == "name":
                        tag = "display_name"
                    kw[tag] = t
                case _:
                    raise Sad.from_sub_elem(e, sub)
        return cls(**kw)
