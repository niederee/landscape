"""CLI commands for deterministic landscape project workflows."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from landscape_planner.analysis.validation import count_entities, validate_project
from landscape_planner.estimating.quantities import (
    existing_condition_quantities,
    format_quantity,
    summarize_quantities,
)
from landscape_planner.io.yaml_loader import ProjectLoadError, load_project
from landscape_planner.rendering.svg import render_existing_conditions_svg

app = typer.Typer(help="Deterministic residential landscape planning tools.")
console = Console()


@app.command()
def validate(project_path: Path) -> None:
    """Validate a landscape project directory or YAML file."""

    project = _load_or_exit(project_path)
    result = validate_project(project)

    if result.ok:
        console.print("[bold green]Validation successful.[/bold green]")
    else:
        console.print("[bold red]Validation failed.[/bold red]")

    table = Table(title="Entities")
    table.add_column("Type")
    table.add_column("Count", justify="right")
    for label, count in count_entities(project).items():
        table.add_row(label, str(count))
    console.print(table)

    for message in result.messages:
        style = {"ERROR": "red", "WARNING": "yellow", "INFO": "cyan"}.get(message.severity, "white")
        entity = f" [{message.entity_id}]" if message.entity_id else ""
        console.print(f"[{style}]{message.severity}[/{style}] {message.code}{entity}: {message.message}")

    console.print(f"Errors: {len(result.errors)}  Warnings: {len(result.warnings)}")
    if not result.ok:
        raise typer.Exit(code=1)


@app.command()
def quantities(project_path: Path) -> None:
    """Report deterministic existing-conditions quantities."""

    project = _load_or_exit(project_path)
    result = validate_project(project)
    if not result.ok:
        console.print("[red]Project has validation errors; fix them before calculating quantities.[/red]")
        for message in result.errors:
            console.print(f"[red]ERROR[/red] {message.code}: {message.message}")
        raise typer.Exit(code=1)

    items = existing_condition_quantities(project)

    detail = Table(title="Existing Conditions Quantities")
    detail.add_column("Category")
    detail.add_column("Entity")
    detail.add_column("Description")
    detail.add_column("Quantity", justify="right")
    detail.add_column("Unit")
    for item in items:
        detail.add_row(
            item.category,
            item.entity_id,
            item.description,
            format_quantity(item.quantity),
            item.unit,
        )
    console.print(detail)

    totals = Table(title="Quantity Totals")
    totals.add_column("Category")
    totals.add_column("Quantity", justify="right")
    totals.add_column("Unit")
    for (category, unit), quantity in summarize_quantities(items).items():
        totals.add_row(category, format_quantity(quantity), unit)
    console.print(totals)


@app.command()
def render(
    project_path: Path,
    sheet: str = typer.Option("existing", "--sheet", help="Sheet to render. Currently: existing."),
    output: Path | None = typer.Option(None, "--output", "-o", help="SVG output path."),
) -> None:
    """Render deterministic SVG drawings from project data."""

    if sheet != "existing":
        console.print("[red]Only --sheet existing is implemented in this phase.[/red]")
        raise typer.Exit(code=2)

    project = _load_or_exit(project_path)
    result = validate_project(project)
    if not result.ok:
        console.print("[red]Project has validation errors; fix them before rendering.[/red]")
        for message in result.errors:
            console.print(f"[red]ERROR[/red] {message.code}: {message.message}")
        raise typer.Exit(code=1)

    if output is None:
        base = project_path if project_path.is_dir() else project_path.parent
        output = base / "generated" / "svg" / "L1.0_existing_conditions.svg"

    written = render_existing_conditions_svg(project, output)
    console.print(f"[green]Generated:[/green] {written}")


def _load_or_exit(project_path: Path):
    try:
        return load_project(project_path)
    except (ProjectLoadError, ValueError) as exc:
        console.print(f"[red]Unable to load project:[/red] {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
