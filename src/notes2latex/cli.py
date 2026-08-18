"""Typer CLI entry point."""

import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler

from notes2latex import __version__
from notes2latex.agent.config import RunConfig
from notes2latex.agent.graph import run_pipeline
from notes2latex.core.config import get_settings
from notes2latex.db.migrate import MigrationError, upgrade_to_head

app = typer.Typer(
    name="notes2latex",
    help="Convert handwritten math notes to compiled LaTeX.",
    add_completion=False,
)
console = Console()
# Errors carry file paths, which markup, highlighting and word wrapping all mangle.
err_console = Console(stderr=True, markup=False, highlight=False, soft_wrap=True)


@app.command()
def convert(
    files: Annotated[
        list[Path],
        typer.Argument(help="Input PDF or image files", exists=True),
    ],
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="LLM model name (e.g. openai/gpt-4o)"),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output directory"),
    ] = None,
    max_retries: Annotated[
        int | None,
        typer.Option("--max-retries", help="Max fix attempts per page"),
    ] = None,
    dpi: Annotated[
        int | None,
        typer.Option("--dpi", help="DPI for PDF rendering"),
    ] = None,
) -> None:
    """Convert handwritten math notes (images/PDFs) to compiled LaTeX."""
    overrides = {
        "model": model,
        "output_dir": output_dir,
        "max_retries": max_retries,
        "dpi": dpi,
    }
    config = RunConfig.from_settings(
        get_settings(), **{k: v for k, v in overrides.items() if v is not None}
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_time=False, show_path=False)],
    )

    console.print(
        f"[bold blue]Processing {len(files)} file(s)[/] with model [cyan]{config.model}[/]"
    )

    result = asyncio.run(run_pipeline(files, config))

    console.print(f"[bold green]TeX:[/] {config.outputs.tex}")
    if result.has_pdf:
        console.print(f"[bold green]PDF:[/] {config.outputs.pdf}")
    else:
        console.print(
            "[bold yellow]Warning:[/] Compilation failed. "
            "LaTeX source was saved but no PDF was produced."
        )


@app.command()
def serve(
    # Bound on every interface so the server is reachable from outside its container.
    host: Annotated[str, typer.Option("--host", "-h", help="Bind host")] = "0.0.0.0",  # noqa: S104
    port: Annotated[int, typer.Option("--port", "-p", help="Bind port")] = 8000,
) -> None:
    """Start the web UI server."""
    # Deferred: uvicorn costs a quarter of a second to import, and no other command needs it.
    import uvicorn  # noqa: PLC0415

    # Ahead of uvicorn so a database that cannot be upgraded is reported on its own.
    # Startup migrates too, which covers uvicorn being run directly.
    try:
        asyncio.run(upgrade_to_head())
    except MigrationError as exc:
        err_console.print(str(exc), style="bold red")
        raise typer.Exit(1) from None

    console.print(f"[bold blue]Starting server[/] on [cyan]{host}:{port}[/]")
    uvicorn.run("notes2latex.main:app", host=host, port=port)


@app.command()
def version() -> None:
    """Show version."""
    console.print(f"notes2latex {__version__}")
