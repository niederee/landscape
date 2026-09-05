"""CLI commands for deterministic landscape project workflows."""

from __future__ import annotations

import csv
import json
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
def report(
    project_path: Path,
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format. Supported values: table, csv, json.",
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="CSV/JSON output path."),
) -> None:
    """Summarize project validation, counts, quantities, and references."""

    project = _load_or_exit(project_path)
    result = validate_project(project)
    report_payload = _build_report_payload(project, result)

    if output_format == "json":
        output_data = json.dumps(report_payload, indent=2, sort_keys=True)
        if output is None:
            console.print(JSON.from_data(json.loads(output_data)))
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(f"{output_data}\n", encoding="utf-8")
            console.print(f"[green]Generated:[/green] {output}")
        return

    if output_format == "csv":
        if output is None:
            base = project_path if project_path.is_dir() else project_path.parent
            output = base / "generated" / "report" / "report.csv"
        write_report_csv(report_payload, output)
        console.print(f"[green]Generated:[/green] {output}")
        return

    if output_format != "table":
        console.print("[red]Unsupported report format. Use table, csv, or json.[/red]")
        raise typer.Exit(code=2)

    console.print(f"[bold]Project Report:[/bold] {project.project_id}")
    console.print(f"[bold]Validation Status:[/bold] {'OK' if result.ok else 'FAILED'}")

    validation = Table(title="Validation")
    validation.add_column("Status")
    validation.add_column("Count", justify="right")
    validation.add_row("Errors", str(len(result.errors)))
    validation.add_row("Warnings", str(len(result.warnings)))
    validation.add_row("Overall", "OK" if result.ok else "FAILED")
    console.print(validation)

    if result.messages:
        messages = Table(title="Validation Messages")
        messages.add_column("Severity")
        messages.add_column("Code")
        messages.add_column("Entity")
        messages.add_column("Message")
        for message in result.messages:
            style = {"ERROR": "red", "WARNING": "yellow", "INFO": "cyan"}.get(message.severity, "white")
            entity = message.entity_id or ""
            messages.add_row(
                f"[{style}]{message.severity}[/{style}]",
                message.code,
                entity,
                message.message,
            )
        console.print(messages)

    counts = Table(title="Entity Counts")
    counts.add_column("Category")
    counts.add_column("Count", justify="right")
    for category, total in count_entities(project).items():
        counts.add_row(category, str(total))
    console.print(counts)

    quantities = Table(title="Existing-Conditions Quantity Totals")
    quantities.add_column("Category")
    quantities.add_column("Quantity", justify="right")
    quantities.add_column("Unit")
    for (category, unit), quantity in summarize_quantities(existing_condition_quantities(project)).items():
        quantities.add_row(category, format_quantity(quantity), unit)
    console.print(quantities)

    references = Table(title="Reference Summary")
    references.add_column("Type")
    references.add_column("Count", justify="right")
    references.add_column("IDs")
    references.add_row(
        "Reference Documents",
        str(len(project.reference_documents)),
        ", ".join(document.id for document in sorted(project.reference_documents, key=lambda item: item.id)),
    )
    references.add_row(
        "Site Photos",
        str(len(project.site_photos)),
        ", ".join(photo.id for photo in sorted(project.site_photos, key=lambda item: item.id)),
    )
    console.print(references)


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


def _build_report_payload(project, result) -> dict:
    totals = summarize_quantities(existing_condition_quantities(project))

    return {
        "project_id": project.project_id,
        "validation": {
            "ok": result.ok,
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "infos": len(result.infos),
            "messages": [
                {
                    "severity": message.severity,
                    "code": message.code,
                    "entity_id": message.entity_id,
                    "message": message.message,
                }
                for message in result.messages
            ],
        },
        "entity_counts": [
            {"category": category, "count": total} for category, total in count_entities(project).items()
        ],
        "quantity_totals": [
            {"category": category, "unit": unit, "quantity": quantity} for (category, unit), quantity in totals.items()
        ],
        "references": {
            "documents": [document.id for document in sorted(project.reference_documents, key=lambda item: item.id)],
            "site_photos": [photo.id for photo in sorted(project.site_photos, key=lambda item: item.id)],
        },
    }


def write_report_csv(report_payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["section", "category", "unit", "count", "value", "entity_id", "message_code", "message"])

        validation = report_payload["validation"]
        writer.writerow([
            "validation",
            "",
            "",
            "",
            "",
            "",
            "",
            f"errors={validation['errors']};warnings={validation['warnings']};infos={validation['infos']};ok={validation['ok']}",
        ])

        for item in report_payload["entity_counts"]:
            writer.writerow(["entity_count", item["category"], "", item["count"], "", "", "", ""])

        for item in report_payload["quantity_totals"]:
            writer.writerow([
                "quantity_total",
                item["category"],
                item["unit"],
                "",
                item["quantity"],
                "",
                "",
                "",
            ])

        for document_id in report_payload["references"]["documents"]:
            writer.writerow(["reference_document", "", "", "", "", document_id, "", ""])
        for photo_id in report_payload["references"]["site_photos"]:
            writer.writerow(["site_photo", "", "", "", "", photo_id, "", ""])

        for message in validation["messages"]:
            writer.writerow([
                "validation_message",
                message["entity_id"] or "",
                "",
                "",
                "",
                "",
                message["code"],
                message["message"],
            ])


if __name__ == "__main__":
    app()
