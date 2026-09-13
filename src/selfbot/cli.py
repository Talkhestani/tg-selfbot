"""CLI entry point using Typer."""
from __future__ import annotations

import typer

from selfbot import __version__ as pkg_version

app = typer.Typer(
    name="selfbot",
    help="Telegram Self-Bot",
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@app.command()
def run() -> None:
    """Run the bot."""
    from selfbot.app import main
    main()


@app.command()
def version() -> None:
    typer.echo(f"selfbot {pkg_version}")
