"""Proxy management commands."""

from __future__ import annotations

import typer

from rich.table import Table
from rich import box
from selfbot.proxy import PROXY_FILE, load_proxies, ensure_proxy_file

proxy_app = typer.Typer(help="Manage proxy list")


@proxy_app.command()
def add(
    proxy: str = typer.Argument(..., help="host:port, e.g. 127.0.0.1:1080"),
    proxy_type: str = typer.Option("socks5", "--type", "-t", help="Proxy type: socks5, socks4, http, mtproto"),
) -> None:
    ensure_proxy_file()
    lines = PROXY_FILE.read_text(encoding="utf-8").splitlines()
    # avoid duplicates
    stripped_proxy = proxy.strip()
    entry = f"{proxy_type} {stripped_proxy}"
    if entry not in lines and stripped_proxy not in lines:
        with PROXY_FILE.open("a", encoding="utf-8") as f:
            if lines and lines[-1] != "":
                f.write("\n")
            f.write(entry + "\n")
    typer.echo(f"Added {entry}")


@proxy_app.command()
def list() -> None:
    proxies = load_proxies()
    if not proxies:
        typer.echo("No proxies configured")
        return
    table = Table(title="Proxies", box=box.ROUNDED)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Type")
    table.add_column("Address")
    for idx, p in enumerate(proxies, 1):
        parts = p.split()
        if len(parts) == 2 and parts[0] in {"socks5", "socks4", "http", "mtproto"}:
            ptype, addr = parts[0], parts[1]
        else:
            ptype, addr = "socks5", p
        table.add_row(str(idx), ptype, addr)
    from rich.console import Console
    Console().print(table)


@proxy_app.command()
def delete(
    number: int = typer.Argument(..., help="Line number to remove (use list to see)"),
) -> None:
    ensure_proxy_file()
    lines = PROXY_FILE.read_text(encoding="utf-8").splitlines()
    non_empty_indices = [i for i, line in enumerate(lines) if line.strip() and not line.strip().startswith("#")]
    if number < 1 or number > len(non_empty_indices):
        typer.echo(f"Invalid number: {number} (max {len(non_empty_indices)})")
        raise typer.Exit(1)
    del_idx = non_empty_indices[number - 1]
    del lines[del_idx]
    # clean trailing blank lines
    while lines and lines[-1].strip() == "":
        lines.pop()
    PROXY_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    typer.echo(f"Deleted {number}")


@proxy_app.command()
def clear() -> None:
    ensure_proxy_file()
    PROXY_FILE.write_text("", encoding="utf-8")
    typer.echo("Proxy list cleared")
