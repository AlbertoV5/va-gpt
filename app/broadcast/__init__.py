from rich.markdown import Markdown
from rich.console import Console
from rich.syntax import Syntax
from rich.status import Status
from rich.align import Align
from rich.panel import Panel
from rich.text import Text
from rich import print

from datetime import datetime
from typing import Generator
from re import findall, sub
from time import sleep

from app.chat.context import Context
from app.audio.capture import Capture

# from functools import wraps, partial
# from asyncio import sleep
# import asyncio


# def to_async(func):
#     @wraps(func)  # Makes sure that function is returned for e.g. func.__name__ etc.
#     async def run(*args, loop=None, executor=None, **kwargs):
#         if loop is None:
#             loop = asyncio.get_event_loop()  # Make event loop of nothing exists
#         pfunc = partial(func, *args, **kwargs)  # Return function with variables (event) filled in
#         return await loop.run_in_executor(executor, pfunc)

#     return run


class Broadcast:
    def __init__(self) -> None:
        self.default_lexer = "python"
        self.theme = "github-dark"
        self.console = Console()

    def load(self, context: Context) -> None:
        self.context = context

    @property
    def width(self):
        return self.console.size.width

    def to_markdown(self, text: str):
        return Markdown(
            text,
            code_theme=self.theme,
            inline_code_lexer=self.default_lexer,
        )

    def clear(self):
        """Clear line text."""
        print(f"{' ' * self.width}", end="\r")

    def mon(self, peak: float, rms: float, time: float, gate: bool):
        """Broadcast audio monitoring information."""
        print(
            f" {(peak):.0f} db {(rms):.0f} rms {time:.0f} s "
            # f" :studio_microphone: {(peak):.0f} db {(rms):.0f} rms {time:.0f} s "
            f"[bold red]{'*'*gate}[/bold red]{' '*5}",
            end="\r",
        )

    def loading(self, text: str):
        """Generator for displaying loading spinner."""
        loading = Status(text)
        loading.start()
        yield True
        loading.stop()

    def startup(self, loading: str, title: str = "GPT-VA"):
        self.status = Status(loading)
        self.status.start()
        message = yield "[bold cyan]{bold}:[/bold cyan] {text}"
        self.status.stop()
        print(
            Panel(
                message,
                title=title,
                subtitle=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                subtitle_align="right",
            )
        )
        yield True

    def error(self, text: str):
        print(f"[bold red]Error:[/bold red] {text}")

    def capture(self, capture: Capture, text: str):
        """Broadcast audio capture information."""
        print(Text(f"{capture}: {text}"))

    def command(self, command: str, text: str):
        """Broadcast command information and result."""
        print(f"[bold white]Command[/bold white]: {command}")
        print(text)

    def sleep(self, text: str):
        """Broadcast sleep command."""
        print(f"[bold gray]Sleep[/bold gray]: {text}")

    # @to_async
    def user(self, text: str):
        """Broadcast user prompt."""
        print(f":bust_in_silhouette: [bold blue]{self.context.user.name}[/bold blue]")
        print(Text(text))
        # for t in Text(text):
        # print(t, end="")
        # sleep(0.01)
        # print("\n")

    def assistant(self, stream: Generator[str, None, None]):
        """Broadcast assistant response. Yields before broadcasting."""
        LEXER_MATCH = r"```(.+?)\n"
        LEXER_REPLACE = r"```.*?\n"
        THEME = self.theme
        lexer = [self.default_lexer]
        # header
        print(f":nerd_face: [bold green]{self.context.assistant.name}[/bold green]")
        # text
        for block in stream:
            # print code without yielding it
            if "```" in block:
                # detect code language and print line by line
                lexer = findall(LEXER_MATCH, block) or lexer
                for t in sub(LEXER_REPLACE, " \n", block).split("\n")[:-1]:
                    print(
                        Syntax(t, lexer=lexer[0], theme=THEME),
                        end="",
                    )
                    sleep(0.5)
                print("")
                continue
            yield block
            for t in Text(block, justify="full"):
                print(t, end="")
                sleep(0.05)
        print("\n")
