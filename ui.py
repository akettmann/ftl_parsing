from typing import Type

from rich.console import RenderableType
from textual.driver import Driver
from textual.reactive import Reactive
from textual.widget import Widget


from ftl import FTL
from textual.app import App


class EventWidget(Widget):
    _events = FTL.events
    _event_list = list(_events.values())
    _current = Reactive(_event_list[0])

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self.idx = 0

    def inc(self):
        self.idx += 1

    def dec(self):
        self.idx -= 1

    @property
    def idx(self):
        return self._idx

    @idx.setter
    def idx(self, value: int):
        self._idx = value
        self._current = self._event_list[value]

    def render(self) -> RenderableType:
        return self._current


class EventApp(App):
    def __init__(
        self,
        screen: bool = True,
        driver_class: Type[Driver] | None = None,
        log: str = "",
        log_verbosity: int = 1,
        title: str = "Textual Application",
    ):
        super().__init__(screen, driver_class, log, log_verbosity, title)
        self._event_widget = EventWidget()

    async def on_mount(self) -> None:
        await self.view.dock(self._event_widget, edge="top")
        await self.bind("z", "inc()")
        await self.bind("x", "dec()")
        await self.bind("q", "quit")

    def action_inc(self):
        self._event_widget.inc()

    def action_dec(self):
        self._event_widget.dec()


EventApp.run("textual.log")
