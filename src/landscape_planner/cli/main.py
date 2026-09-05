"""CLI commands for deterministic landscape project workflows."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from landscape_planner.analysis.validation import count_entities, validate_project
from landscape_planner.estimating.quantities import (
    existing_condition_quantities,
    format_quantity,
    summarize_quantities,
    write_quantities_csv,
)
from landscape_planner.inspection import entity_inspection_payload, find_entity
from landscape_planner.inspection import entity_display_name, iter_inspectable_entities
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
def quantities(
    project_path: Path,
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format. Supported values: table, csv.",
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="CSV output path."),
) -> None:
    """Report deterministic existing-conditions quantities."""

    project = _load_or_exit(project_path)
    result = validate_project(project)
    if not result.ok:
        console.print("[red]Project has validation errors; fix them before calculating quantities.[/red]")
        for message in result.errors:
            console.print(f"[red]ERROR[/red] {message.code}: {message.message}")
        raise typer.Exit(code=1)

    items = existing_condition_quantities(project)
    if output_format == "csv":
        if output is None:
            base = project_path if project_path.is_dir() else project_path.parent
            output = base / "generated" / "csv" / "existing_conditions_quantities.csv"
        written = write_quantities_csv(items, output)
        console.print(f"[green]Generated:[/green] {written}")
        return
    if output_format != "table":
        console.print("[red]Unsupported quantity format. Use table or csv.[/red]")
        raise typer.Exit(code=2)

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
def references(project_path: Path) -> None:
    """List project reference documents and site photos."""

    project = _load_or_exit(project_path)

    documents = Table(title="Reference Documents")
    documents.add_column("ID", no_wrap=True)
    documents.add_column("Type")
    documents.add_column("Filename")
    documents.add_column("Date")
    documents.add_column("Name")
    for document in sorted(project.reference_documents, key=lambda item: item.id):
        documents.add_row(
            document.id,
            document.document_type,
            document.filename,
            document.date.isoformat() if document.date else "",
            document.name or "",
        )
    console.print(documents)

    photos = Table(title="Site Photos")
    photos.add_column("ID", no_wrap=True)
    photos.add_column("Filename")
    photos.add_column("Camera")
    photos.add_column("Direction")
    photos.add_column("Date")
    photos.add_column("Description")
    for photo in sorted(project.site_photos, key=lambda item: item.id):
        camera = ""
        if photo.camera_location is not None:
            camera = f"{photo.camera_location[0]:g}, {photo.camera_location[1]:g}"
        photos.add_row(
            photo.id,
            photo.filename,
            camera,
            f"{photo.direction_degrees:g}" if photo.direction_degrees is not None else "",
            photo.date.isoformat() if photo.date else "",
            photo.description or "",
        )
    console.print(photos)


@app.command("list-entities")
def list_entities(
    project_path: Path,
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by entity category."),
) -> None:
    """List project entities by stable ID."""

    project = _load_or_exit(project_path)
    entities = tuple(iter_inspectable_entities(project))
    if category is not None:
        entities = tuple(entity for entity in entities if entity.category == category)

    table = Table(title="Project Entities")
    table.add_column("Category")
    table.add_column("ID", no_wrap=True)
    table.add_column("Name")
    table.add_column("Source")
    for inspected in entities:
        source = ""
        if inspected.entity.source is not None and inspected.entity.source.reference is not None:
            source = inspected.entity.source.reference
        table.add_row(
            inspected.category,
            inspected.entity.id,
            entity_display_name(inspected),
            source,
        )
    console.print(table)
    console.print(f"Entities: {len(entities)}")


@app.command()
def inspect(project_path: Path, entity_id: str) -> None:
    """Inspect one project entity by stable ID."""

    project = _load_or_exit(project_path)
    result = find_entity(project, entity_id)
    if result is None:
        console.print(f"[red]Entity not found:[/red] {entity_id}")
        raise typer.Exit(code=1)

    console.print(f"[bold]{result.category}[/bold] {result.entity.id}")
    console.print(JSON.from_data(entity_inspection_payload(result)))


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
