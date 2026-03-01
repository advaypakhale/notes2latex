"""Typer CLI entry point."""

import asyncio
import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from agent.config import AgentConfig
from agent.graph import run_pipeline
from core.config import Settings

app = typer.Typer(
    name="notes2latex",
    help="Convert handwritten math notes to compiled LaTeX.",
    add_completion=False,
)
console = Console()


@app.command()
def convert(
    files: Annotated[
        list[Path],
        typer.Argument(help="Input PDF or image files", exists=True),
    ],
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="LLM model name (e.g. openai/gpt-4o)"),
    ] = None,
    output_dir: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output directory"),
    ] = None,
    max_retries: Annotated[
        Optional[int],
        typer.Option("--max-retries", help="Max fix attempts per page"),
    ] = None,
    dpi: Annotated[
        Optional[int],
        typer.Option("--dpi", help="DPI for PDF rendering"),
    ] = None,
) -> None:
    """Convert handwritten math notes (images/PDFs) to compiled LaTeX."""
    overrides = {
        k: v
        for k, v in {
            "model": model,
            "output_dir": output_dir,
            "max_retries": max_retries,
            "dpi": dpi,
        }.items()
        if v is not None
    }

    settings = Settings(**overrides)
    config = AgentConfig.from_settings(settings)

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_time=False, show_path=False)],
    )

    console.print(
        f"[bold blue]Processing {len(files)} file(s)[/] with model [cyan]{config.model}[/]"
    )

    result = asyncio.run(run_pipeline(files, config))

    if result.get("output_tex_path"):
        console.print(f"[bold green]TeX:[/] {result['output_tex_path']}")

    if result.get("output_pdf_path"):
        console.print(f"[bold green]PDF:[/] {result['output_pdf_path']}")
    else:
        console.print(
            "[bold yellow]Warning:[/] Compilation failed. "
            "LaTeX source was saved but no PDF was produced."
        )


@app.command()
def serve(
    host: Annotated[
        str,
        typer.Option("--host", "-h", help="Bind host"),
    ] = "0.0.0.0",
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Bind port"),
    ] = 8000,
) -> None:
    """Start the web UI server."""
    import uvicorn

    console.print(f"[bold blue]Starting server[/] on [cyan]{host}:{port}[/]")
    uvicorn.run("app:app", host=host, port=port)


@app.command()
def version() -> None:
    """Show version."""
    from importlib.metadata import version as get_version

    console.print(f"notes2latex {get_version('notes2latex')}")
