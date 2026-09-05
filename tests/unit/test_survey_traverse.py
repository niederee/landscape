import math

import pytest

from landscape_planner.surveying import SurveyLeg, SurveyTraverse, load_traverse, reconstruct_traverse


def rectangle(**kwargs):
    return SurveyTraverse(legs=[
        SurveyLeg(bearing="N 30 E", distance_ft=100),
        SurveyLeg(bearing="S60°00'00\"E", distance_ft=50),
        SurveyLeg(bearing="S 30 00 00 W", distance_ft=100),
        SurveyLeg(bearing="N60°00′00″W", distance_ft=50),
    ], **kwargs)


def test_nonaxis_rectangle_preserves_courses_and_provenance():
    spec = rectangle(source="Synthetic example, not Greenleaf", origin=(10, 20))
    result = reconstruct_traverse(spec)
    assert result.accepted
    assert result.boundary.to_shape().area == pytest.approx(5000)
    assert result.boundary.coordinates[1] == pytest.approx((60, 20 + 50 * math.sqrt(3)))
    assert result.closure_error_ft < 1e-10
    assert result.perimeter_ft == 300
    assert result.traverse.source == spec.source
    assert 'NaN' not in result.model_dump_json()


def test_bad_course_fails_closure_without_boundary():
    spec = rectangle()
    spec.legs[3] = SurveyLeg(bearing="N 50 W", distance_ft=50)
    result = reconstruct_traverse(spec)
    assert not result.accepted
    assert result.boundary is None
    assert result.closure_error_ft > 1
    assert result.closure_ratio == pytest.approx(result.closure_error_ft / 300)
    assert any("exceeds tolerance" in item for item in result.diagnostics)


def test_small_gap_is_not_distributed():
    spec = SurveyTraverse(legs=[
        SurveyLeg(bearing="E", distance_ft=10), SurveyLeg(bearing="N", distance_ft=10),
        SurveyLeg(bearing="W", distance_ft=10), SurveyLeg(bearing="S", distance_ft=9.95),
    ])
    result = reconstruct_traverse(spec)
    assert result.accepted
    assert result.closure_dy_ft == pytest.approx(.05)
    assert result.boundary.coordinates[-2] == pytest.approx((0, .05))
    assert result.boundary.coordinates[-1] == (0, 0)
    assert result.perimeter_ft == 39.95


@pytest.mark.parametrize("bearing", ["N91E", "N 21 60 00 E", "N 21 00 60 E", "NE",
                                       "N -1 E", "N NaN W", "N 1e2 E", "30", "N21E junk"])
def test_invalid_bearings(bearing):
    with pytest.raises(ValueError):
        SurveyLeg(bearing=bearing, distance_ft=10)


@pytest.mark.parametrize("distance", [0, -1, float("nan"), float("inf")])
def test_invalid_distance(distance):
    with pytest.raises(ValueError):
        SurveyLeg(bearing="N", distance_ft=distance)


@pytest.mark.parametrize("kwargs", [{"origin": (float("nan"), 0)},
                                     {"max_closure_error_ft": float("inf")},
                                     {"max_closure_error_ft": -1}, {"schema_version": 2}])
def test_invalid_spec(kwargs):
    with pytest.raises(ValueError):
        rectangle(**kwargs)


def test_requires_three_legs():
    with pytest.raises(ValueError):
        SurveyTraverse(legs=[SurveyLeg(bearing="N", distance_ft=1)])


def test_self_intersection_rejected_even_when_closed():
    spec = SurveyTraverse(legs=[
        SurveyLeg(bearing="N45E", distance_ft=10 * math.sqrt(2)),
        SurveyLeg(bearing="W", distance_ft=10),
        SurveyLeg(bearing="S45E", distance_ft=10 * math.sqrt(2)),
        SurveyLeg(bearing="W", distance_ft=10),
    ])
    result = reconstruct_traverse(spec)
    assert not result.accepted
    assert result.boundary is None
    assert any("Invalid boundary polygon" in item for item in result.diagnostics)


def test_zero_area_rejected():
    result = reconstruct_traverse(SurveyTraverse(legs=[
        SurveyLeg(bearing="N", distance_ft=10), SurveyLeg(bearing="N", distance_ft=10),
        SurveyLeg(bearing="S", distance_ft=20),
    ]))
    assert not result.accepted
    assert result.boundary is None


def test_load_yaml_and_decimal_bearing(tmp_path):
    path = tmp_path / "traverse.yaml"
    path.write_text("""schema_version: 1
source: synthetic
legs:
  - {bearing: N22.5E, distance_ft: 10}
  - {bearing: S67.5E, distance_ft: 10}
  - {bearing: S22.5W, distance_ft: 10}
  - {bearing: N67.5W, distance_ft: 10}
""")
    result = reconstruct_traverse(load_traverse(path))
    assert result.accepted
    assert result.boundary.to_shape().area == pytest.approx(100)


def test_overflow_rejected():
    spec = SurveyTraverse(legs=[SurveyLeg(bearing="N", distance_ft=1e308)] * 3)
    with pytest.raises(ValueError, match="finite coordinate"):
        reconstruct_traverse(spec)
