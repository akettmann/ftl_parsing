from typing import Type
from xml.etree.ElementTree import Element

from .base import ElementModel, M
from .event import Event
from .sector import SectorDescription, SectorType
from .blueprints import ShipBlueprint
from .text import TextList
from ..data import RAW_DATA, STRING_DATA

__all__ = "FTL"


def _make_element_dict(return_class: Type[M], *elements: Element) -> dict[str, M]:
    out = {}
    for sub in elements:
        model = return_class.from_elem(sub)
        out[model.name] = model
    return out


class _FTL(ElementModel):
    tag_name = "FTL"
    sector_descriptions: dict[str, SectorDescription]
    sector_types: dict[str, SectorType]
    events: dict[str, Event]
    ship_blueprints: dict[str, ShipBlueprint]
    text_lists: dict[str, TextList]
    _string_lookup: dict[str:str]

    @classmethod
    def from_elem(cls, e: Element):
        kwargs = {
            "_string_lookup": STRING_DATA,
            "sector_descriptions": _make_element_dict(
                SectorDescription, *e.findall(SectorDescription.tag_name)
            ),
            "sector_types": _make_element_dict(
                SectorType, *e.findall(SectorType.tag_name)
            ),
            # recursively finds events where it has an attribute `name` defined
            "events": _make_element_dict(Event, *e.findall("./event[@name]")),
            "ship_blueprints": _make_element_dict(
                ShipBlueprint, *e.iter("shipBlueprint")
            ),
            "text_lists": _make_element_dict(TextList, *e.iter("textList")),
        }
        return cls(**kwargs)


FTL = _FTL.from_elem(RAW_DATA)
