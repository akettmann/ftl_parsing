from pathlib import Path
from typing import Any, ClassVar, Optional
from xml.etree.ElementTree import Element

from pydantic import conint, Field

from ..exceptions import Sad
from .base import ElementModel, JustAttribs, StringLookup


class Track(ElementModel):
    # noinspection Pydantic
    tag_name: ClassVar[str] = "track"
    __root__: str

    @classmethod
    def from_elem(cls, e: Element) -> "Track":
        return cls(__root__=e.text)

    def get_file(self) -> Path:
        # TODO
        raise NotImplementedError()


class Name(JustAttribs, StringLookup, ElementModel):
    tag_name = "name"
    short: str


class SectorEvent(JustAttribs, ElementModel):
    tag_name = "event"
    name: str
    min: conint(ge=0)
    max: conint(ge=0)


class StartEvent(ElementModel):
    tag_name = "startEvent"
    name: str

    @classmethod
    def from_elem(cls, e: Element):
        assert e.tag == cls.tag_name
        return cls(name=e.text)


class Rarity(JustAttribs, ElementModel):
    tag_name = "rarity"
    name: str
    rarity: int


class SectorDescription(ElementModel):
    tag_name = "sectorDescription"
    # From attribs
    name: str
    min_sector: int = Field(alias="minSector")
    unique: bool
    # From subelements
    name_list: list[Name]
    event_list: list[SectorEvent]
    start_event: Optional[StartEvent]
    rarity_list: Optional[list[Rarity]]
    track_list: Optional[list[Track]]

    @classmethod
    def from_elem(cls, e: Element) -> "SectorDescription":
        kw: dict[str, Any] = e.attrib.copy()
        kw["event_list"] = event_list = []
        for sub in e:
            match sub:
                # `name_list`, `track_list`, `rarity_list` are from a sub element
                # that has child subelements `event_list` is made up of separate
                # <event/> tags, so we build it as we go
                case Element(tag="nameList"):  # sub.tag == "nameList"
                    kw["name_list"] = [Name.from_elem(i) for i in sub]
                case Element(tag="trackList"):  # sub.tag == "trackList"
                    kw["track_list"] = [Track.from_elem(i) for i in sub]
                case Element(tag="rarityList"):  # sub.tag == "rarityList"
                    kw["rarity_list"] = [Rarity.from_elem(i) for i in sub]
                case Element(tag="event"):
                    event_list.append(SectorEvent.from_elem(sub))
                case Element(tag="startEvent"):
                    kw["start_event"] = StartEvent.from_elem(sub)
                case _:
                    raise Sad.from_elem(sub)
        return cls(**kw)


class Sector(StringLookup, ElementModel):
    tag_name = "sector"

    @classmethod
    def from_elem(cls, e: Element):
        assert e.tag == cls.tag_name
        return cls(id_=e.text)

    def __str__(self):
        print("#TODO: Need to get the SectorDescription")


class SectorType(ElementModel):
    tag_name = "sectorType"
    sectors: list[Sector]
    name: str

    @classmethod
    def from_elem(cls, e: Element):
        assert e.tag == cls.tag_name
        return cls(
            name=e.attrib.get("name"),
            sectors=[Sector.from_elem(sub) for sub in e],
        )
