"""

A Textual app to create a fully working FTL Wiki

"""
from enum import Enum

from textual.app import App
from textual.layout import Layout
from textual.reactive import Reactive
from textual.views import GridView
from textual.widgets import Button, ButtonPressed, Placeholder

from ftl.ui.beacon import EventWidget
from ftl.ui.logo import FigletWidget


class Categories(Enum):
    events = "Events"
    quests = "Quests"
    ships = "Ships"
    races = "Races"
    weapons = "Weapons"
    drones = "Drones"

    @property
    def kls(self):
        match self:
            case Categories.events:
                return EventWidget
            case _:
                return Placeholder

    @property
    def button(self):
        return Button(self.value, name=self.value)


def _make_area_string(c1, c2, c3, c4) -> str:
    return f"col{c1}-start|col{c2}-end,row{c3}-start|row{c4}-end"


class CategoryButtons(GridView):
    def __init__(self, layout: Layout = None, name: str | None = None) -> None:
        super().__init__(layout, name)
        self.buttons = None

    # noinspection PyMethodOverriding
    async def on_mount(self):
        self.grid.set_gap(1, 1)
        self.grid.set_gutter(1)
        self.grid.add_column("col")
        self.grid.add_row("row", repeat=len(Categories))
        self.buttons = {c: c.button for c in Categories}
        self.grid.place(*self.buttons.values())


# noinspection PyAttributeOutsideInit
class FTLApp(App):
    category = Reactive(Categories.events)
    """The FTL Application"""

    async def on_load(self):
        await self.bind("q", "quit")

    async def on_mount(self) -> None:
        """Mount the ftl widget."""
        # Set basic grid settings
        self.grid = await self.view.dock_grid()
        self.grid.set_gap(2, 1)
        self.grid.set_gutter(1)
        self.grid.set_align("center", "center")

        # Create rows / columns / areas
        self.grid.add_column("header", fraction=1)
        self.grid.add_column("data", fraction=8)
        self.grid.add_row("header", fraction=2)

        self.grid.add_row("data", fraction=7)
        self.grid.add_areas(
            logo="header,header",
            left_bar="header,data",
            main_screen="data,data",
            top_bar="data,header",
        )
        self.logo = FigletWidget("logo", "FTL\nWiki")
        self.top_bar = Placeholder(name="Top Bar")
        self.grid.place(
            logo=self.logo,
            top_bar=self.top_bar,
            left_bar=CategoryButtons(),
        )
        self.cat_widgets = await self.place_category_widgets()
        await self.bind("q", "quit")

    async def handle_button_pressed(self, message: ButtonPressed) -> None:
        match message:
            case ButtonPressed(sender=Button(name=name, parent=CategoryButtons())):
                self.category = Categories(name)
            case _:
                raise RuntimeError("WHY DID YOU DO THIS?!")

    async def place_category_widgets(self):
        cat_widgets = {}
        for cat in Categories:
            cat_widgets[cat] = kls = cat.kls(name=cat.value)
            kls.visible = False
            self.grid.place(main_screen=kls)
        return cat_widgets

    async def watch_category(self, value: Categories):

        for k, v in self.cat_widgets.items():
            if k == value:
                v.visible = True
            else:
                v.visible = False
