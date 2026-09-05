"""Report payload model and deterministic report artifact generation."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from landscape_planner.analysis.validation import ValidationResult
from landscape_planner.estimating.quantities import summarize_quantities
from landscape_planner.model.project import LandscapeProject
from landscape_planner.estimating.quantities import existing_condition_quantities


REPORT_SCHEMA_VERSION = "1.0.0"
DEFAULT_REPORT_DIR = Path("generated") / "report"
DEFAULT_REPORT_JSON_PATH = DEFAULT_REPORT_DIR / "landscape_report.json"
DEFAULT_REPORT_CSV_PATH = DEFAULT_REPORT_DIR / "landscape_report.csv"
DEFAULT_REPORT_SCHEMA_PATH = DEFAULT_REPORT_DIR / "landscape_report.schema.json"


class ReportValidationMessage(BaseModel):
    severity: str
    code: str
    entity_id: str | None
    message: str


class ReportValidation(BaseModel):
    ok: bool
    errors: int
    warnings: int
    infos: int
    messages: tuple[ReportValidationMessage, ...]


class ReportEntityCount(BaseModel):
    category: str
    count: int


class ReportQuantityTotal(BaseModel):
    category: str
    unit: str
    quantity: float


class ReportReferences(BaseModel):
    documents: tuple[str, ...]
    site_photos: tuple[str, ...]


class ReportPayload(BaseModel):
    schema_version: str = Field(default=REPORT_SCHEMA_VERSION)
    project_id: str
    validation: ReportValidation
    entity_counts: tuple[ReportEntityCount, ...]
    quantity_totals: tuple[ReportQuantityTotal, ...]
    references: ReportReferences


def build_report_payload(project: LandscapeProject, result: ValidationResult) -> ReportPayload:
    totals = summarize_quantities(existing_condition_quantities(project))

    return ReportPayload(
        project_id=project.project_id,
        validation=ReportValidation(
            ok=result.ok,
            errors=len(result.errors),
            warnings=len(result.warnings),
            infos=len(result.infos),
            messages=tuple(
                ReportValidationMessage(
                    severity=message.severity,
                    code=message.code,
                    entity_id=message.entity_id,
                    message=message.message,
                )
                for message in result.messages
            ),
        ),
        entity_counts=tuple(
            ReportEntityCount(category=category, count=total)
            for category, total in sorted_count_entities(project).items()
        ),
        quantity_totals=tuple(
            ReportQuantityTotal(category=category, unit=unit, quantity=quantity)
            for (category, unit), quantity in totals.items()
        ),
        references=ReportReferences(
            documents=tuple(document.id for document in sorted(project.reference_documents, key=lambda item: item.id)),
            site_photos=tuple(photo.id for photo in sorted(project.site_photos, key=lambda item: item.id)),
        ),
    )


def build_report_schema() -> dict:
    return ReportPayload.model_json_schema()


def write_report_json(payload: ReportPayload, output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload.model_dump_json(indent=2, by_alias=False) + "\n", encoding="utf-8")
    return output_path


def write_report_schema(schema: dict, output_path: Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def write_report_csv(payload: ReportPayload, output_path: Path) -> Path:
    import csv

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "section",
            "category",
            "unit",
            "count",
            "value",
            "entity_id",
            "message_code",
            "message",
        ])

        validation = payload.validation
        writer.writerow([
            "validation",
            "",
            "",
            "",
            "",
            "",
            "",
            f"errors={validation.errors};warnings={validation.warnings};infos={validation.infos};ok={validation.ok}",
        ])

        for item in payload.entity_counts:
            writer.writerow(["entity_count", item.category, "", item.count, "", "", "", ""])

        for item in payload.quantity_totals:
            writer.writerow([
                "quantity_total",
                item.category,
                item.unit,
                "",
                item.quantity,
                "",
                "",
                "",
            ])

        for document_id in payload.references.documents:
            writer.writerow(["reference_document", "", "", "", "", document_id, "", ""])
        for photo_id in payload.references.site_photos:
            writer.writerow(["site_photo", "", "", "", "", photo_id, "", ""])

        for message in validation.messages:
            writer.writerow([
                "validation_message",
                message.entity_id or "",
                "",
                "",
                "",
                "",
                message.code,
                message.message,
            ])

    return output


def sorted_count_entities(project: LandscapeProject) -> dict[str, int]:
    # Import lazily to avoid circular import with validation module.
    from landscape_planner.analysis.validation import count_entities

    return dict(sorted(count_entities(project).items(), key=lambda item: item[0]))
