from rich.console import RenderableType
from textual.reactive import Reactive
from textual.widget import Widget

from ftl import FTL


class EventWidget(Widget):
    _events = FTL.events
    _event_list = list(_events.values())
    _current = Reactive(_event_list[0])

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self.idx = 0

    def action_inc(self):
        self.idx += 1

    def action_dec(self):
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

    def press(self, i: int):
        choices = self._current.choices
        if not choices and i == 1 and self._current.ship:
            self._current = self._current.ship
        if 0 < i <= len(choices):
            self._current = choices[i - 1].event
            self.refresh()

    async def on_mount(self, event=None):
        # self.inc()
        await self.app.bind("left", "app.main_screen.dec()")
        await self.app.bind("right", "app.main_screen.inc()")
