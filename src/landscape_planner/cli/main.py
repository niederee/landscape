"""CLI commands for deterministic landscape project workflows."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from landscape_planner.analysis.validation import count_entities, validate_project
from landscape_planner.analysis.reporting import (
    DEFAULT_REPORT_CSV_PATH,
    DEFAULT_REPORT_JSON_PATH,
    DEFAULT_REPORT_SCHEMA_PATH,
    build_report_payload,
    build_report_schema,
    write_report_csv,
    write_report_json,
    write_report_schema,
)
from landscape_planner.analysis.reference_manifest import (
    DEFAULT_REFERENCES_JSON_PATH,
    DEFAULT_REFERENCES_SCHEMA_PATH,
    build_reference_manifest,
    build_reference_manifest_schema,
    write_reference_manifest_json,
    write_reference_manifest_schema,
)
from landscape_planner.estimating.quantities import (
    existing_condition_quantities,
    DEFAULT_QUANTITIES_JSON_PATH,
    DEFAULT_QUANTITIES_SCHEMA_PATH,
    build_quantities_payload,
    build_quantities_schema,
    format_quantity,
    summarize_quantities,
    write_quantities_json,
    write_quantities_schema,
    write_quantities_csv,
)
from landscape_planner.inspection import entity_inspection_payload, find_entity
from landscape_planner.inspection import entity_display_name, iter_inspectable_entities
from landscape_planner.io.yaml_loader import ProjectLoadError, load_project
from landscape_planner.rendering.svg import render_existing_conditions_svg
from landscape_planner.rendering.html import render_existing_conditions_html

app = typer.Typer(help="Deterministic residential landscape planning tools.")
console = Console()


@app.command()
def validate(
    project_path: Path,
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat warnings as errors and fail the command.",
    ),
) -> None:
    """Validate a landscape project directory or YAML file."""

    project = _load_or_exit(project_path)
    result = validate_project(project, project_root=project_path)

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
    if strict and result.warnings:
        console.print("[bold red]Strict mode: warnings treated as errors.[/bold red]")
        raise typer.Exit(code=1)
    if not result.ok:
        raise typer.Exit(code=1)


@app.command()
def quantities(
    project_path: Path,
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format. Supported values: table, csv, json, schema.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="CSV/JSON/Schema output path.",
    ),
) -> None:
    """Report deterministic existing-conditions quantities."""

    project = _load_or_exit(project_path)
    result = validate_project(project, project_root=project_path)
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
    if output_format == "json":
        quantity_payload = build_quantities_payload(project)
        if output is None:
            base = project_path if project_path.is_dir() else project_path.parent
            output = base / DEFAULT_QUANTITIES_JSON_PATH
        written = write_quantities_json(quantity_payload, output)
        console.print(f"[green]Generated:[/green] {written}")
        return
    if output_format == "schema":
        if output is None:
            base = project_path if project_path.is_dir() else project_path.parent
            output = base / DEFAULT_QUANTITIES_SCHEMA_PATH
        write_quantities_schema(build_quantities_schema(), output)
        console.print(f"[green]Generated:[/green] {output}")
        return
    if output_format != "table":
        console.print("[red]Unsupported quantity format. Use table, csv, json, or schema.[/red]")
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
def references(
    project_path: Path,
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format. Supported values: table, json, schema.",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="JSON/Schema output path.",
    ),
) -> None:
    """List project reference documents and site photos."""

    project = _load_or_exit(project_path)

    if output_format == "json":
        payload = build_reference_manifest(project)
        if output is None:
            base = project_path if project_path.is_dir() else project_path.parent
            output = base / DEFAULT_REFERENCES_JSON_PATH
        written = write_reference_manifest_json(payload, output)
        console.print(f"[green]Generated:[/green] {written}")
        return

    if output_format == "schema":
        if output is None:
            base = project_path if project_path.is_dir() else project_path.parent
            output = base / DEFAULT_REFERENCES_SCHEMA_PATH
        write_reference_manifest_schema(build_reference_manifest_schema(), output)
        console.print(f"[green]Generated:[/green] {output}")
        return

    if output_format != "table":
        console.print("[red]Unsupported references format. Use table, json, or schema.[/red]")
        raise typer.Exit(code=2)

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
        help="Output format. Supported values: table, csv, json, schema.",
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="CSV/JSON/Schema output path."),
) -> None:
    """Summarize project validation, counts, quantities, and references."""

    project = _load_or_exit(project_path)
    base = project_path if project_path.is_dir() else project_path.parent

    if output_format == "schema":
        if output is None:
            output = base / DEFAULT_REPORT_SCHEMA_PATH
        write_report_schema(build_report_schema(), output)
        console.print(f"[green]Generated:[/green] {output}")
        return

    if output_format == "csv":
        result = validate_project(project, project_root=project_path)
        report_payload = build_report_payload(project, result)
        if output is None:
            output = base / DEFAULT_REPORT_CSV_PATH
        write_report_csv(report_payload, output)
        console.print(f"[green]Generated:[/green] {output}")
        return

    if output_format != "table":
        result = validate_project(project, project_root=project_path)
        report_payload = build_report_payload(project, result)
        if output_format == "json":
            if output is None:
                output = base / DEFAULT_REPORT_JSON_PATH
            written = write_report_json(report_payload, output)
            console.print(f"[green]Generated:[/green] {written}")
            return
        console.print("[red]Unsupported report format. Use table, csv, json, or schema.[/red]")
        raise typer.Exit(code=2)

    result = validate_project(project, project_root=project_path)

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
    output: Path | None = typer.Option(None, "--output", "-o", help="SVG or HTML output path."),
    output_format: str = typer.Option("svg", "--format", "-f", help="Output format: svg or html."),
    profile: str = typer.Option("share", "--profile", help="HTML metadata profile: share or private."),
) -> None:
    """Render an SVG drawing or a portable, read-only HTML review file."""

    if output_format not in {"svg", "html"} or profile not in {"share", "private"}:
        console.print("[red]Use --format svg|html and --profile share|private.[/red]")
        raise typer.Exit(code=2)
    if sheet != "existing":
        console.print("[red]Only --sheet existing is implemented in this phase.[/red]")
        raise typer.Exit(code=2)

    project = _load_or_exit(project_path)
    result = validate_project(project, project_root=project_path)
    if not result.ok:
        console.print("[red]Project has validation errors; fix them before rendering.[/red]")
        for message in result.errors:
            console.print(f"[red]ERROR[/red] {message.code}: {message.message}")
        raise typer.Exit(code=1)

    base = project_path if project_path.is_dir() else project_path.parent
    if output is None:
        output = base / "generated" / output_format / f"L1.0_existing_conditions.{output_format}"

    protected = {base / name for name in ("project.yaml", "references.yaml", "existing_conditions.yaml", "planning.yaml")}
    if project_path.is_file():
        protected.add(project_path)
    protected.update(base / item.filename for item in [*project.reference_documents, *project.site_photos])
    if output.resolve() in {path.resolve() for path in protected} or (
        output.exists() and any(path.exists() and output.samefile(path) for path in protected)
    ):
        console.print("[red]Output would overwrite a project input or reference asset.[/red]")
        raise typer.Exit(code=2)
    if output_format == "html" and output.suffix.lower() != ".html":
        console.print(f"[red]Output must have a .{output_format} extension.[/red]")
        raise typer.Exit(code=2)
    for message in result.warnings:
        console.print(f"[yellow]WARNING[/yellow] {message.code}: {message.message}")
    try:
        if output_format == "html":
            written = render_existing_conditions_html(project, output, profile=profile, validation_result=result)
        else:
            written = render_existing_conditions_svg(project, output)
    except (OSError, ValueError) as exc:
        console.print(f"[red]Unable to render:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Generated:[/green] {written}")
    if output_format == "html":
        console.print(f"Existing conditions; profile={profile}; warnings={len(result.warnings)}; bytes={written.stat().st_size}")



@app.command("compare")
def compare(
    project_path: Path,
    planning: Path | None = typer.Option(None, "--planning", help="Planning YAML; defaults to planning.yaml beside project."),
    output: Path | None = typer.Option(None, "--output", "-o"),
    profile: str = typer.Option("share", "--profile"),
) -> None:
    """Review existing conditions and independently authored alternatives offline."""
    _planning_export(project_path, planning, output, profile, phases=False)


@app.command("phases")
def phases(
    project_path: Path,
    planning: Path | None = typer.Option(None, "--planning"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    profile: str = typer.Option("share", "--profile"),
) -> None:
    """Review cumulative construction phases, dependencies and sourced cost ranges."""
    _planning_export(project_path, planning, output, profile, phases=True)


def _planning_export(project_path, planning_path, output, profile, *, phases):
    import os
    import tempfile
    from landscape_planner.planning.document import load_planning
    from landscape_planner.planning.concepts import compare_projects, resolve_concept
    from landscape_planner.planning.phases import resolve_phases
    from landscape_planner.rendering.comparison import comparison_html

    if profile not in {"share", "private"}:
        console.print("Use --profile share|private.")
        raise typer.Exit(code=2)
    project = _load_or_exit(project_path)
    base = project_path if project_path.is_dir() else project_path.parent
    planning_path = planning_path or base / "planning.yaml"
    output = output or base / "generated/html" / ("phases.html" if phases else "alternatives.html")
    protected = {base / name for name in ("project.yaml", "references.yaml", "existing_conditions.yaml", "planning.yaml")}
    protected.add(planning_path)
    if project_path.is_file():
        protected.add(project_path)
    protected.update(base / item.filename for item in [*project.reference_documents, *project.site_photos])
    if output.resolve() in {path.resolve() for path in protected} or (
        output.exists() and any(path.exists() and output.samefile(path) for path in protected)
    ):
        console.print("Output would overwrite a project input or reference asset.")
        raise typer.Exit(code=2)
    if output.suffix.lower() != ".html":
        console.print("Output must have a .html extension.")
        raise typer.Exit(code=2)
    try:
        document = load_planning(planning_path)
        snapshots = [("existing", "Existing conditions", project)]
        metadata = {}
        if phases:
            if not document.phases:
                raise ValueError("No construction phases are declared.")
            resolved = resolve_phases(project, document.phases)
            if document.selected_concept:
                selected = next(c for c in document.concepts if c.id == document.selected_concept)
                target = resolve_concept(project, selected)
                delta = compare_projects(target, resolved[-1].project)
                if any(delta[key] for key in ("added", "removed", "modified")):
                    raise ValueError("Final phase does not match selected_concept; reconcile the phase operations with the selected design.")
            for snapshot in resolved:
                snapshots.append((snapshot.phase.id, snapshot.phase.name, snapshot.project))
                metadata[snapshot.phase.id] = {
                    "cost": snapshot.cost.model_dump(mode="json"), "cumulative_cost": snapshot.cumulative_cost.model_dump(mode="json"),
                    "warnings": snapshot.warnings, "depends_on": snapshot.phase.depends_on,
                    "cost_items": [item.model_dump(mode="json") for item in snapshot.phase.cost_items],
                }
        else:
            if not document.concepts:
                raise ValueError("No design alternatives are declared.")
            snapshots.extend((c.id, c.name, resolve_concept(project, c)) for c in document.concepts)
        html = comparison_html(snapshots, profile=profile, project_root=project_path, metadata=metadata)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                             prefix=f".{output.name}.", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(html)
            os.replace(temporary, output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    except (OSError, ValueError) as exc:
        console.print(f"Unable to export planning review: {exc}", markup=False)
        raise typer.Exit(code=1) from exc
    console.print(f"Generated: {output}; snapshots={len(snapshots)}; profile={profile}", markup=False)


def _load_or_exit(project_path: Path):
    try:
        return load_project(project_path)
    except (ProjectLoadError, ValueError) as exc:
        console.print(f"[red]Unable to load project:[/red] {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
