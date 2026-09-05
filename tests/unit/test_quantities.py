from pathlib import Path

from landscape_planner.estimating.quantities import (
    existing_condition_quantities,
    format_csv_quantity,
    format_quantity,
    summarize_quantities,
    write_quantities_csv,
)
from landscape_planner.io.yaml_loader import load_project


FIXTURE = Path("tests/fixtures/synthetic")


def test_existing_condition_quantities_are_calculated_by_entity():
    project = load_project(FIXTURE)
    items = existing_condition_quantities(project)
    quantities = {(item.category, item.entity_id): item.quantity for item in items}

    assert quantities[("parcel", "PARCEL001")] == 10400
    assert quantities[("structure", "HOUSE001")] == 2475
    assert quantities[("hardscape", "DRIVE001")] == 912
    assert quantities[("hardscape", "PATIO001")] == 540
    assert quantities[("hardscape", "WALK001")] == 190
    assert quantities[("linear_feature", "FENCE001")] == 264
    assert quantities[("planting_bed", "BED001")] == 304
    assert quantities[("planting_bed", "BED002")] == 494
    assert quantities[("lawn", "LAWN001")] == 1140
    assert quantities[("lawn", "LAWN002")] == 1035
    assert quantities[("tree", "TREES")] == 3
    assert quantities[("utility", "UTILITIES")] == 1


def test_quantity_summary_groups_by_category_and_unit():
    project = load_project(FIXTURE)
    totals = summarize_quantities(existing_condition_quantities(project))

    assert totals[("hardscape", "sqft")] == 1642
    assert totals[("planting_bed", "sqft")] == 798
    assert totals[("lawn", "sqft")] == 2175
    assert totals[("tree", "each")] == 3


def test_quantity_formatting_avoids_unneeded_decimal_places():
    assert format_quantity(1200) == "1,200"
    assert format_quantity(12.345) == "12.35"


def test_csv_quantity_formatting_is_machine_readable():
    assert format_csv_quantity(1200) == "1200"
    assert format_csv_quantity(12.34567) == "12.346"
    assert format_csv_quantity(12.300) == "12.3"


def test_write_quantities_csv_includes_detail_and_totals(tmp_path):
    project = load_project(FIXTURE)
    output = tmp_path / "quantities.csv"

    write_quantities_csv(existing_condition_quantities(project), output)

    csv_text = output.read_text(encoding="utf-8")
    assert csv_text.startswith("section,category,entity_id,description,quantity,unit\n")
    assert "detail,hardscape,DRIVE001,Driveway,912,sqft\n" in csv_text
    assert "total,hardscape,,,1642,sqft\n" in csv_text
