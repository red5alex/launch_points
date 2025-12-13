import os
import unittest

from launch_points import generator


class TestGenerator(unittest.TestCase):
    def test_calculate_length_simple(self):
        coords = [[0, 0], [0, 1]]
        dist = generator.calculate_length(coords)
        self.assertTrue(110 <= dist <= 112)

    def test_validate_geojson(self):
        path = os.path.join(os.path.dirname(__file__), "..", "berlin", "routes.geojson")
        path = os.path.abspath(path)
        self.assertTrue(generator.validate_geojson(path))

    def test_validate_station_paths(self):
        import tempfile

        tfile = tempfile.NamedTemporaryFile(mode='w+', suffix='.geojson', delete=False)
        try:
            content = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"station_name": "Test Station", "station_type": "train"},
                        "geometry": {"type": "LineString", "coordinates": [[13.4, 52.5], [13.41, 52.501]]},
                    }
                ],
            }
            import json as _json

            tfile.write(_json.dumps(content))
            tfile.flush()
            tfile.close()

            self.assertTrue(generator.validate_station_paths(tfile.name))
        finally:
            try:
                os.unlink(tfile.name)
            except Exception:
                pass

    def test_generate_with_station_paths(self):
        import tempfile

        tmpdir = tempfile.mkdtemp()
        out_index = os.path.join(tmpdir, "index.html")
        out_editor = os.path.join(tmpdir, "editor.html")

        # Create a small station paths GeoJSON
        station_geo = os.path.join(tmpdir, "station_paths.geojson")
        content = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"station_name": "Central Station", "station_type": "train"},
                    "geometry": {"type": "LineString", "coordinates": [[13.4050, 52.5200], [13.406, 52.5205]]},
                }
            ],
        }
        with open(station_geo, "w", encoding="utf-8") as f:
            import json as _json

            f.write(_json.dumps(content))

        markers = [
            (os.path.join(os.path.dirname(__file__), "..", "berlin", "launch_with_transport.csv"), "launch_with_transport"),
        ]
        geojson = os.path.join(os.path.dirname(__file__), "..", "berlin", "routes.geojson")
        geojson = os.path.abspath(geojson)

        generator.generate_map(markers, geojson, station_paths=station_geo, output_index=out_index, output_editor=out_editor)

        self.assertTrue(os.path.exists(out_index))
        with open(out_index, "r", encoding="utf-8") as f:
            html = f.read()
        # The station name and length should appear in the generated HTML and the dotted line style and color should be present
        self.assertIn("Central Station", html)
        # Calculate expected length and assert it appears in the HTML tooltip
        expected_length = generator.calculate_length([[13.4050, 52.5200], [13.406, 52.5205]])
        self.assertIn(f"{expected_length:.2f} km", html)
        # Check dotted pattern and dark grey color presence
        self.assertIn("1, 6", html)
        self.assertIn("#4a4a4a", html)
        # station icon size should be large (20px)
        self.assertIn("font-size: 20px", html)

    def test_tram_icon_and_dotted_path(self):
        import tempfile

        tmpdir = tempfile.mkdtemp()
        out_index = os.path.join(tmpdir, "index.html")
        out_editor = os.path.join(tmpdir, "editor.html")

        # Create a small station paths GeoJSON with a tram station
        station_geo = os.path.join(tmpdir, "station_paths.geojson")
        content = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"station_name": "Tram Stop", "station_type": "tram"},
                    "geometry": {"type": "LineString", "coordinates": [[13.4100, 52.5150], [13.4110, 52.5154]]},
                }
            ],
        }
        with open(station_geo, "w", encoding="utf-8") as f:
            import json as _json

            f.write(_json.dumps(content))

        markers = [
            (os.path.join(os.path.dirname(__file__), "..", "berlin", "launch_with_transport.csv"), "launch_with_transport"),
        ]
        geojson = os.path.join(os.path.dirname(__file__), "..", "berlin", "routes.geojson")
        geojson = os.path.abspath(geojson)

        generator.generate_map(markers, geojson, station_paths=station_geo, output_index=out_index, output_editor=out_editor)

        self.assertTrue(os.path.exists(out_index))
        with open(out_index, "r", encoding="utf-8") as f:
            html = f.read()

        # Check for tram icon class (Font Awesome 'fa-train-tram'), dotted pattern and matching dark grey color and size
        self.assertIn("fa-train-tram", html)
        self.assertIn("1, 6", html)
        self.assertIn("#4a4a4a", html)
        self.assertIn("font-size: 20px", html)
        # ensure distance tooltip text is present and formatted
        expected_length = generator.calculate_length([[13.4100, 52.5150], [13.4110, 52.5154]])
        self.assertIn(f"{expected_length:.2f} km", html)

    def test_example_station_paths_valid(self):
        # Ensure example file included in the repo is valid according to our validator
        path = os.path.join(os.path.dirname(__file__), "..", "berlin", "station_paths.example.geojson")
        path = os.path.abspath(path)
        self.assertTrue(generator.validate_station_paths(path))

    def test_load_markers_normalization(self):
        import tempfile
        csv_path = tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False)
        try:
            csv_path.write('name, lat, lon, transport\nA, 52.0, 13.0, True\nB, 52.1, 13.1, false\n')
            csv_path.flush()
            df = generator.load_markers(csv_path.name, 'test')
            self.assertIn('marker_type', df.columns)
            self.assertEqual([True, False], df['transport'].tolist())
        finally:
            csv_path.close()
            os.unlink(csv_path.name)

    def test_generate_map_runs(self):
        # Ensure generate_map completes and writes the expected output files
        import tempfile

        tmpdir = tempfile.mkdtemp()
        out_index = os.path.join(tmpdir, "index.html")
        out_editor = os.path.join(tmpdir, "editor.html")

        markers = [
            (os.path.join(os.path.dirname(__file__), "..", "berlin", "launch_with_transport.csv"), "launch_with_transport"),
            (os.path.join(os.path.dirname(__file__), "..", "berlin", "launch_without_transport.csv"), "launch_without_transport"),
            (os.path.join(os.path.dirname(__file__), "..", "berlin", "resting_points.csv"), "resting_point"),
        ]
        geojson = os.path.join(os.path.dirname(__file__), "..", "berlin", "routes.geojson")
        geojson = os.path.abspath(geojson)

        # Run generator (should not raise)
        generator.generate_map(markers, geojson, output_index=out_index, output_editor=out_editor)

        self.assertTrue(os.path.exists(out_index))
        self.assertTrue(os.path.exists(out_editor))


if __name__ == '__main__':
    unittest.main()
