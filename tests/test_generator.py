import json
import os
import tempfile

import pytest

from launch_points import generator


def test_calculate_length_simple():
    # Two points 1 degree latitude apart at lon 0: approx 111 km
    coords = [[0, 0], [0, 1]]  # [lon, lat]
    dist = generator.calculate_length(coords)
    assert 110 <= dist <= 112


def test_validate_geojson():
    path = os.path.join(os.path.dirname(__file__), "..", "berlin", "routes.geojson")
    # path may not be normalized; make absolute
    path = os.path.abspath(path)
    assert generator.validate_geojson(path)


def test_load_markers_normalization(tmp_path):
    csv_path = tmp_path / "markers.csv"
    csv_path.write_text("name, lat, lon, transport\nA, 52.0, 13.0, True\nB, 52.1, 13.1, false\n")
    df = generator.load_markers(str(csv_path), "test")
    assert "marker_type" in df.columns
    assert df["transport"].tolist() == [True, False]
    assert df["lat"].dtype.kind in ("f", "i")
