from enum import auto, Enum
from typing import ClassVar, Any
from xml.etree.ElementTree import Element

from pydantic import Field

from .base import Parent, Child
from .ftl_list import BaseList
from .text import Text
from ..exceptions import Sad


class Image(Text):
    tag_name: ClassVar[str] = "image"


class IconImage(Image):
    tag_name: ClassVar[str] = "iconImage"


class Explosion(Image):
    tag_name: ClassVar[str] = "explosion"


class Sound(Text):
    tag_name: ClassVar[str] = "sound"


class WeaponArt(Text):
    tag_name: ClassVar[str] = "weaponArt"


@Sound.attach
class SoundList(BaseList, Child):
    tag_name: ClassVar[str] = "soundList"


@Explosion.attach
@IconImage.attach
@WeaponArt.attach
@Image.attach
@Text.attach(tag_name="title", destination="title")
@Text.attach(tag_name="short", destination="short")
@Text.attach(tag_name="desc", destination="desc")
@Text.attach(tag_name="tooltip", destination="tooltip")
@Text.attach(tag_name="type", destination="type")
@Text.attach(tag_name="tip", destination="tip")
@SoundList.attach(tag_name="launchSounds", destination="launchSounds")
@SoundList.attach(tag_name="hitShipSounds", destination="hitShipSounds")
@SoundList.attach(tag_name="hitShieldSounds", destination="hitShieldSounds")
@SoundList.attach(tag_name="missSounds", destination="missSounds")
class WeaponBlueprint(Parent):
    _number_text_fields = {
        "bp",
        "breachChance",
        "chargeLevels",
        "cooldown",
        "cost",
        "damage",
        "drone_targetable",
        "fireChance",
        "hullBust",
        "ion",
        "length",
        "lockdown",
        "locked",
        "missiles",
        "persDamage",
        "power",
        "radius",
        "rarity",
        "shots",
        "sp",
        "speed",
        "spin",
        "stun",
        "stunChance",
        "sysDamage",
    }

    tag_name: ClassVar[str] = "weaponBlueprint"
    name: str
    title: Text
    desc: Text = None
    short: Text = None
    tooltip: Text = None
    image: Image
    weapon_art: WeaponArt = None
    explosion: Explosion = None
    type_: Text
    tip: Text = None

    locked: bool = False
    cost: int = 0
    lockdown: int = 0
    cooldown: int = 0

    hull_bust: int = 0
    length: int = 0
    damage: int = 0
    radius: int = 0
    sys_damage: int = 0

    power: int = 0
    color: int = 0
    sp: int = 0
    icon_image: IconImage = None
    breach_chance: int = 0
    boost: int = 0
    ion: int = 0

    fire_chance: int = 0

    shots: int = 0
    spin: int = 0

    bp: int = 0
    missiles: int = 0
    projectiles: int = 0
    charge_levels: int = 0
    speed: int = 0

    stun: int = 0

    flavor_type: int = 0

    drone_targetable: bool = False
    stun_chance: int = 0
    rarity: int = 0
    crew_damage: int = Field(0, alias="persDamage")
    hit_ship_sounds: list[Sound]
    hit_shield_sounds: list[Sound]
    miss_sounds: list[Sound]
    launch_sounds: list[Sound]

    @classmethod
    def from_elem(cls, e: Element):
        kw: dict[str, Any] = e.attrib.copy()
        kw["launchSounds"] = []
        kw["hitShipSounds"] = []
        kw["hitShieldSounds"] = []
        kw["missSounds"] = []

        for sub in cls._xml_to_model(e, kw):
            match sub:
                case Element(
                    tag=tag
                ) if tag in cls._number_text_fields and sub.text and sub.text.isnumeric():
                    kw[tag] = int(sub.text)
                case _:
                    pass
                    # raise Sad.from_sub_elem(e, sub)
        return cls(**kw)
