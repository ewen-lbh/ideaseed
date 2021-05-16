from shutil import get_terminal_size
from typing import Iterable, NamedTuple, Optional

import rich.box
import rich.markup
from rich import print
from rich.align import Align
from rich.box import Box
from rich.console import Console, ConsoleOptions, RenderResult
from rich.markdown import CodeBlock, Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from ideaseed.utils import readable_on

ABOUT_SCREEN = """


                ██████████  ██  ██
                ██      ██  ██  ██
                ██████████  ██  ██
                ██      ██  ██  ██
                ██████████████████
                ██      ██      ██
                ██████████      ██
                ██      ██      ██
                ██████████      ██

            ideaseed v{version}
            by Ewen Le Bihan
            more at https://ewen.works

                ~ thx to these ppl ~

https://github.com/kiwiz
    This madman reverse-engineered Google Keep's
    internal REST API so that anyone could
    use it with ease.

https://github.com/PyGithub
    This one of the cleanest libs I've ever used.
    Like `requests`-level cleanliness.

https://github.com/docopt
    Designing CLIs with this is a fucking breeze.
    I can almost copy-paste documentation into
    a docstring and call it a day, it's crazy.
"""


# Remove ugly frames around markdown code blocks
# see https://github.com/willmcgugan/rich/issues/264
class FramelessCodeBlock(CodeBlock):
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        code = str(self.text).rstrip()
        syntax = Padding(Syntax(code, self.lexer_name, theme=self.theme), pad=(1, 4))
        yield syntax


Markdown.elements["code_block"] = FramelessCodeBlock


class Label(NamedTuple):
    name: str
    color: str = "default"
    url: Optional[str] = None

    def __str__(self) -> str:
        s = f"[{readable_on(self.color)} on #{self.color}]{self.name}[/]"
        if self.url:
            s = f"[link={self.url}]{s}[/link]"
        return s


def href(s: str, url: str) -> str:
    """
    Turns `s` into a console link pointing to `url`, escaping `s` from rich markup
    """
    return f"[link={url}]{rich.markup.escape(s)}[/link]"


def make_card(
    title: Optional[str],
    right_of_title: str,
    description: str,
    labels: Iterable[Label],
    card_title: str,
    card_style: str = "default",
) -> Panel:
    title = title or ""  # no silly 'None' as title
    header = Table.grid(expand=True)
    header.add_column()
    header.add_column(justify="right")
    header.add_row(
        f"[bold]{rich.markup.escape(title)}", f"[bold blue]{right_of_title}",
    )

    card = Table.grid(padding=1, expand=True)
    card.add_column()
    card.add_row(header)
    card.add_row(Markdown(description))

    if labels:
        label_row = Table.grid(expand=True)
        label_row.add_column(justify="right")
        label_row.add_row(", ".join(map(str, labels)))
        card.add_row(label_row)

    return Panel(
        card,
        title=card_title,
        style=card_style,
        box=rich.box.ROUNDED if "on " not in card_style else Box("    \n" * 8),
    )


def make_table(
    milestone: Optional[str] = None,
    assignees: Optional[Iterable[str]] = None,
    project: Optional[str] = None,
    project_column: Optional[str] = None,
    url: Optional[str] = None,
    local_copy: Optional[str] = None,
) -> Table:
    assignees = assignees or []
    listing = Table.grid(expand=True, padding=0)
    listing.add_column()
    listing.add_column(justify="right")
    if project:
        listing.add_row(
            "Card in", f"[bold blue]{project}[/] [bold dim]>[/] [blue]{project_column}",
        )
    if milestone:
        listing.add_row("Milestone'd to", f"[bold blue]{milestone}[/]")
    if list(assignees):
        listing.add_row(
            "Assigned to",
            ", ".join(f"[bold dim]@[/][bold blue]{name}[/]" for name in assignees),
        )

    if url:
        listing.add_row("Available at", f"[blue link {url}]{rich.markup.escape(url)}")

    if local_copy:
        listing.add_row("Local copy saved to", f"[blue]{local_copy}")

    return listing

def get_console() -> Console:
    return Console(width=min(get_terminal_size().columns, 75))

def show(
    title: str,
    right_of_title: str,
    description: str,
    labels: Iterable[Label],
    card_title: str,
    card_style: str = "default",
    milestone: Optional[str] = None,
    assignees: Optional[Iterable[str]] = None,
    project: Optional[str] = None,
    project_column: Optional[str] = None,
    url: Optional[str] = None,
):
    c = get_console()
    c.print(
        make_card(
            title=title,
            right_of_title=right_of_title,
            description=description,
            labels=labels,
            card_title=card_title,
            card_style=card_style,
        )
    )
    c.print()
    c.print(
        make_table(
            milestone=milestone,
            assignees=assignees,
            project=project,
            project_column=project_column,
            url=url,
        )
    )


def dry_run_banner() -> Panel:
    width = min(get_terminal_size().columns, 75)
    return Panel(
        Align(
            """\
You are in [bold blue]dry-run mode[/].
Issues and cards will not be created.

Creation of objects from --create-missing will still occur
[dim](e.g. missing labels will be created if you answer 'yes')[/]\
""",
            "center",
            width=width,
        ),
        title="--dry-run was passed",
        width=width,
        style="black on yellow",
        box=Box("    \n" * 8),
    )


def show_dry_run_banner(dry_run: bool, **_) -> None:
    if dry_run:
        print()
        print(dry_run_banner())
        print()
