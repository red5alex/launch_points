import os
import tempfile
import unittest

from launch_points import validator


class TestValidator(unittest.TestCase):
    def test_validate_marker_csv_basic(self):
        tmpdir = tempfile.TemporaryDirectory()
        try:
            base = tmpdir.name
            pics = os.path.join(base, "figs")
            os.makedirs(pics, exist_ok=True)
            picfile = os.path.join(pics, "img.jpg")
            with open(picfile, "w") as fh:
                fh.write("x")

            csv_path = os.path.join(base, "markers.csv")
            with open(csv_path, "w") as fh:
                fh.write("name, lat, lon, transport, picture\n")
                fh.write("A, 52.0, 13.0, True, figs/img.jpg\n")
                fh.write("B, x, 13.1, maybe, figs/missing.jpg\n")

            issues = validator.validate_marker_csv(csv_path)
            # Expect invalid coordinate in row 1 and unknown transport format and missing picture
            self.assertTrue(any("invalid-coordinates" in i for i in issues))
            self.assertTrue(any("transport-unknown-format" in i for i in issues))
            self.assertTrue(any("missing-picture" in i for i in issues))
        finally:
            tmpdir.cleanup()
