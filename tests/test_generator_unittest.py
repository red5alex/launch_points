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
