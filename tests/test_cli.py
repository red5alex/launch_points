import unittest
from typer.testing import CliRunner

from launch_points import cli


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_validate_json_no_exit_on_error(self):
        result = self.runner.invoke(cli.app, ["validate", "--format", "json", "--no-exit-on-error"])  # note: Typer converts option name
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.output.strip().startswith("{"))

    def test_generate_dryrun_no_validate(self):
        result = self.runner.invoke(cli.app, ["generate", "--dry-run", "--no-validate"])  # no files written
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Dry run", result.output)

    def test_generate_shows_validation_issues(self):
        # Run the validator first to see if any issues exist in this workspace.
        # The test is resilient: if validation finds issues, `generate` should
        # exit with code 2 and show helpful messages; if there are no issues,
        # `generate` should succeed (exit code 0).
        val = self.runner.invoke(cli.app, ["validate", "--format", "json", "--no-exit-on-error"])  # get JSON
        self.assertEqual(val.exit_code, 0)
        import json as _json
        parsed = _json.loads(val.output)
        has_issues = any(len(v) for v in parsed.values())

        result = self.runner.invoke(cli.app, ["generate"])
        if has_issues:
            # Should exit with validation error code (2) and show 'missing-picture' or similar in output
            self.assertEqual(result.exit_code, 2)
            self.assertIn("Suggested fixes", result.output)
        else:
            # No validation issues in this workspace — generation should complete
            self.assertEqual(result.exit_code, 0)

    def test_generate_success_shows_files(self):
        # Patch generator.generate_map so we don't overwrite repo files during the test
        from unittest.mock import patch

        with patch("launch_points.generator.generate_map") as gm:
            gm.return_value = None
            result = self.runner.invoke(cli.app, ["generate", "--no-validate"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Map generation complete", result.output)
            self.assertIn("berlin/index.html", result.output)
            self.assertIn("berlin/editor.html", result.output)
