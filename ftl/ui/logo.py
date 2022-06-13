from pyfiglet import Figlet
from rich.console import RenderableType
from textual.reactive import Reactive
from textual.widget import Widget


class FigletWidget(Widget):
    font: Reactive[str] = Reactive("standard")
    text: Reactive[str] = Reactive("")

    def __init__(
        self, name: str | None = None, text: str = "", font: str = "standard"
    ) -> None:
        super().__init__(name)
        # noinspection PyTypeChecker
        self.text = text
        # noinspection PyTypeChecker
        self.font = font

    def render(self) -> RenderableType:
        fig = self.font_figlet.renderText(self.text)
        return fig

    @property
    def font_figlet(self) -> Figlet:
        return Figlet(font=self.font)
