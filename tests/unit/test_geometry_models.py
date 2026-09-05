from landscape_planner.model.geometry import GeometryData
from landscape_planner.model.project import HardscapeArea, LawnArea, Tree


def test_polygon_area_is_calculated_from_geometry():
    lawn = LawnArea(
        id="LAWN001",
        geometry=GeometryData(
            type="polygon",
            coordinates=[(0, 0), (10, 0), (10, 20), (0, 20)],
        ),
    )

    assert lawn.area_sqft == 200


def test_linestring_rejects_single_coordinate():
    try:
        GeometryData(type="linestring", coordinates=[(0, 0)])
    except ValueError as exc:
        assert "at least two coordinates" in str(exc)
    else:
        raise AssertionError("single-point linestring should fail")


def test_hardscape_perimeter_is_calculated_from_geometry():
    patio = HardscapeArea(
        id="PATIO001",
        subtype="patio",
        geometry=GeometryData(
            type="polygon",
            coordinates=[(0, 0), (12, 0), (12, 8), (0, 8)],
        ),
    )

    assert patio.area_sqft == 96
    assert patio.perimeter_ft == 40


def test_tree_location_exposes_point_geometry():
    tree = Tree(id="TREE001", location=(5, 7), common_name="Live Oak", canopy_radius_ft=12)

    assert tree.point.x == 5
    assert tree.point.y == 7

