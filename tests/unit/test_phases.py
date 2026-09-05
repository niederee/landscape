from pathlib import Path

import pytest
from pydantic import ValidationError

from landscape_planner.io.yaml_loader import load_project
from landscape_planner.planning.concepts import ConceptOperation
from landscape_planner.planning.phases import CostItem, Phase, resolve_phases


def project():
    return load_project(Path("tests/fixtures/synthetic"))


def tree_operation(action, entity_id="NEW_TREE", **data):
    return ConceptOperation(action=action, category="trees", entity_id=entity_id, data=data)


def new_tree():
    return tree_operation("add", id="NEW_TREE", location=[10, 10], canopy_radius_ft=2,
                          status="proposed")


def test_phases_topological_cumulative_and_isolated():
    baseline = project()
    original = baseline.model_dump()
    phases = [
        Phase(id="later", name="Later", depends_on=["first"], operations=[
            tree_operation("update", common_name="Changed tree")]),
        Phase(id="first", name="First", operations=[new_tree()]),
        Phase(id="independent", name="Independent"),
    ]
    snapshots = resolve_phases(baseline, phases)
    assert [s.phase.id for s in snapshots] == ["first", "later", "independent"]
    assert baseline.model_dump() == original
    assert snapshots[0].project.existing_conditions.trees[-1].common_name is None
    assert snapshots[1].project.existing_conditions.trees[-1].common_name == "Changed tree"
    snapshots[2].project.existing_conditions.trees[-1].common_name = "Other"
    assert snapshots[1].project.existing_conditions.trees[-1].common_name == "Changed tree"
    assert "Potential rework" in snapshots[1].warnings[0]
    assert not snapshots[0].cost.complete
    assert snapshots[0].cost.unknown_item_ids == ["first:unestimated"]


@pytest.mark.parametrize("phases,match", [
    ([Phase(id="a", name="A"), Phase(id="a", name="Other")], "Duplicate"),
    ([Phase(id="a", name="A", depends_on=["missing"])], "unknown"),
    ([Phase(id="a", name="A", depends_on=["a"])], "Cyclic"),
    ([Phase(id="a", name="A", depends_on=["b"]),
      Phase(id="b", name="B", depends_on=["a"])], "Cyclic"),
])
def test_reject_invalid_phase_graph(phases, match):
    with pytest.raises(ValueError, match=match):
        resolve_phases(project(), phases)


def test_explicit_cost_subtotals_and_unknowns_accumulate():
    known = CostItem(id="allowance", quantity=3, unit="each", rate_low=20, rate_high=30,
                     source="Synthetic test-only supplied allowance")
    unknown = CostItem(id="delivery", quantity=1, unit="trip")
    snapshots = resolve_phases(project(), [
        Phase(id="a", name="A", cost_items=[known, unknown]),
        Phase(id="b", name="B", cost_items=[known]),
    ])
    assert snapshots[0].cost.known_low == 60
    assert snapshots[0].cost.known_high == 90
    assert snapshots[1].cost.complete
    assert snapshots[1].cumulative_cost.known_low == 120
    assert snapshots[1].cumulative_cost.known_high == 180
    assert snapshots[1].cumulative_cost.unknown_item_ids == ["a:delivery"]
    assert not snapshots[1].cumulative_cost.complete
    assert snapshots[1].cumulative_cost.currency == "USD"


@pytest.mark.parametrize("overrides", [
    {"quantity": -1}, {"quantity": float("nan")}, {"quantity": float("inf")},
    {"rate_low": 5}, {"rate_high": 5},
    {"rate_low": -1, "rate_high": 5, "source": "test"},
    {"rate_low": 6, "rate_high": 5, "source": "test"},
    {"rate_low": 1, "rate_high": 5},
    {"rate_low": 1, "rate_high": 5, "source": "  "},
    {"rate_low": 1, "rate_high": float("inf"), "source": "test"},
    {"quantity": 1e308, "rate_low": 2, "rate_high": 3, "source": "test"},
    {"unit": " "}, {"currency": "EUR"},
])
def test_cost_inputs_fail_closed(overrides):
    with pytest.raises(ValidationError):
        CostItem.model_validate({"id": "item", "quantity": 1, "unit": "each", **overrides})


def test_duplicate_cost_ids_and_dependencies_rejected():
    item = CostItem(id="x", quantity=1, unit="each")
    with pytest.raises(ValidationError, match="Duplicate cost"):
        Phase(id="a", name="A", cost_items=[item, item])
    with pytest.raises(ValidationError, match="Duplicate phase dependencies"):
        Phase(id="a", name="A", depends_on=["b", "b"])


def test_preserve_across_phase_boundary_rejects_modification():
    baseline = project()
    tree_id = baseline.existing_conditions.trees[0].id
    with pytest.raises(ValueError, match="preserved"):
        resolve_phases(baseline, [
            Phase(id="a", name="A", operations=[tree_operation("preserve", tree_id)]),
            Phase(id="b", name="B", operations=[tree_operation("update", tree_id,
                                                              common_name="Changed")]),
        ])


def test_added_then_removed_warns_and_removes():
    baseline = project()
    snapshots = resolve_phases(baseline, [
        Phase(id="a", name="A", operations=[new_tree()]),
        Phase(id="b", name="B", operations=[tree_operation("remove")]),
    ])
    assert snapshots[-1].project.existing_conditions == baseline.existing_conditions
    assert "will remove" in snapshots[-1].warnings[0]


def test_empty_phases_and_overflow():
    assert resolve_phases(project(), []) == []
    huge = CostItem(id="huge", quantity=1, unit="each", rate_low=1e308, rate_high=1e308,
                    source="Overflow test input")
    with pytest.raises(ValueError, match="not finite"):
        resolve_phases(project(), [Phase(id="a", name="A", cost_items=[huge]),
                                   Phase(id="b", name="B", cost_items=[huge])])


def test_mutated_cost_instance_revalidated():
    item = CostItem(id="x", quantity=1, unit="each", rate_low=1, rate_high=2, source="test")
    phase = Phase(id="a", name="A", cost_items=[item])
    item.rate_high = -2
    with pytest.raises(ValidationError):
        resolve_phases(project(), [phase])
